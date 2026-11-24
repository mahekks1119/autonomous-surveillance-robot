# encode_faces.py
import os
import pickle
from deepface import DeepFace

AUTHORIZED_PATH = "authorized"

authorized_embeddings = {}

print("🔄 Encoding faces (ONE TIME)...")

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

with open("encodings.pkl", "wb") as f:
    pickle.dump(authorized_embeddings, f)

print("💾 Saved as encodings.pkl")