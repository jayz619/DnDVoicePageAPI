from fastapi import FastAPI, Request
from pydantic import BaseModel
import requests
import base64
import os
import tempfile

app = FastAPI()

ELEVENLABS_API_KEY = "sk_7723ae0f43fc2638619ac7cbf13baf7b16bcc4b49a7f3262"  # Replace with your actual key

class VoiceRequest(BaseModel):
    userText: str
    selectedVoiceid: str

def upload_to_fileio(audio_bytes: bytes) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
        temp_file.write(audio_bytes)
        temp_file_path = temp_file.name

    with open(temp_file_path, 'rb') as file_data:
        upload_response = requests.post("https://file.io", files={"file": file_data})
        result = upload_response.json()

    if result.get("success"):
        return result["link"]
    else:
        raise Exception("Upload failed: " + str(result))

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
        public_audio_url = upload_to_fileio(audio_bytes)

        return {"audioUrl": public_audio_url}

    except Exception as e:
        return {"error": str(e)}

# Required for local testing; Render will use its own entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
