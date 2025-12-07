use parking_lot::RwLock;
use std::collections::VecDeque;
use std::time::{Duration, Instant};

pub struct FrameBuffer {
    frames: RwLock<VecDeque<(Instant, Vec<u8>)>>,
    max_duration: Duration,
    max_frames: usize,
}

impl FrameBuffer {
    pub fn new(max_duration_secs: f32, fps: f32) -> Self {
        let max_frames = (max_duration_secs * fps).ceil() as usize + 1;
        Self {
            frames: RwLock::new(VecDeque::with_capacity(max_frames)),
            max_duration: Duration::from_secs_f32(max_duration_secs),
            max_frames,
        }
    }

    pub fn push(&self, jpeg_data: Vec<u8>) {
        let mut frames = self.frames.write();
        let now = Instant::now();

        frames.push_back((now, jpeg_data));

        while frames.len() > self.max_frames {
            frames.pop_front();
        }

        let cutoff = now.checked_sub(self.max_duration).unwrap_or(now);
        while frames.front().map(|(t, _)| *t < cutoff).unwrap_or(false) {
            frames.pop_front();
        }
    }

    pub fn get_frames_since(&self, duration_secs: f32) -> Vec<Vec<u8>> {
        let frames = self.frames.read();
        let cutoff = Instant::now().checked_sub(Duration::from_secs_f32(duration_secs)).unwrap_or(Instant::now());

        frames
            .iter()
            .filter(|(t, _)| *t >= cutoff)
            .map(|(_, data)| data.clone())
            .collect()
    }

    pub fn get_latest(&self) -> Option<Vec<u8>> {
        self.frames.read().back().map(|(_, data)| data.clone())
    }

    pub fn stats(&self) -> (usize, f32) {
        let frames = self.frames.read();
        let count = frames.len();
        let duration = if count > 1 {
            if let (Some((first, _)), Some((last, _))) = (frames.front(), frames.back()) {
                last.duration_since(*first).as_secs_f32()
            } else {
                0.0
            }
        } else {
            0.0
        };
        (count, duration)
    }

    pub fn clear(&self) {
        self.frames.write().clear();
    }
}
