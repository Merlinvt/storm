import yt_dlp
from typing import List, Dict, Any

def search_videos(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search YouTube videos using yt-dlp
    
    Args:
        query: Search query string
        limit: Maximum number of results to return
        
    Returns:
        List of video entries with metadata
    """
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'force_generic_extractor': True,
        'no_warnings': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            results = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
            if results and 'entries' in results:
                return [{
                    'id': entry.get('id', ''),
                    'title': entry.get('title', ''),
                    'url': f"https://www.youtube.com/watch?v={entry.get('id', '')}",
                    'duration': entry.get('duration', 0),
                    'view_count': entry.get('view_count', 0),
                    'description': entry.get('description', '')
                } for entry in results['entries']]
    except Exception as e:
        print(f"Error searching videos: {e}")
    return []

def get_video_info(video_url: str, download_transcript: bool = True) -> Dict[str, Any]:
    """
    Get detailed information about a specific video including transcript
    
    Args:
        video_url: Full YouTube video URL
        download_transcript: Whether to download and transcribe audio
        
    Returns:
        Dictionary containing video metadata and transcript
    """
    import whisper
    import os
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
    }
    
    try:
        # First get video info
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(video_url, download=False)
        
        result = {
            'id': info.get('id', ''),
            'title': info.get('title', ''),
            'description': info.get('description', ''),
            'duration': info.get('duration', 0),
            'view_count': info.get('view_count', 0),
            'transcript': ''
        }
        
        if download_transcript:
            # Download audio and transcribe
            output_file = f"{info['id']}"
            ydl_opts['outtmpl'] = f"{output_file}.%(ext)s"
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            # Use OpenAI Whisper API for transcription
            from openai import OpenAI
            client = OpenAI()
            
            with open(f"{output_file}.mp3", "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            result['transcript'] = transcript.text
            
            # Cleanup
            if os.path.exists(f"{output_file}.mp3"):
                os.remove(f"{output_file}.mp3")
                
        return result
    except Exception as e:
        print(f"Error getting video info: {e}")
        return {}
