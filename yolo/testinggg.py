from PIL import Image
import numpy as np
import face_recognition

img_path = "E:/MissionHardware/authorized/krutika/test.jpg"

print("Loading:", img_path)

try:
    image = Image.open(img_path).convert("RGB")
    image = np.array(image)

    encodings = face_recognition.face_encodings(image)

    print("Faces found:", len(encodings))

except Exception as e:
    print("ERROR:", e)