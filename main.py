from fastapi import FastAPI
from pydantic import BaseModel
import requests
import firebase_admin
from firebase_admin import credentials, storage
import uuid
import os
import io
import json

# Load Firebase credentials from env var
creds_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
if creds_json:
    cred = credentials.Certificate(json.loads(creds_json))
    firebase_admin.initialize_app(cred, {
        'storageBucket': f"{json.loads(creds_json)['project_id']}.appspot.com"
    })

app = FastAPI()

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")  # Set in your Render env vars

class VoiceRequest(BaseModel):
    userText: str
    selectedVoiceid: str

@app.post("/generate")
async def generate_audio(data: VoiceRequest):
    try:
        # Call ElevenLabs API
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

        # Upload to Firebase Storage
        file_name = f"audio/{uuid.uuid4()}.mp3"
        bucket = storage.bucket()
        blob = bucket.blob(file_name)
        blob.upload_from_file(io.BytesIO(audio_bytes), content_type='audio/mpeg')
        blob.make_public()

        return {"audioUrl": blob.public_url}

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
