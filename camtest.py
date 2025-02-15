import cv2
import numpy as np
import mss
import os
import time

# Create a directory to save images
save_dir = 'captured_frames'
os.makedirs(save_dir, exist_ok=True)

frame_count = 0

with mss.mss() as sct:
    # Capture the entire primary monitor's screen.
    # If you want all monitors combined, use sct.monitors[0]
    monitor = sct.monitors[1]

    # Create a named window and set it to fullscreen
    cv2.namedWindow("AirPlay Stream", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("AirPlay Stream", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while True:
        # Grab a screenshot of the entire monitor
        screenshot = sct.grab(monitor)
        # Convert to a NumPy array and change color format from BGRA to BGR
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        
        # Increment frame counter
        frame_count += 1
        
        # Save an image every 5 frames
        if frame_count % 5 == 0:
            filename = os.path.join(save_dir, f"frame_{frame_count}.png")
            cv2.imwrite(filename, frame)
            print(f"Saved {filename}")
        
        # Display the frame in fullscreen
        cv2.imshow("AirPlay Stream", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cv2.destroyAllWindows()
