import sys
import os
import socket
import struct
import cv2
import numpy as np
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap


class FrameReceiver(QThread):
    frame_received = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.sock = None
        
    def run(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect(('localhost', 8769))
            self.sock.settimeout(0.1)
            
            while self.running:
                try:
                    size_data = self.sock.recv(4)
                    if len(size_data) < 4:
                        continue
                    size = struct.unpack('>I', size_data)[0]
                    
                    data = b''
                    while len(data) < size:
                        chunk = self.sock.recv(min(size - len(data), 65536))
                        if not chunk:
                            break
                        data += chunk
                    
                    if len(data) == size:
                        nparr = np.frombuffer(data, np.uint8)
                        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                        if frame is not None:
                            self.frame_received.emit(frame)
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Frame receive error: {e}")
                    break
        except Exception as e:
            print(f"Could not connect to frame server: {e}")
        finally:
            if self.sock:
                self.sock.close()
                
    def stop(self):
        self.running = False


class CameraWindow(QWidget):
    def __init__(self):
        super().__init__()
        self._frame_count = 0
        self._fps_counter = 0
        self._current_fps = 0
        self._face_count = 0
        self.frame_receiver = None
        
        self.setWindowTitle("Annie Mie - Camera Feed")
        self.resize(700, 520)
        self.setWindowFlags(Qt.WindowType.Window)
        self.setStyleSheet("background-color: #1E1E1E;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        header = QFrame()
        header.setFixedHeight(48)
        header.setStyleSheet("background-color: #2D2D2D; border-bottom: 1px solid #3D3D3D;")
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 0, 16, 0)
        
        cam_icon = QLabel("📷")
        cam_icon.setStyleSheet("font-size: 18px;")
        title = QLabel("Live Camera Feed")
        title.setStyleSheet("color: #E0E0E0; font-size: 14px; font-weight: 500;")
        
        self.face_count_label = QLabel("0 faces")
        self.face_count_label.setStyleSheet("color: #78909C; font-size: 12px;")
        
        self.fps_label = QLabel("0 FPS")
        self.fps_label.setStyleSheet("color: #78909C; font-size: 12px;")
        
        self.status_label = QLabel("Connecting...")
        self.status_label.setStyleSheet("color: #FFC107; font-size: 12px;")
        
        header_layout.addWidget(cam_icon)
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.face_count_label)
        header_layout.addSpacing(16)
        header_layout.addWidget(self.fps_label)
        header_layout.addSpacing(16)
        header_layout.addWidget(self.status_label)
        
        self.image_container = QFrame()
        self.image_container.setStyleSheet("background-color: #121212;")
        
        image_layout = QVBoxLayout(self.image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background-color: #121212; color: #666; font-size: 14px;")
        self.image_label.setMinimumSize(640, 360)
        self.image_label.setText("Waiting for frames from Rust recorder...")
        
        image_layout.addWidget(self.image_label)
        
        main_layout.addWidget(header)
        main_layout.addWidget(self.image_container, 1)
        
        self.fps_timer = QTimer(self)
        self.fps_timer.timeout.connect(self._update_fps_display)

    def showEvent(self, event):
        super().showEvent(event)
        
        self.frame_receiver = FrameReceiver()
        self.frame_receiver.frame_received.connect(self.update_frame)
        self.frame_receiver.start()
        
        self.fps_timer.start(1000)

    def closeEvent(self, event):
        self.fps_timer.stop()
        if self.frame_receiver:
            self.frame_receiver.stop()
            self.frame_receiver.wait()
        event.accept()

    def _update_fps_display(self):
        self._current_fps = self._fps_counter
        self._fps_counter = 0
        self.fps_label.setText(f"{self._current_fps} FPS")

    def update_frame(self, frame):
        if frame is None:
            return
            
        self._frame_count += 1
        self._fps_counter += 1
        self.status_label.setText("Active")
        self.status_label.setStyleSheet("color: #4CAF50; font-size: 12px;")

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        
        pixmap = QPixmap.fromImage(qt_image)
        scaled = pixmap.scaled(
            self.image_label.size(), 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.image_label.setPixmap(scaled)


def main():
    app = QApplication(sys.argv)
    window = CameraWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
