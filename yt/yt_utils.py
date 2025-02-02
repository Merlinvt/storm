'''
YouTube utilities for downloading and transcribing videos
'''

import yt_dlp
import whisper
import os
from typing import Dict, Optional

def load_model():
    return whisper.load_model("base")

model = load_model()

def yt_get(video_url: str) -> Optional[str]:
    """Download YouTube video audio and return path"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': '%(id)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            return f"{info['id']}.mp3"
    except Exception as e:
        print(f"Error downloading {video_url}: {e}")
        return None

def yt_transcribe(video_path: str) -> str:
    """Transcribe video file using OpenAI Whisper API"""
    try:
        from openai import OpenAI
        client = OpenAI()
        
        with open(video_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        os.remove(video_path)  # Clean up downloaded file
        return transcript.text
    except Exception as e:
        print(f"Error transcribing {video_path}: {e}")
        return ""
