use std::collections::HashMap;

#[derive(Clone, Debug, PartialEq)]
pub enum AudioFormat {
    Wav,
    Flac,
}

impl Default for AudioFormat {
    fn default() -> Self {
        AudioFormat::Flac
    }
}

#[derive(Clone, Debug)]
pub struct AudioConfig {
    pub target_sample_rate: u32,
    pub chunk_size: usize,
    pub format: AudioFormat,
    pub flac_compression: u8,
    pub spike_factor: f32,
    pub stop_factor: f32,
    pub release_ratio: f32,
    pub silence_limit_secs: f32,
    pub silence_abs_threshold: f32,
    pub min_record_seconds: f32,
    pub background_alpha: f32,
    pub output_directory: String,
}

impl Default for AudioConfig {
    fn default() -> Self {
        AudioConfig {
            target_sample_rate: 16000,
            chunk_size: 512,
            format: AudioFormat::Flac,
            flac_compression: 5,
            spike_factor: 2.5,
            stop_factor: 2.5,
            release_ratio: 0.25,
            silence_limit_secs: 2.0,
            silence_abs_threshold: 0.008,
            min_record_seconds: 0.3,
            background_alpha: 0.95,
            output_directory: "data/recordings".to_string(),
        }
    }
}

#[derive(Clone, Debug)]
pub struct VideoConfig {
    pub enabled: bool,
    pub camera_index: u32,
    pub fps: f32,
    pub width: u32,
    pub height: u32,
    pub jpeg_quality: u8,
    pub buffer_duration_secs: f32,
}

impl Default for VideoConfig {
    fn default() -> Self {
        VideoConfig {
            enabled: false,
            camera_index: 0,
            fps: 0.5,
            width: 640,
            height: 480,
            jpeg_quality: 75,
            buffer_duration_secs: 30.0,
        }
    }
}

#[derive(Clone, Debug)]
pub struct RecorderConfig {
    pub audio: AudioConfig,
    pub video: VideoConfig,
}

impl Default for RecorderConfig {
    fn default() -> Self {
        RecorderConfig {
            audio: AudioConfig::default(),
            video: VideoConfig::default(),
        }
    }
}

impl RecorderConfig {
    pub fn from_python_dict(dict: &HashMap<String, ConfigValue>) -> Self {
        let mut config = RecorderConfig::default();

        if let Some(ConfigValue::Float(val)) = dict.get("target_sample_rate") {
            config.audio.target_sample_rate = *val as u32;
        }
        if let Some(ConfigValue::Float(val)) = dict.get("chunk_size") {
            config.audio.chunk_size = *val as usize;
        }
        if let Some(ConfigValue::String(val)) = dict.get("audio_format") {
            config.audio.format = match val.as_str() {
                "wav" => AudioFormat::Wav,
                _ => AudioFormat::Flac,
            };
        }
        if let Some(ConfigValue::Float(val)) = dict.get("flac_compression") {
            config.audio.flac_compression = (*val as u8).min(8);
        }
        if let Some(ConfigValue::Float(val)) = dict.get("spike_factor") {
            config.audio.spike_factor = *val as f32;
        }
        if let Some(ConfigValue::Float(val)) = dict.get("stop_factor") {
            config.audio.stop_factor = *val as f32;
        }
        if let Some(ConfigValue::Float(val)) = dict.get("release_ratio") {
            config.audio.release_ratio = *val as f32;
        }
        if let Some(ConfigValue::Float(val)) = dict.get("silence_limit_secs") {
            config.audio.silence_limit_secs = *val as f32;
        }
        if let Some(ConfigValue::Float(val)) = dict.get("silence_abs_threshold") {
            config.audio.silence_abs_threshold = *val as f32;
        }
        if let Some(ConfigValue::Float(val)) = dict.get("min_record_seconds") {
            config.audio.min_record_seconds = *val as f32;
        }
        if let Some(ConfigValue::Float(val)) = dict.get("background_alpha") {
            config.audio.background_alpha = *val as f32;
        }
        if let Some(ConfigValue::String(val)) = dict.get("output_directory") {
            config.audio.output_directory = val.clone();
        }

        if let Some(ConfigValue::Bool(val)) = dict.get("video_enabled") {
            config.video.enabled = *val;
        }
        if let Some(ConfigValue::Float(val)) = dict.get("camera_index") {
            config.video.camera_index = *val as u32;
        }
        if let Some(ConfigValue::Float(val)) = dict.get("video_fps") {
            config.video.fps = *val as f32;
        }
        if let Some(ConfigValue::Float(val)) = dict.get("video_width") {
            config.video.width = *val as u32;
        }
        if let Some(ConfigValue::Float(val)) = dict.get("video_height") {
            config.video.height = *val as u32;
        }
        if let Some(ConfigValue::Float(val)) = dict.get("jpeg_quality") {
            config.video.jpeg_quality = (*val as u8).min(100);
        }
        if let Some(ConfigValue::Float(val)) = dict.get("buffer_duration_secs") {
            config.video.buffer_duration_secs = *val as f32;
        }

        config
    }
}

#[derive(Clone, Debug)]
pub enum ConfigValue {
    Float(f64),
    String(String),
    Bool(bool),
}
