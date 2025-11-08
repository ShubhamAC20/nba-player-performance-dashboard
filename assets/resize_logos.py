# assets/resize_logos.py
# Run this after logos are downloaded
# python assets/resize_logos.py

import os
from PIL import Image

LOGO_DIR = "assets/logos"
TARGET_SIZE = (64, 64)  # you can change to (100, 100) for larger logos

def resize_logo(path):
    try:
        with Image.open(path) as img:
            img = img.convert("RGBA")
            img = img.resize(TARGET_SIZE, Image.LANCZOS)
            img.save(path, optimize=True)
            print(f"✅ Resized: {os.path.basename(path)}")
    except Exception as e:
        print(f"⚠️ Skipped {path}: {e}")

def main():
    if not os.path.exists(LOGO_DIR):
        print("Logo folder not found:", LOGO_DIR)
        return

    files = [f for f in os.listdir(LOGO_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not files:
        print("No image files found in", LOGO_DIR)
        return

    print(f"Resizing {len(files)} logo(s) to {TARGET_SIZE}...")
    for file in files:
        resize_logo(os.path.join(LOGO_DIR, file))

    print("\n✅ All done! Logos resized and optimized.")

if __name__ == "__main__":
    main()