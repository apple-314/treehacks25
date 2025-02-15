from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import numpy as np
from scipy.io.wavfile import write
import cv2
import mss
import os
from datetime import datetime

app = FastAPI()

def capture_single_screenshot():
    """Capture a single screenshot and save it with timestamp"""
    with mss.mss() as sct:
        # Capture the primary monitor's screen
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        # Convert to a NumPy array and change color format from BGRA to BGR
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        
        # Create timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        
        # Save the image
        cv2.imwrite(filename, frame)
        return filename

@app.post("/capture_gesture")
async def capture_gesture(data: dict):
    """
    Endpoint for capturing pinch gesture timestamps from Vision Pro.
    The payload should be a JSON object like:
    { "timestamp": "2025-02-15T10:30:45Z" }
    """
    # Initialize timestamps list if it doesn't exist
    if not hasattr(app, 'timestamps'):
        app.timestamps = []
    
    # Store the timestamp
    app.timestamps.append(data["timestamp"])
    
    # Capture and save screenshot
    screenshot_file = capture_single_screenshot()
    
    return {
        "message": f"Received timestamp: {data['timestamp']}. Total gestures captured: {len(app.timestamps)}.",
        "screenshot": screenshot_file
    }