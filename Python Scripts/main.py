from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import numpy as np
from scipy.io.wavfile import write

app = FastAPI()

app.timestamps = []

# Global list to store audio samples sent from Swift
accumulated_samples: List[float] = []

class AudioSamples(BaseModel):
    samples: List[float]

@app.post("/capture_gesture")
async def capture_gesture(data: dict):
    """
    Endpoint for capturing pinch gesture timestamps from Vision Pro.
    The payload should be a JSON object like:
    { "timestamp": "2025-02-15T10:30:45Z" }
    """
    global timestamps
    
    # Initialize timestamps list if it doesn't exist
    if not hasattr(app, 'timestamps'):
        app.timestamps = []
    
    # Store the timestamp
    app.timestamps.append(data["timestamp"])
    
    return {
        "message": f"Received timestamp: {data['timestamp']}. Total gestures captured: {len(app.timestamps)}."
    }