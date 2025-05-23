import os
import json
import tempfile
import firebase_admin
from firebase_admin import credentials, storage
from fastapi import FastAPI
from pydantic import BaseModel
import requests
from datetime import datetime

# Load Firebase credentials from environment variable
creds_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
if creds_json:
    cred = credentials.Certificate(json.loads(creds_json))
    firebase_admin.initialize_app(cred, {
        'storageBucket': f"dn-d-v3-2gt5bn.firebasestorage.app"
    })

app = FastAPI()

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")

class VoiceRequest(BaseModel):
    userText: str
    selectedVoiceid: str
    selectedEmotion: str
    userId: str  # 🔒 Firebase UID

@app.post("/generate")
async def generate_audio(data: VoiceRequest):
    try:
        # Emotion to narrative mapping
        emotion_map = {
            "angry": "he shouted in rage.",
            "happy": "he said with joy.",
            "sad": "he whispered sadly.",
            "scared": "he said with fear in his voice.",
            "calm": "he said peacefully.",
            "excited": "he said, brimming with excitement."
        }

        narrative = emotion_map.get(data.selectedEmotion.lower(), "he said.")

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{data.selectedVoiceid}"
        payload = {
            "text": data.userText,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.3,
                "similarity_boost": 0.75,
                "use_speaker_boost": True
            },
            "next_text": narrative
        }
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            return {"error": "Voice generation failed", "details": response.text}

        # Upload to Firebase Storage — in user-specific folder
        bucket = storage.bucket()
        timestamp = datetime.utcnow().timestamp()
        filename = f"voiceOvers/{data.userId}/{timestamp}.mp3"
        blob = bucket.blob(filename)
        blob.upload_from_string(response.content, content_type="audio/mpeg")
        blob.make_public()

        return {"audioUrl": blob.public_url}

    except Exception as e:
        return {"error": str(e)}
