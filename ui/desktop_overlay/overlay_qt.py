import sys
import json
from PyQt6.QtWidgets import QApplication, QWidget, QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
import websockets
import asyncio

class JarvisOverlay(QWidget):
    def __init__(self):
        super().__init__()
        # Make window transparent, frameless, and always on top
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(0, 0, 1920, 1080) # Adjust to your screen size
        
        # Cursor element
        self.cursor = QLabel(self)
        self.cursor.resize(20, 20)
        self.cursor.setStyleSheet("background-color: rgba(0, 229, 255, 150); border-radius: 10px;")
        
        # Status Label
        self.status_label = QLabel("SYSTEM: ONLINE", self)
        self.status_label.setStyleSheet("color: #00e5ff; font-family: 'Courier New'; font-size: 18px;")
        self.status_label.move(50, 50)
        
    def update_hand(self, x, y, is_pinching):
        screen_x = int(x * self.width())
        screen_y = int(y * self.height())
        self.cursor.move(screen_x, screen_y)
        
        if is_pinching:
            self.cursor.resize(30, 30)
            self.cursor.setStyleSheet("background-color: rgba(255, 0, 0, 200); border-radius: 15px;")
        else:
            self.cursor.resize(20, 20)
            self.cursor.setStyleSheet("background-color: rgba(0, 229, 255, 150); border-radius: 10px;")

# Run this module separately from the main FastAPI loop
# e.g., python -m ui.desktop_overlay.overlay_qt