use crate::config::{AudioConfig, AudioFormat};
use anyhow::Result;
use flacenc::error::Verify;
use std::collections::VecDeque;
use std::fs::{self, File};
use std::io::BufWriter;
use std::path::PathBuf;

pub struct VoiceActivityDetector {
    config: AudioConfig,
    is_active: bool,
    background_level: f32,
    peak_volume: f32,
    silent_duration: f32,
    recording_buffer: Vec<i16>,
    pre_buffer: VecDeque<Vec<i16>>,
    chunk_duration_secs: f32,
}

impl VoiceActivityDetector {
    pub fn new(config: AudioConfig) -> Self {
        let chunk_duration_secs = config.chunk_size as f32 / config.target_sample_rate as f32;

        VoiceActivityDetector {
            config,
            is_active: false,
            background_level: 0.01,
            peak_volume: 0.0,
            silent_duration: 0.0,
            recording_buffer: Vec::new(),
            pre_buffer: VecDeque::with_capacity(10),
            chunk_duration_secs,
        }
    }

    fn calculate_rms(&self, samples: &[i16]) -> f32 {
        if samples.is_empty() {
            return 0.0;
        }

        let sum_squares: f64 = samples
            .iter()
            .map(|&s| {
                let normalized = s as f64 / 32767.0;
                normalized * normalized
            })
            .sum();

        (sum_squares / samples.len() as f64).sqrt() as f32
    }

    pub fn process_chunk(&mut self, chunk: Vec<i16>) -> Option<String> {
        let volume = self.calculate_rms(&chunk);

        if !self.is_active {
            self.background_level = self.config.background_alpha * self.background_level
                + (1.0 - self.config.background_alpha) * volume;

            self.pre_buffer.push_back(chunk.clone());
            if self.pre_buffer.len() > 10 {
                self.pre_buffer.pop_front();
            }

            if volume > self.background_level * self.config.spike_factor {
                self.start_recording(volume);
                for buffered_chunk in &self.pre_buffer {
                    self.recording_buffer.extend_from_slice(buffered_chunk);
                }
                self.recording_buffer.extend_from_slice(&chunk);
            }

            None
        } else {
            self.recording_buffer.extend_from_slice(&chunk);

            if volume > self.peak_volume {
                self.peak_volume = volume;
            }

            let stop_thresh = self
                .config
                .silence_abs_threshold
                .max(self.background_level * self.config.stop_factor);
            let release_thresh = stop_thresh.max(self.peak_volume * self.config.release_ratio);

            if volume < release_thresh {
                self.silent_duration += self.chunk_duration_secs;
            } else {
                self.silent_duration = 0.0;
            }

            let total_samples = self.recording_buffer.len();
            let recording_duration = total_samples as f32 / self.config.target_sample_rate as f32;

            if self.silent_duration >= self.config.silence_limit_secs
                && recording_duration >= self.config.min_record_seconds
            {
                self.finalize_recording()
            } else {
                None
            }
        }
    }

    fn start_recording(&mut self, initial_volume: f32) {
        self.is_active = true;
        self.recording_buffer.clear();
        self.silent_duration = 0.0;
        self.peak_volume = initial_volume;
        if !Self::is_llm_busy() {
            println!("\u{2139}\u{FE0F} Recording started (vol={:.4})", initial_volume);
        }
    }

    fn is_llm_busy() -> bool {
        std::path::Path::new(".llm_busy").exists()
    }

    fn finalize_recording(&mut self) -> Option<String> {
        let duration = self.recording_buffer.len() as f32 / self.config.target_sample_rate as f32;
        if !Self::is_llm_busy() {
            println!("\u{2139}\u{FE0F} Recording stopped (duration: {:.1}s)", duration);
        }

        let filepath = match self.save_audio_file() {
            Ok(path) => path,
            Err(e) => {
                eprintln!("Error saving audio file: {}", e);
                self.reset_state();
                return None;
            }
        };

        self.reset_state();
        Some(filepath)
    }

    fn save_audio_file(&self) -> Result<String> {
        fs::create_dir_all(&self.config.output_directory)?;

        let timestamp = chrono::Local::now().format("%y%m%d_%H%M%S").to_string();
        let ext = match self.config.format {
            AudioFormat::Flac => "flac",
            AudioFormat::Wav => "wav",
        };
        let filename = format!("{}.{}", timestamp, ext);
        let filepath = PathBuf::from(&self.config.output_directory).join(&filename);

        match self.config.format {
            AudioFormat::Flac => self.save_flac(&filepath)?,
            AudioFormat::Wav => self.save_wav(&filepath)?,
        }

        Ok(filepath.to_string_lossy().to_string())
    }

    fn save_flac(&self, filepath: &PathBuf) -> Result<()> {
        use flacenc::bitsink::ByteSink;
        use flacenc::component::BitRepr;
        use flacenc::config::Encoder as FlacConfig;
        use flacenc::source::MemSource;

        let samples: Vec<i32> = self.recording_buffer.iter().map(|&s| s as i32).collect();
        let source = MemSource::from_samples(&samples, 1, 16, self.config.target_sample_rate as usize);

        let flac_config = FlacConfig::default()
            .into_verified()
            .map_err(|e| anyhow::anyhow!("Invalid FLAC config: {:?}", e))?;

        let stream = flacenc::encode_with_fixed_block_size(&flac_config, source, 4096)
            .map_err(|e| anyhow::anyhow!("FLAC encoding failed: {:?}", e))?;

        let mut sink = ByteSink::new();
        stream
            .write(&mut sink)
            .map_err(|e| anyhow::anyhow!("FLAC write failed: {:?}", e))?;

        fs::write(filepath, sink.as_slice())?;
        Ok(())
    }

    fn save_wav(&self, filepath: &PathBuf) -> Result<()> {
        let file = File::create(filepath)?;
        let mut writer = BufWriter::new(file);

        let num_samples = self.recording_buffer.len() as u32;
        let byte_rate = self.config.target_sample_rate * 2;
        let data_size = num_samples * 2;
        let file_size = 36 + data_size;

        use std::io::Write;
        writer.write_all(b"RIFF")?;
        writer.write_all(&file_size.to_le_bytes())?;
        writer.write_all(b"WAVE")?;
        writer.write_all(b"fmt ")?;
        writer.write_all(&16u32.to_le_bytes())?;
        writer.write_all(&1u16.to_le_bytes())?;
        writer.write_all(&1u16.to_le_bytes())?;
        writer.write_all(&self.config.target_sample_rate.to_le_bytes())?;
        writer.write_all(&byte_rate.to_le_bytes())?;
        writer.write_all(&2u16.to_le_bytes())?;
        writer.write_all(&16u16.to_le_bytes())?;
        writer.write_all(b"data")?;
        writer.write_all(&data_size.to_le_bytes())?;

        for &sample in &self.recording_buffer {
            writer.write_all(&sample.to_le_bytes())?;
        }

        Ok(())
    }

    fn reset_state(&mut self) {
        self.is_active = false;
        self.recording_buffer.clear();
        self.silent_duration = 0.0;
        self.peak_volume = 0.0;
    }
}
