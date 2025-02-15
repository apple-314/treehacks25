from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import numpy as np
from scipy.io.wavfile import write
import whisper
import os

app = FastAPI()

# Global list to store audio samples sent from Swift
accumulated_samples: List[float] = []

# Initialize Whisper model (this will download it the first time)
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
