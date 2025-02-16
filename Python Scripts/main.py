from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import numpy as np
from scipy.io.wavfile import write
import whisper
import mss
import cv2
from datetime import datetime

from linkedin import scrape, update_db
from jarvis import jarvis_handle
from vector_db import VectorDatabase

db = VectorDatabase()
db.create_connection()

app = FastAPI()

accumulated_samples: List[float] = []

model = whisper.load_model("base")

class AudioSamples(BaseModel):
    samples: List[float]

@app.post("/upload_samples")
async def upload_samples(data: AudioSamples):
    """
    Endpoint for streaming audio samples from Swift.
    The payload should be a JSON object like:
      { "samples": [0.02977, 0.03075, ...] }
    """
    global accumulated_samples
    accumulated_samples.extend(data.samples)
    return {
        "message": f"Received {len(data.samples)} samples. Total samples stored: {len(accumulated_samples)}."
    }

@app.post("/finalize")
async def finalize_audio():
    """
    Endpoint to finalize the audio stream.
    This converts all accumulated samples into a WAV file.
    """
    global accumulated_samples
    if not accumulated_samples:
        raise HTTPException(status_code=400, detail="No audio samples received.")

    # Convert the accumulated samples to a numpy array (float32)
    audio_data = np.array(accumulated_samples, dtype=np.float32)

    # Convert the float samples (assumed to be in -1.0 to 1.0) to 16-bit PCM values.
    audio_int16 = np.int16(audio_data * 32767)

    # Define the sample rate in Hz (adjust if needed)
    sample_rate = 44100
    output_file = "output.wav"

    # Write the audio data to a WAV file.
    write(output_file, sample_rate, audio_int16)

    # Transcribe the audio using Whisper
    try:
        result = model.transcribe(output_file)
        transcription = result["text"].strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        # Clear the accumulator after finalizing
        accumulated_samples.clear()

    print(transcription)
    return {"transcription": transcription}

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
    if not hasattr(app, 'timestamps'):
        app.timestamps = []

    app.timestamps.append(data["timestamp"])

    screenshot_file = capture_single_screenshot()
    first_name = "Kaival"
    last_name = "Shah"
    pfp, pf, about, experiences, education = await scrape(first_name, last_name, screenshot_file)

    update_db(db, first_name, last_name, about, experiences, education)

    # SAVE TO DB
    
    if pf is None:
        return {
            "message": f"Received timestamp: {data['timestamp']}. Total gestures captured: {len(app.timestamps)}. No matching LinkedIn profile found.",
            "screenshot": screenshot_file
        }
        
    print("Profile found!")
    print(f"About: {about}")
    print(f"Experiences: {experiences}")
    print(f"Education: {education}")
    print(f"PFP link: {pfp}")
    
    return {
        "message": f"Received timestamp: {data['timestamp']}. Total gestures captured: {len(app.timestamps)}.",
        "screenshot": screenshot_file,
        "profile": {
            "name": first_name + " " + last_name,
            "about": about,
            "experiences": experiences,
            "education": education,
            "profile_url": pf
        }
    }

@app.post("/jarvis")
async def jarvis(data: dict):
    """
    Endpoint for capturing pinch gesture timestamps from Vision Pro.
    The payload should be a JSON object like:
    { "timestamp": "2025-02-15T10:30:45Z" }
    """
    # error check?

    message = data["message"]
    answer, agent = jarvis_handle(db, message)
    return {
        "answer": answer,
        "agent": agent
    }