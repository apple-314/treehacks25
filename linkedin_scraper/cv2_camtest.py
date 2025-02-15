import cv2
import asyncio
import face_recognition
from pathlib import Path
import re
import numpy as np
import linkedin
import time

async def detect_async(frame):
    start_time = time.time()
    imgpath = "/Users/jameschen/Documents/treehacks25/imgs"
    folder_path = Path(imgpath)

    known_face_encodings = []
    known_face_names = []

    for file in folder_path.iterdir():
        if file.is_file() and file.suffix == ".png":  
            name = file.stem
            cur_img = face_recognition.load_image_file(file)
            encodings = await asyncio.to_thread(face_recognition.face_encodings, cur_img)  # Run in background thread
            if encodings:
                known_face_encodings.append(encodings[0])
                known_face_names.append(" ".join(re.findall(r'[A-Z][^A-Z]*', name)))

    # small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_frame = np.ascontiguousarray(frame[:, :, ::-1])

    face_locations = await asyncio.to_thread(face_recognition.face_locations, rgb_frame)  # Run in background thread
    face_encodings = await asyncio.to_thread(face_recognition.face_encodings, rgb_frame, face_locations)  

    face_names = []
    for face_encoding in face_encodings:
        matches = await asyncio.to_thread(face_recognition.compare_faces, known_face_encodings, face_encoding)
        name = "Unknown"

        if known_face_encodings:
            face_distances = await asyncio.to_thread(face_recognition.face_distance, known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]

        face_names.append(name)

    for (top, right, bottom, left), name in zip(face_locations, face_names):
        print(f"Detected: {name} at {top}, {right}, {bottom}, {left}")
    
    height, width, _ = rgb_frame.shape
    center = [height / 2, width / 2]

    best_dist = 100000000
    best_name = None
    best_idx = 0
    i = 0
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        cur_center = [(top + bottom) / 2, (left + right) / 2]
        
        dist = sum([(cur_center[i] - center[i])**2 for i in range(2)])
        if (dist < best_dist):
            best_dist = dist
            best_name = name
            best_idx = i
        i+=1

    if best_name == None:
        print("No one detected")
        return
    print(best_name)

    if (best_name == "Unknown"):
        fn = "James"
        ln = "Chen"

        top, right, bottom, left = face_locations[best_idx]
    
        padding = 250
        
        top = max(0, top - padding)
        left = max(0, left - padding)
        bottom = min(height, bottom + padding)
        right = min(width, right + padding)

        # Crop the face region
        cropped_face = (rgb_frame[top:bottom, left:right])[:, :, ::-1]

        # Show the cropped face
        cv2.imwrite(f"{imgpath}/{fn}{ln}.png", cropped_face)

        # img, link, about, experiences, education = linkedin.scrape(fn, ln, log=True)

        # a, b, c = linkedin.format_info(about, experiences, education)
        img, link, about, experiences, education = await asyncio.to_thread(linkedin.scrape, fn, ln, log=True)
        a, b, c = await asyncio.to_thread(linkedin.format_info, about, experiences, education)

        print(a)
        print()
        print()
        print(b)
        print()
        print()
        print(c)

    print(f"total time: {time.time() - start_time}")

async def main():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    loop = asyncio.get_running_loop()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break

        cv2.imshow('Camera Feed', frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):  # Quit on 'q'
            break
        elif key == ord(' '):  # Space key pressed
            print("Spacebar pressed! Starting async detection...")
            loop.create_task(detect_async(frame.copy()))  # Schedule face detection

        await asyncio.sleep(0.05)

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    asyncio.run(main())
