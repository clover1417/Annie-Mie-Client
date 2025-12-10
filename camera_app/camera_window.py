import cv2
import numpy as np
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, QCheckBox
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QFont, QBrush


class CameraWindow(QWidget):
    def __init__(self, bridge, identity_manager):
        super().__init__()
        self.bridge = bridge
        self.identity_manager = identity_manager
        self._frame_count = 0
        self._last_faces = []
        self._is_active = False
        self._fps_counter = 0
        self._current_fps = 0
        self.cap = None
        
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
        
        self.fps_label = QLabel("0 FPS")
        self.fps_label.setStyleSheet("color: #78909C; font-size: 12px;")
        
        self.face_count_label = QLabel("0 faces")
        self.face_count_label.setStyleSheet("color: #78909C; font-size: 12px;")
        
        header_layout.addWidget(cam_icon)
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.fps_label)
        header_layout.addSpacing(16)
        header_layout.addWidget(self.face_count_label)
        
        self.image_container = QFrame()
        self.image_container.setStyleSheet("background-color: #121212; border-radius: 0;")
        
        image_layout = QVBoxLayout(self.image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background-color: #121212;")
        self.image_label.setMinimumSize(640, 360)
        
        image_layout.addWidget(self.image_label)
        
        controls = QFrame()
        controls.setFixedHeight(56)
        controls.setStyleSheet("background-color: #2D2D2D; border-top: 1px solid #3D3D3D;")
        
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(16, 0, 16, 0)
        
        bbox_label = QLabel("Face Detection")
        bbox_label.setStyleSheet("color: #B0BEC5; font-size: 13px;")
        
        self.bbox_toggle = QCheckBox()
        self.bbox_toggle.setChecked(False)
        self.bbox_toggle.setStyleSheet("""
            QCheckBox::indicator { width: 40px; height: 20px; }
            QCheckBox::indicator:checked { background-color: #4CAF50; border-radius: 10px; }
            QCheckBox::indicator:unchecked { background-color: #555; border-radius: 10px; }
        """)
        
        controls_layout.addWidget(bbox_label)
        controls_layout.addStretch()
        controls_layout.addWidget(self.bbox_toggle)
        
        main_layout.addWidget(header)
        main_layout.addWidget(self.image_container, 1)
        main_layout.addWidget(controls)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        
        self.fps_timer = QTimer(self)
        self.fps_timer.timeout.connect(self._update_fps_display)

    def showEvent(self, event):
        super().showEvent(event)
        self._is_active = True
        self._frame_count = 0
        self._fps_counter = 0
        
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.image_label.setText("Camera not available")
            return
            
        self.timer.start(16)
        self.fps_timer.start(1000)

    def hideEvent(self, event):
        super().hideEvent(event)
        self._is_active = False
        self.timer.stop()
        self.fps_timer.stop()
        self._last_faces = []
        
        if self.cap:
            self.cap.release()
            self.cap = None

    def closeEvent(self, event):
        self.hideEvent(event)
        event.accept()

    def _update_fps_display(self):
        self._current_fps = self._fps_counter
        self._fps_counter = 0
        self.fps_label.setText(f"{self._current_fps} FPS")

    def update_frame(self):
        if not self._is_active or not self.cap:
            return

        ret, frame = self.cap.read()
        if not ret or frame is None:
            return

        self._frame_count += 1
        self._fps_counter += 1
        
        faces = []
        if self.bbox_toggle.isChecked() and self.identity_manager.is_face_detection_available():
            if self._frame_count % 2 == 0:
                try:
                    self._last_faces = self.identity_manager.face_detector.detect_faces(frame)
                except Exception:
                    self._last_faces = []
            faces = self._last_faces
            
        self.face_count_label.setText(f"{len(faces)} face{'s' if len(faces) != 1 else ''}")

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        
        pixmap = QPixmap.fromImage(qt_image)
        
        if faces and self.bbox_toggle.isChecked():
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            for face in faces:
                bbox = face["bbox"]
                x, y, x2, y2 = [int(v) for v in bbox]
                w_box = x2 - x
                h_box = y2 - y
                
                pen = QPen(QColor("#4CAF50"))
                pen.setWidth(2)
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(x, y, w_box, h_box, 4, 4)
                
                score = face.get("det_score", 0.0)
                label = f"{score:.0%}"
                
                label_bg = QColor("#4CAF50")
                font_metrics = painter.fontMetrics()
                text_width = font_metrics.horizontalAdvance(label) + 12
                text_height = font_metrics.height() + 4
                
                label_rect_y = max(0, y - text_height - 2)
                painter.setBrush(QBrush(label_bg))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(x, label_rect_y, text_width, text_height, 3, 3)
                
                painter.setPen(QPen(QColor("white")))
                painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
                painter.drawText(x + 6, label_rect_y + text_height - 5, label)

            painter.end()
        
        scaled = pixmap.scaled(
            self.image_label.size(), 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.image_label.setPixmap(scaled)

    def cleanup(self):
        self._is_active = False
        self.timer.stop()
        self.fps_timer.stop()
        self._last_faces = []
        if self.cap:
            self.cap.release()
            self.cap = None
