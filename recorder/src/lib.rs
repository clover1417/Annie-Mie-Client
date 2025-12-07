use crossbeam_channel::{unbounded, Receiver};
use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::collections::HashMap;

mod audio;
mod config;
mod frame_buffer;
mod vad;
mod video;

use audio::AudioRecorder;
use config::{ConfigValue, RecorderConfig};
use video::VideoRecorder;

#[pyclass(unsendable)]
struct NativeRecorder {
    audio: Option<AudioRecorder>,
    video: Option<VideoRecorder>,
    filepath_rx: Receiver<String>,
    config: RecorderConfig,
}

#[pymethods]
impl NativeRecorder {
    #[new]
    fn new(py_config: &PyDict) -> PyResult<Self> {
        let config_map = parse_python_dict(py_config)?;
        let config = RecorderConfig::from_python_dict(&config_map);

        let (filepath_tx, filepath_rx) = unbounded();

        let audio = AudioRecorder::new(config.audio.clone(), filepath_tx)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        let video = if config.video.enabled {
            Some(
                VideoRecorder::new(config.video.clone())
                    .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?,
            )
        } else {
            None
        };

        Ok(NativeRecorder {
            audio: Some(audio),
            video,
            filepath_rx,
            config,
        })
    }

    fn start(&mut self) -> PyResult<()> {
        if let Some(audio) = &self.audio {
            audio
                .start()
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        }
        if let Some(video) = &mut self.video {
            video
                .start()
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        }
        Ok(())
    }

    fn stop(&mut self) -> PyResult<()> {
        if let Some(audio) = &self.audio {
            audio
                .stop()
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        }
        if let Some(video) = &mut self.video {
            video.stop();
        }
        Ok(())
    }

    fn read_speech_event(&self) -> PyResult<Option<String>> {
        match self.filepath_rx.try_recv() {
            Ok(filepath) => Ok(Some(filepath)),
            Err(_) => Ok(None),
        }
    }

    fn get_frames_for_duration(&self, py: Python, duration_secs: f32) -> PyResult<Vec<PyObject>> {
        use pyo3::types::PyBytes;

        let frames = match &self.video {
            Some(v) => v.get_frames_for_duration(duration_secs),
            None => vec![],
        };

        Ok(frames
            .into_iter()
            .map(|data| PyBytes::new(py, &data).into())
            .collect())
    }

    fn get_latest_frame(&self, py: Python) -> PyResult<Option<PyObject>> {
        use pyo3::types::PyBytes;

        match &self.video {
            Some(v) => Ok(v.get_latest_frame().map(|data| PyBytes::new(py, &data).into())),
            None => Ok(None),
        }
    }

    fn get_buffer_stats(&self) -> PyResult<(usize, f32)> {
        match &self.video {
            Some(v) => Ok(v.stats()),
            None => Ok((0, 0.0)),
        }
    }

    fn get_audio_format(&self) -> PyResult<String> {
        Ok(match self.config.audio.format {
            config::AudioFormat::Flac => "flac".to_string(),
            config::AudioFormat::Wav => "wav".to_string(),
        })
    }
}

fn parse_python_dict(py_dict: &PyDict) -> PyResult<HashMap<String, ConfigValue>> {
    let mut config_map: HashMap<String, ConfigValue> = HashMap::new();

    for (key, value) in py_dict.iter() {
        let key_str: String = key.extract()?;

        if let Ok(s) = value.extract::<String>() {
            config_map.insert(key_str, ConfigValue::String(s));
        } else if let Ok(b) = value.extract::<bool>() {
            config_map.insert(key_str, ConfigValue::Bool(b));
        } else if let Ok(f) = value.extract::<f64>() {
            config_map.insert(key_str, ConfigValue::Float(f));
        }
    }

    Ok(config_map)
}

#[pymodule]
fn recorder(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<NativeRecorder>()?;
    Ok(())
}
