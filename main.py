from fastapi import FastAPI
from pydantic import BaseModel
import requests
import firebase_admin
from firebase_admin import credentials, storage
import tempfile
import uuid
import os
import json

app = FastAPI()

# Load Firebase credentials from environment
firebase_creds = json.loads(os.getenv("FIREBASE_CREDENTIALS"))
cred = credentials.Certificate(firebase_creds)
firebase_admin.initialize_app(cred, {
    "storageBucket": os.getenv("FIREBASE_BUCKET")
})

ELEVENLABS_API_KEY = "sk_7723ae0f43fc2638619ac7cbf13baf7b16bcc4b49a7f3262"

class VoiceRequest(BaseModel):
    userText: str
    selectedVoiceid: str

def upload_to_firebase(audio_bytes: bytes) -> str:
    filename = f"{uuid.uuid4()}.mp3"
    blob = storage.bucket().blob(f"voiceOvers/{filename}")
    blob.upload_from_string(audio_bytes, content_type="audio/mpeg")
    blob.make_public()
    return blob.public_url

@app.post("/generate")
async def generate_audio(data: VoiceRequest):
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{data.selectedVoiceid}"
        payload = {
            "text": data.userText,
            "model_id": "eleven_multilingual_v2"
        }
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            return {"error": "Voice generation failed", "details": response.text}

        audio_bytes = response.content
        audio_url = upload_to_firebase(audio_bytes)

        return {"audioUrl": audio_url}

    except Exception as e:
        return {"error": str(e)}

# For local testing only (Render ignores this)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
