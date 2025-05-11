from fastapi import FastAPI
from pydantic import BaseModel
import os
import json
import firebase_admin
from firebase_admin import credentials, storage
import requests
import tempfile
import datetime

# Load Firebase credentials from env var
creds_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
if creds_json:
    cred = credentials.Certificate(json.loads(creds_json))
    firebase_admin.initialize_app(cred, {
        'storageBucket': f"{json.loads(creds_json)['project_id']}.appspot.com"
    })

app = FastAPI()

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")

class VoiceRequest(BaseModel):
    userText: str
    selectedVoiceid: str
    selectedEmotion: str

def apply_emotion_prompt(emotion: str, text: str) -> str:
    emotion_prompts = {
        "angry": f"He growled angrily, \"{text}\"",
        "sad": f"She whispered sadly, \"{text}\"",
        "excited": f"He exclaimed with excitement, \"{text}\"",
        "happy": f"She smiled and said, \"{text}\"",
        "narration": f"In a calm and descriptive tone, \"{text}\"",
        "neutral": text
    }
    return emotion_prompts.get(emotion.lower(), text)

@app.post("/generate")
async def generate_audio(data: VoiceRequest):
    try:
        formatted_text = apply_emotion_prompt(data.selectedEmotion, data.userText)

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{data.selectedVoiceid}"
        payload = {
            "text": formatted_text,
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

        # Upload to Firebase
        file_name = f"voiceOvers/voice_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
        bucket = storage.bucket()
        blob = bucket.blob(file_name)
        blob.upload_from_string(audio_bytes, content_type="audio/mpeg")
        blob.make_public()

        return {"audioUrl": blob.public_url}

    except Exception as e:
        return {"error": str(e)}
