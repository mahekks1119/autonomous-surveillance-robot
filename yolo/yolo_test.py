import cv2
from deepface import DeepFace
from ultralytics import YOLO
import os
import numpy as np
import time

print("🚀 Advanced Surveillance System Started...")

# -----------------------------
# PATH
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUTHORIZED_PATH = os.path.join(BASE_DIR, "authorized")

# -----------------------------
# LOAD YOLO
# -----------------------------
model = YOLO("yolov8n.pt")
print("✅ YOLO loaded")

# -----------------------------
# FACE DETECTOR
# -----------------------------
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

# -----------------------------
# LOAD AUTHORIZED EMBEDDINGS
# -----------------------------
authorized_embeddings = {}

print("🔄 Encoding authorized faces...")

for person in os.listdir(AUTHORIZED_PATH):
    person_folder = os.path.join(AUTHORIZED_PATH, person)

    if not os.path.isdir(person_folder):
        continue

    authorized_embeddings[person] = []

    for img in os.listdir(person_folder):
        path = os.path.join(person_folder, img)

        try:
            embedding = DeepFace.represent(
                img_path=path,
                model_name="Facenet",
                enforce_detection=False
            )[0]["embedding"]

            authorized_embeddings[person].append(embedding)
            print(f"✅ Encoded {person}")

        except Exception as e:
            print("Error:", e)

print("🎯 Encoding complete!")

# -----------------------------
# CAMERA
# -----------------------------
cap = cv2.VideoCapture(0)

# -----------------------------
# TRACKING STORAGE
# -----------------------------
tracked_people = {}  # key = id, value = {label, time}
person_id_counter = 0

DISPLAY_TIME = 2  # seconds

# -----------------------------
# HELPER: MATCH PERSON BY POSITION
# -----------------------------
def get_person_id(x, y):
    for pid, data in tracked_people.items():
        px, py = data["pos"]
        if abs(px - x) < 50 and abs(py - y) < 50:
            return pid
    return None

# -----------------------------
# MAIN LOOP
# -----------------------------
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (480, 360))

    results = model(frame, stream=True)

    for r in results:
        for box, cls in zip(r.boxes.xyxy, r.boxes.cls):

            if int(cls) == 0:  # person

                x1, y1, x2, y2 = map(int, box)

                # safe crop
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)

                person_crop = frame[y1:y2, x1:x2]

                if person_crop.size == 0:
                    continue

                # get center for tracking
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2

                pid = get_person_id(cx, cy)

                if pid is None:
                    pid = person_id_counter
                    person_id_counter += 1
                    tracked_people[pid] = {
                        "label": "Detecting...",
                        "time": 0,
                        "pos": (cx, cy)
                    }

                tracked_people[pid]["pos"] = (cx, cy)

                label = tracked_people[pid]["label"]
                last_time = tracked_people[pid]["time"]

                # -----------------------------
                # FACE DETECTION
                # -----------------------------
                gray = cv2.cvtColor(person_crop, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)

                for (fx, fy, fw, fh) in faces:

                    face = person_crop[fy:fy+fh, fx:fx+fw]

                    if face.size == 0:
                        continue

                    current_time = time.time()

                    # 🔥 Only recompute after DISPLAY_TIME
                    if current_time - last_time > DISPLAY_TIME:

                        try:
                            temp_path = "temp.jpg"
                            cv2.imwrite(temp_path, face)

                            embedding = DeepFace.represent(
                                img_path=temp_path,
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

                            if min_dist < 1.7:
                                label = "Authorized"
                            else:
                                label = "Unknown"

                            # update tracking
                            tracked_people[pid]["label"] = label
                            tracked_people[pid]["time"] = current_time

                        except Exception as e:
                            print("Error:", e)
                            label = "Unknown"

                    # -----------------------------
                    # DRAW
                    # -----------------------------
                    if "Authorized" in label:
                        color = (0, 255, 0)
                    elif label == "Detecting...":
                        color = (255, 255, 0)
                    else:
                        color = (0, 0, 255)

                    # draw face box
                    cv2.rectangle(person_crop, (fx, fy), (fx+fw, fy+fh), color, 2)

                    # draw label on person box
                    cv2.putText(frame, label, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

                    # alert
                    if label == "Unknown":
                        print("⚠️ ALERT: Unauthorized person!")

    cv2.imshow("Advanced Surveillance System", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()

print("🛑 System stopped")

