from fastapi import FastAPI
from pydantic import BaseModel
import requests
import base64

app = FastAPI()

ELEVENLABS_API_KEY = "sk-b6cc403f5874b3e6ceaf686e30bf60f8bbe90d9c091e27d4"

class GenerateVoiceRequest(BaseModel):
    userText: str
    selectedEmotion: str
    selectedVoiceid: str

@app.post("/generate")
async def generate_voice(data: GenerateVoiceRequest):
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{data.selectedVoiceid}"

        payload = {
            "text": data.userText,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.8,
                "style": 0.5,
                "use_speaker_boost": True
            }
        }

        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            return {
                "error": "Voice generation failed",
                "details": response.text
            }

        audio_base64 = base64.b64encode(response.content).decode("utf-8")
        return { "audioBase64": audio_base64 }

    except Exception as e:
        return { "error": str(e) }