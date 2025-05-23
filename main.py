import os
import json
import uuid
import firebase_admin
from firebase_admin import credentials, storage, auth
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import requests
from datetime import datetime

# Load Firebase credentials from environment variable
creds_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
if creds_json:
    cred = credentials.Certificate(json.loads(creds_json))
    firebase_admin.initialize_app(cred, {
        'storageBucket': "dn-d-v3-2gt5bn.appspot.com"
    })

app = FastAPI()

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")

class VoiceRequest(BaseModel):
    userText: str
    selectedVoiceid: str
    selectedEmotion: str

@app.post("/generate")
async def generate_audio(data: VoiceRequest, authorization: str = Header(...)):
    try:
        # 🔐 Verify Firebase Auth token
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid Authorization header")
        id_token = authorization.split("Bearer ")[1]
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token["uid"]  # Optional: log or use if needed

        # 📖 Emotion narrative mapping
        emotion_map = {
            "angry": "he shouted in rage.",
            "happy": "he said with joy.",
            "sad": "he whispered sadly.",
            "scared": "he said with fear in his voice.",
            "calm": "he said peacefully.",
            "excited": "he said, brimming with excitement."
        }
        narrative = emotion_map.get(data.selectedEmotion.lower(), "he said.")

        # 🎙️ Call ElevenLabs API
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

        # ☁️ Upload to Firebase Storage with UUID filename
        bucket = storage.bucket()
        unique_id = str(uuid.uuid4())
        filename = f"voiceOvers/{unique_id}.mp3"
        blob = bucket.blob(filename)
        blob.upload_from_string(response.content, content_type="audio/mpeg")

        # 🌐 Make file public
        blob.make_public()

        # ✅ Return permanent public URL
        return {
            "audioUrl": blob.public_url,
            "filePath": filename
        }

    except Exception as e:
        return {"error": str(e)}
