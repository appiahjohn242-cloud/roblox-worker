import modal
import subprocess
import asyncio
import edge_tts
from fastapi import Response

app = modal.App("roblox-3d-webhook")

image = (
    modal.Image.debian_slim()
    .apt_install("blender", "ffmpeg")
    .pip_install("edge-tts", "fastapi[standard]")
)

async def make_voiceover(text: str, output_path: str):
    communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural", rate="+15%")
    await communicate.save(output_path)

@app.function(image=image, gpu="T4", timeout=1800)
@modal.fastapi_endpoint(method="POST")
def generate_3d_webhook(payload: dict):
    story_script = payload.get("story", "Welcome to Roblox town!")
    bpy_code = payload.get("bpy_code", "")

    asyncio.run(make_voiceover(story_script, "/tmp/voice.mp3"))

    with open("/tmp/scene.py", "w") as f:
        f.write(bpy_code)
    subprocess.run(["blender", "--background", "--python", "/tmp/scene.py"], check=True)

    subprocess.run([
        "ffmpeg", "-y",
        "-i", "/tmp/raw_render.mp4",
        "-i", "/tmp/voice.mp3",
        "-c:v", "copy", "-c:a", "aac", "-shortest",
        "/tmp/final_short.mp4"
    ], check=True)

    with open("/tmp/final_short.mp4", "rb") as f:
        video_bytes = f.read()

    return Response(content=video_bytes, media_type="video/mp4")
  
