use crate::config::VideoConfig;
use crate::frame_buffer::FrameBuffer;
use anyhow::Result;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::thread;
use std::time::Duration;

pub struct VideoRecorder {
    running: Arc<AtomicBool>,
    frame_buffer: Arc<FrameBuffer>,
    capture_thread: Option<thread::JoinHandle<()>>,
    config: VideoConfig,
}

impl VideoRecorder {
    pub fn new(config: VideoConfig) -> Result<Self> {
        let frame_buffer = Arc::new(FrameBuffer::new(
            config.buffer_duration_secs,
            config.fps,
        ));

        Ok(Self {
            running: Arc::new(AtomicBool::new(false)),
            frame_buffer,
            capture_thread: None,
            config,
        })
    }

    pub fn start(&mut self) -> Result<()> {
        if self.running.load(Ordering::SeqCst) {
            return Ok(());
        }

        self.running.store(true, Ordering::SeqCst);

        let running = Arc::clone(&self.running);
        let frame_buffer = Arc::clone(&self.frame_buffer);
        let config = self.config.clone();

        let handle = thread::spawn(move || {
            if let Err(e) = capture_loop(running, frame_buffer, config) {
                eprintln!("Video capture error: {}", e);
            }
        });

        self.capture_thread = Some(handle);
        println!("Video capture started at {} FPS", self.config.fps);
        Ok(())
    }

    pub fn stop(&mut self) {
        self.running.store(false, Ordering::SeqCst);

        if let Some(handle) = self.capture_thread.take() {
            let _ = handle.join();
        }
        println!("Video capture stopped");
    }

    pub fn get_frames_for_duration(&self, duration_secs: f32) -> Vec<Vec<u8>> {
        self.frame_buffer.get_frames_since(duration_secs)
    }

    pub fn get_latest_frame(&self) -> Option<Vec<u8>> {
        self.frame_buffer.get_latest()
    }

    pub fn stats(&self) -> (usize, f32) {
        self.frame_buffer.stats()
    }
}

impl Drop for VideoRecorder {
    fn drop(&mut self) {
        self.stop();
    }
}

fn capture_loop(
    running: Arc<AtomicBool>,
    frame_buffer: Arc<FrameBuffer>,
    config: VideoConfig,
) -> Result<()> {
    use nokhwa::pixel_format::RgbFormat;
    use nokhwa::utils::{CameraFormat, CameraIndex, FrameFormat, RequestedFormat, RequestedFormatType, Resolution};
    use nokhwa::Camera;
    use std::time::Instant;

    let index = CameraIndex::Index(config.camera_index);
    let resolution = Resolution::new(config.width, config.height);
    let camera_fps = 15u32;
    let camera_format = CameraFormat::new(resolution, FrameFormat::MJPEG, camera_fps);
    let requested = RequestedFormat::new::<RgbFormat>(RequestedFormatType::Closest(camera_format));

    let mut camera = Camera::new(index, requested)?;
    camera.open_stream()?;

    let target_interval = Duration::from_secs_f32(1.0 / config.fps);
    let mut last_capture = Instant::now() - target_interval;

    while running.load(Ordering::SeqCst) {
        match camera.frame() {
            Ok(frame) => {
                let now = Instant::now();
                if now.duration_since(last_capture) >= target_interval {
                    let rgb_data = frame.decode_image::<RgbFormat>().ok();

                    if let Some(rgb) = rgb_data {
                        if let Ok(jpeg_data) = encode_jpeg(&rgb, config.width, config.height, config.jpeg_quality) {
                            frame_buffer.push(jpeg_data);
                            last_capture = now;
                        }
                    }
                }
            }
            Err(e) => {
                eprintln!("Frame capture error: {}", e);
                thread::sleep(Duration::from_millis(100));
            }
        }
    }

    camera.stop_stream()?;
    Ok(())
}

fn encode_jpeg(rgb_data: &[u8], width: u32, height: u32, quality: u8) -> Result<Vec<u8>> {
    use jpeg_encoder::{ColorType, Encoder};

    let mut output = Vec::new();
    let encoder = Encoder::new(&mut output, quality);
    encoder
        .encode(rgb_data, width as u16, height as u16, ColorType::Rgb)
        .map_err(|e| anyhow::anyhow!("JPEG encoding failed: {:?}", e))?;

    Ok(output)
}
