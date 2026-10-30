import unittest
from vision.smoothing import ExponentialSmoother
from vision.gestures import detect_pinch, detect_open_palm
from vision.camera import CameraManager

class MockLandmark:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z

class TestVision(unittest.IsolatedAsyncioTestCase):
    def test_exponential_smoother(self):
        smoother = ExponentialSmoother(alpha=0.5)
        # First point sets baseline
        x, y, z = smoother.smooth(1.0, 2.0, 3.0)
        self.assertEqual((x, y, z), (1.0, 2.0, 3.0))

        # Second point smoothed with alpha 0.5: 0.5*2.0 + 0.5*1.0 = 1.5
        sx, sy, sz = smoother.smooth(2.0, 4.0, 5.0)
        self.assertAlmostEqual(sx, 1.5)
        self.assertAlmostEqual(sy, 3.0)
        self.assertAlmostEqual(sz, 4.0)

    def test_detect_pinch_true_and_false(self):
        landmarks = [MockLandmark() for _ in range(21)]
        # Thumb tip (4) and Index tip (8) close together
        landmarks[4] = MockLandmark(x=0.5, y=0.5)
        landmarks[8] = MockLandmark(x=0.51, y=0.51)
        self.assertTrue(detect_pinch(landmarks))

        # Thumb tip and Index tip far apart
        landmarks[8] = MockLandmark(x=0.8, y=0.8)
        self.assertFalse(detect_pinch(landmarks))

    def test_detect_open_palm_true_and_false(self):
        landmarks = [MockLandmark() for _ in range(21)]
        # Fingertips (8, 12, 16, 20) are above knuckles (6, 10, 14, 18) -> smaller y in image coords
        landmarks[8] = MockLandmark(y=0.2)
        landmarks[6] = MockLandmark(y=0.4)
        landmarks[12] = MockLandmark(y=0.2)
        landmarks[10] = MockLandmark(y=0.4)
        landmarks[16] = MockLandmark(y=0.2)
        landmarks[14] = MockLandmark(y=0.4)
        landmarks[20] = MockLandmark(y=0.2)
        landmarks[18] = MockLandmark(y=0.4)
        self.assertTrue(detect_open_palm(landmarks))

        # Closed fist (fingertips below knuckles)
        landmarks[8] = MockLandmark(y=0.6)
        landmarks[6] = MockLandmark(y=0.4)
        self.assertFalse(detect_open_palm(landmarks))

    async def test_camera_manager_mock_frame(self):
        cam = CameraManager(camera_index=999) # Non-existent camera index
        success, frame = await cam.read_frame()
        self.assertTrue(success)
        self.assertIsNotNone(frame)
        self.assertEqual(len(frame.shape), 3)

if __name__ == "__main__":
    unittest.main()

