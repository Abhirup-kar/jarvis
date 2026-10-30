import asyncio
from typing import Optional
from config.settings import settings
from vision.smoothing import ExponentialSmoother
from vision.gestures import detect_pinch, detect_open_palm
from core.event_bus import bus

class HandTracker:
    def __init__(self):
        self.smoother = ExponentialSmoother()
        self.is_running = False
        self.hands = None
        self._init_mediapipe()

    def _init_mediapipe(self):
        try:
            import mediapipe as mp
            self.mp_hands = mp.solutions.hands
            self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
        except Exception:
            self.hands = None

    async def start_stream(self):
        try:
            import cv2
        except ImportError:
            # Mediapipe/OpenCV not installed in current environment
            return

        cap = cv2.VideoCapture(settings.CAMERA_INDEX)
        self.is_running = True
        
        try:
            while self.is_running:
                if not cap.isOpened():
                    await asyncio.sleep(1.0)
                    continue

                success, frame = await asyncio.to_thread(cap.read)
                if not success or frame is None:
                    await asyncio.sleep(0.05)
                    continue
                    
                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                if self.hands is None:
                    self._init_mediapipe()

                if self.hands is not None:
                    results = await asyncio.to_thread(self.hands.process, rgb)
                    
                    if results.multi_hand_landmarks:
                        for hand_landmarks in results.multi_hand_landmarks:
                            idx_tip = hand_landmarks.landmark[8]
                            sx, sy, sz = self.smoother.smooth(idx_tip.x, idx_tip.y, idx_tip.z)
                            
                            is_pinching = detect_pinch(hand_landmarks.landmark)
                            is_palm = detect_open_palm(hand_landmarks.landmark)
                            
                            payload = {
                                "x": float(sx),
                                "y": float(sy),
                                "z": float(sz),
                                "pinch": is_pinching,
                                "open_palm": is_palm
                            }
                            await bus.publish("hand_coordinates", payload)
                
                await asyncio.sleep(0.01)
        finally:
            cap.release()

    def stop(self):
        self.is_running = False

hand_tracker = HandTracker()