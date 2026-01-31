import cv2
import numpy as np
from PIL import Image

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

def crop_by_face(image: Image.Image, face_ratio: float):
    img = np.array(image.convert("RGB"))
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    faces = face_cascade.detectMultiScale(gray, 1.2, 5)

    if len(faces) == 0:
        return image  # fallback

    x, y, w, h = faces[0]

    desired_face_height = int(image.height * face_ratio)
    scale = desired_face_height / h

    new_w = int(image.width * scale)
    new_h = int(image.height * scale)

    image = image.resize((new_w, new_h), Image.LANCZOS)

    return image
