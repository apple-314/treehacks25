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
from jarvis import jarvis_handle, get_summary, update_summary
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

# @app.post("/jarvis")
# async def jarvis(data: dict):
#     message = data["message"]
#     answer, agent = jarvis_handle(db, message)
#     return {
#         "answer": answer,
#         "agent": agent
#     }

@app.post("/save_transcript")
async def save_transcript(data: dict):
    transcript = data["transcript"]
    fn =  data["fn"]
    ln =  data["ln"]
    id_name = fn+ln

    ts = {
        "time_stamp" : str(datetime.now().replace(microsecond=0))
    }

    cur_contact = db.get_entries_w_col_match("General", "Contacts", "id_name", id_name)
    cur_summary = cur_contact[0][4]

    summary = get_summary(transcript)

    if cur_summary:
        db.update_row_from_table("General", "Contacts", "id_name", id_name, "conv_summary", summary)
        db.update_row_from_table("General", "Contacts", "id_name", id_name, "most_recent_conv_summary", summary)
    else:
        db.update_row_from_table("General", "Contacts", "id_name", id_name, "conv_summary", update_summary(cur_summary, transcript))
        db.update_row_from_table("General", "Contacts", "id_name", id_name, "most_recent_conv_summary", summary)
        
        return {}

@app.post("/save_contact")
async def save_contact(data: dict):
    fn =  data["fn"]
    ln =  data["ln"]
    id_name = fn+ln
    phone = data["phone"]
    conv_summary = ""
    most_recent_conv_summary = ""

    data = {
        "time_stamp" : str(datetime.now().replace(microsecond=0))
    }

    data_dict = {"fname": fn, "lname": ln, "id_name": id_name, "phone": phone, "conv_summary": conv_summary, "most_recent_conv_summary": most_recent_conv_summary}
    db.write_data_dict("General", "Contacts", data_dict[i])
    
    return {}

@app.post("/upload_samples_jarvis")
async def upload_samples_jarvis(data: AudioSamples):
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

@app.post("/finalize_jarvis")
async def finalize_audio_jarvis():
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

    answer, agent = jarvis_handle(db, transcription)
    print(answer)
    return {
        "answer": answer,
        "agent": agent
    }

app.post("/get_profiles")
async def get_profiles():
    names = db.get_column_from_table("General", "Contacts", "id_name")
    names = [p[0] for p in names]

    data = {}
    for name in names:
        formatted_name = "".join([c if c.islower() else " " + c for c in name]).strip()

        # Fetch LinkedIn data
        bio_result = db.get_entries_w_col_match(name, "LinkedIn", "type", "bio")
        bio = bio_result[0][1] if bio_result else ""

        exp_results = db.get_entries_w_col_match(name, "LinkedIn", "type", "exp")
        experiences = [entry[1] for entry in exp_results] if exp_results else []

        edu_results = db.get_entries_w_col_match(name, "LinkedIn", "type", "edu")
        education = [entry[1] for entry in edu_results] if edu_results else []

        # get image from "pfp" type under LinkedIn
        img_results = db.get_row_from_table(name, "LinkedIn", "type", "pfp")
        image = img_results[0][1] if img_results else ""

        # get interests from "interests" type under LinkedIn
        interests_results = db.get_row_from_table(name, "LinkedIn", "type", "interests")
        interests = interests_results[0][1] if interests_results else ""

        # Structure data
        data[formatted_name] = {
            "LinkedIn": {
                "bio": bio,
                "experiences": experiences,
                "education": education
            },
            "convos": [],
            "interests": interests,
            "img": image
        }

    return data