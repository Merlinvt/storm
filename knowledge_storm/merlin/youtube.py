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

def get_video_info(video_url: str, download_transcript: bool = True, cache_file: str = "transcripts_cache.json") -> Dict[str, Any]:
    """
    Get detailed information about a specific video including transcript
    
    Args:
        video_url: Full YouTube video URL
        download_transcript: Whether to download and transcribe audio
        cache_file: Path to JSON file for caching transcripts
        
    Returns:
        Dictionary containing video metadata and transcript
    """
    import os
    import json
    
    # Load cache if it exists
    transcripts_cache = {}
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                transcripts_cache = json.load(f)
        except Exception as e:
            print(f"Error loading cache: {e}")
    
    try:
        # First get video info
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(video_url, download=False)
        
        video_id = info.get('id', '')
        result = {
            'id': video_id,
            'title': info.get('title', ''),
            'description': info.get('description', ''),
            'duration': info.get('duration', 0),
            'view_count': info.get('view_count', 0),
            'transcript': ''
        }
        
        if download_transcript:
            # Check cache first
            if video_id in transcripts_cache:
                print(f"Using cached transcript for {video_id}")
                result['transcript'] = transcripts_cache[video_id]
            else:
                # Download and transcribe if not in cache
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                    }],
                    'outtmpl': f"{video_id}.%(ext)s"
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([video_url])
                
                # Use OpenAI Whisper API for transcription
                from openai import OpenAI
                client = OpenAI()
                
                with open(f"{video_id}.mp3", "rb") as audio_file:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                result['transcript'] = transcript.text
                
                # Save to cache
                transcripts_cache[video_id] = transcript.text
                try:
                    with open(cache_file, 'w') as f:
                        json.dump(transcripts_cache, f, indent=2)
                except Exception as e:
                    print(f"Error saving to cache: {e}")
                
                # Cleanup
                if os.path.exists(f"{video_id}.mp3"):
                    os.remove(f"{video_id}.mp3")
                
        return result
    except Exception as e:
        print(f"Error getting video info: {e}")
        return {}
