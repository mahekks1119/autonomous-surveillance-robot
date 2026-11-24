import cv2
import time
import numpy as np
import requests
from ultralytics import YOLO

# -----------------------------
# CONFIG
# -----------------------------
URL = "http://10.131.52.243/capture"  # your ESP32-CAM IP

model = YOLO("yolov8n.pt")

print("🚀 Running YOLO on ESP32-CAM (CAPTURE MODE)")

while True:
    try:
        response = requests.get(URL, timeout=5)

        if response.status_code != 200:
            print("❌ Bad response")
            time.sleep(1)
            continue

        img_array = np.frombuffer(response.content, np.uint8)
        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if frame is None:
            print("❌ Decode failed")
            time.sleep(0.5)
            continue

        cv2.imshow("ESP32", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

        time.sleep(0.2)

    except Exception as e:
        print("⚠️ Connection issue:", e)
        time.sleep(2)

cv2.destroyAllWindows()