import numpy as np

def detect_pinch(landmarks) -> bool:
    # Landmark 4 = Thumb Tip, Landmark 8 = Index Tip
    thumb = np.array([landmarks[4].x, landmarks[4].y])
    index = np.array([landmarks[8].x, landmarks[8].y])
    distance = np.linalg.norm(thumb - index)
    return distance < 0.05

def detect_open_palm(landmarks) -> bool:
    # Detect if fingertips 8, 12, 16, 20 are above their knuckle joints (y is smaller)
    return (landmarks[8].y < landmarks[6].y and
            landmarks[12].y < landmarks[10].y and
            landmarks[16].y < landmarks[14].y and
            landmarks[20].y < landmarks[18].y)