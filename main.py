from fastapi import FastAPI, Request
from pydantic import BaseModel
import requests
import base64
import os

app = FastAPI()

ELEVENLABS_API_KEY = "sk_7723ae0f43fc2638619ac7cbf13baf7b16bcc4b49a7f3262"  # Replace with your actual key

class VoiceRequest(BaseModel):
    userText: str
    selectedVoiceid: str

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

        audio_base64 = base64.b64encode(response.content).decode("utf-8")
        return {"audioBase64": audio_base64}

    except Exception as e:
        return {"error": str(e)}

# Important for Railway/Render
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
