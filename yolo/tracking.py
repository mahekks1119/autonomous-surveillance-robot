import cv2
from ultralytics import YOLO
from deepface import DeepFace
import numpy as np
import requests
import pickle
import socket
import time

print("🚀 AI SYSTEM READY (WAITING FOR PIR)...")

# -----------------------------
# CONFIG
# -----------------------------
ESP32_IP = "192.168.1.10"
STREAM_URL = "http://192.168.1.20:81/stream"
ENCODING_FILE = "encodings.pkl"

DIST_THRESHOLD = 2.5
ALERT_COOLDOWN = 5

last_alert_time = 0
ai_active = False

# -----------------------------
# LOAD MODELS
# -----------------------------
model = YOLO("yolov8n.pt")
DeepFace.build_model("Facenet")

with open(ENCODING_FILE, "rb") as f:
    authorized_embeddings = pickle.load(f)

print("✅ System Ready")

# -----------------------------
# LISTEN FOR PIR SIGNAL
# -----------------------------
server_socket = socket.socket()
server_socket.bind(("0.0.0.0", 5000))
server_socket.listen(1)

print("📡 Waiting for ESP32 trigger...")

conn, addr = server_socket.accept()
data = conn.recv(1024).decode()

if "START_AI" in data:
    print("🟢 AI ACTIVATED")
    ai_active = True

conn.close()

# -----------------------------
# CAMERA
# -----------------------------
cap = cv2.VideoCapture(STREAM_URL)

# -----------------------------
# SEND COMMAND
# -----------------------------
def send(cmd):
    try:
        requests.get(f"http://{ESP32_IP}/{cmd}", timeout=0.2)
    except:
        pass

# -----------------------------
# MAIN LOOP
# -----------------------------
while ai_active:

    ret, frame = cap.read()
    if not ret:
        continue

    frame = cv2.resize(frame, (480, 360))

    results = model(frame)

    person_found = False

    for r in results:
        for box, cls in zip(r.boxes.xyxy, r.boxes.cls):

            if int(cls) != 0:
                continue

            person_found = True

            x1, y1, x2, y2 = map(int, box)

            # -----------------------------
            # FOLLOW PERSON
            # -----------------------------
            cx = (x1 + x2) // 2
            center = frame.shape[1] // 2

            if cx < center - 50:
                send("left")
            elif cx > center + 50:
                send("right")
            else:
                send("forward")

            # -----------------------------
            # CLOSE → FACE CHECK
            # -----------------------------
            if (x2 - x1) > 150:

                face = frame[y1:y2, x1:x2]

                try:
                    embedding = DeepFace.represent(
                        img_path=face,
                        model_name="Facenet",
                        enforce_detection=False
                    )[0]["embedding"]

                    min_dist = 999
                    best_match = "Unknown"

                    for person, embeds in authorized_embeddings.items():
                        for ref_emb in embeds:
                            dist = np.linalg.norm(
                                np.array(ref_emb) - np.array(embedding)
                            )
                            if dist < min_dist:
                                min_dist = dist
                                best_match = person

                    # -----------------------------
                    # AUTHORIZED
                    # -----------------------------
                    if min_dist < DIST_THRESHOLD:
                        print(f"✅ {best_match} Authorized")

                        send("stop")
                        send("resume")   # 🔥 back to path
                        ai_active = False
                        break

                    # -----------------------------
                    # UNAUTHORIZED
                    # -----------------------------
                    else:
                        print("🚨 Intruder")

                        if time.time() - last_alert_time > ALERT_COOLDOWN:
                            send("intruder")
                            last_alert_time = time.time()

                except:
                    pass

    if not person_found:
        send("stop")

    cv2.imshow("AI Mode", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()

print("🛑 AI Mode Ended")