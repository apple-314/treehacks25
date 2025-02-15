from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import numpy as np
from scipy.io.wavfile import write

app = FastAPI()

# Global list to store audio samples sent from Swift
accumulated_samples: List[float] = []

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

    # Optionally clear the accumulator after finalizing the WAV file.
    sample_count = len(audio_int16)
    accumulated_samples = []

    return {
        "message": f"WAV file saved as '{output_file}' with {sample_count} samples at {sample_rate} Hz."
    }
