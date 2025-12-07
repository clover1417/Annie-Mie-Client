use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use std::sync::{Arc, Mutex};
use crossbeam_channel::Sender;
use anyhow::Result;
use crate::config::AudioConfig;
use crate::vad::VoiceActivityDetector;

pub struct AudioRecorder {
    stream: Option<cpal::Stream>,
    vad: Arc<Mutex<VoiceActivityDetector>>,
    filepath_sender: Sender<String>,
}

impl AudioRecorder {
    pub fn new(config: AudioConfig, filepath_sender: Sender<String>) -> Result<Self> {
        let host = cpal::default_host();
        let device = host.default_input_device()
            .ok_or_else(|| anyhow::anyhow!("No input device found"))?;

        let default_config = device.default_input_config()?;
        let sample_rate = default_config.sample_rate().0;
        let stream_config: cpal::StreamConfig = default_config.into();

        println!("Native sample rate: {}Hz, resampling to 16kHz", sample_rate);

        let target_rate = config.target_sample_rate;
        let resample_ratio = sample_rate as f64 / target_rate as f64;
        let mut sample_buffer: Vec<f32> = Vec::new();

        // Initialize VAD
        let vad = Arc::new(Mutex::new(VoiceActivityDetector::new(config)));
        let vad_clone = Arc::clone(&vad);
        let sender_clone = filepath_sender.clone();

        let err_fn = |err| eprintln!("an error occurred on stream: {}", err);

        let stream = device.build_input_stream(
            &stream_config,
            move |data: &[f32], _: &_| {
                sample_buffer.extend_from_slice(data);

                let required_samples = (resample_ratio * 512.0).ceil() as usize;

                while sample_buffer.len() >= required_samples {
                    let mut resampled = Vec::with_capacity(512);

                    for i in 0..512 {
                        let src_idx = (i as f64 * resample_ratio) as usize;
                        if src_idx < sample_buffer.len() {
                            resampled.push(sample_buffer[src_idx]);
                        }
                    }

                    let consumed = (512.0 * resample_ratio) as usize;
                    sample_buffer.drain(0..consumed.min(sample_buffer.len()));

                    // Convert to i16 PCM
                    let pcm_chunk: Vec<i16> = resampled
                        .iter()
                        .map(|&sample| (sample.clamp(-1.0, 1.0) * 32767.0) as i16)
                        .collect();

                    // Process through VAD
                    if let Ok(mut vad) = vad_clone.lock() {
                        if let Some(filepath) = vad.process_chunk(pcm_chunk) {
                            // Speech segment completed, send filepath
                            if let Err(e) = sender_clone.send(filepath) {
                                eprintln!("Failed to send filepath: {}", e);
                            }
                        }
                    }
                }
            },
            err_fn,
            None,
        )?;

        Ok(Self {
            stream: Some(stream),
            vad,
            filepath_sender,
        })
    }

    pub fn start(&self) -> Result<()> {
        if let Some(ref stream) = self.stream {
            stream.play()?;
        }
        Ok(())
    }

    pub fn stop(&self) -> Result<()> {
        if let Some(ref stream) = self.stream {
            stream.pause()?;
        }
        Ok(())
    }
}
