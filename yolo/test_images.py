from PIL import Image
import os

base = "authorized"

for person in os.listdir(base):
    folder = os.path.join(base, person)

    for file in os.listdir(folder):
        path = os.path.join(folder, file)

        try:
            img = Image.open(path).convert("RGB")
            img.save(path)  # overwrite fixed image
            print("Fixed:", path)
        except:
            print("Failed:", path)