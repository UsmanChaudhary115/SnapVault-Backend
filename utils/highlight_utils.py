import cv2
import numpy as np  

# ---------- Quality Score Functions ----------

def detect_blur(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()

def check_brightness(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    return hsv[..., 2].mean()

def face_area_ratio(bbox, image_shape):
    img_area = image_shape[0] * image_shape[1]
    face_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
    return face_area / img_area

def is_facing_camera(pose, threshold=15):
    return abs(pose[0]) < threshold and abs(pose[1]) < threshold and abs(pose[2]) < threshold

def evaluate_image_quality(faces, image): 
    if not faces:
        return 0

    scores = []
    for face in faces:
        pose_ok = is_facing_camera(face.pose)
        face_ratio = face_area_ratio(face.bbox, image.shape)

        score = 0
        if 0.15 < face_ratio < 0.6:
            score += 1
        if pose_ok:
            score += 1 
        scores.append(score)

    blur_score = detect_blur(image)
    brightness = check_brightness(image)

    img_score = 0
    if 70 < brightness < 180:
        img_score += 1
    if blur_score > 100:
        img_score += 1

    face_score = np.mean(scores)
    final_score = face_score + img_score

    return final_score
