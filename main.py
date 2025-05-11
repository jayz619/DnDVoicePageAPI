from fastapi import FastAPI
from pydantic import BaseModel
import requests
import firebase_admin
from firebase_admin import credentials, storage
import os
import uuid
import json

# Load Firebase credentials
creds_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
if creds_json:
    cred = credentials.Certificate(json.loads(creds_json))
    firebase_admin.initialize_app(cred, {
        "storageBucket": "dn-d-v3-2gt5bn.appspot.com"
    })

# Get ElevenLabs API Key
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")

# FastAPI app
app = FastAPI()

# Request model
class VoiceRequest(BaseModel):
    userText: str
    selectedVoiceid: str
    selectedEmotion: str

# Emotion prompt injector
def format_prompt(text: str, emotion: str) -> str:
    cues = {
        "angry": "[speak with rage and aggression]",
        "happy": "[speak cheerfully and with excitement]",
        "sad": "[speak softly with a somber tone]",
        "narrator": "[narrate with clarity and depth]",
        "whisper": "[speak in a low whisper]",
        "robotic": "[speak in a robotic monotone]",
    }
    cue = cues.get(emotion.lower(), "")
    return f"{cue} {text}"

# API Endpoint
@app.post("/generate")
async def generate_audio(data: VoiceRequest):
    try:
        formatted_text = format_prompt(data.userText, data.selectedEmotion)
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{data.selectedVoiceid}"

        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "text": formatted_text,
            "model_id": "eleven_multilingual_v2"
        }

        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            return {
                "error": "Voice generation failed",
                "details": response.text
            }

        # Upload to Firebase Storage
        file_name = f"voiceovers/{str(uuid.uuid4())}.mp3"
        bucket = storage.bucket()
        blob = bucket.blob(file_name)
        blob.upload_from_string(response.content, content_type="audio/mpeg")
        blob.make_public()

        return {"audioUrl": blob.public_url}

    except Exception as e:
        return {"error": str(e)}

# Local testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
