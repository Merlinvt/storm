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

def get_channel_videos(channel_url: str, limit: int = None, force_update: bool = False, cache_file: str = "channel_cache.json", fetch_only_new: bool = False) -> List[Dict[str, Any]]:
    """
    Get videos from a YouTube channel with caching
    
    Args:
        channel_url: Full YouTube channel URL
        limit: Maximum number of videos to return (None for all)
        force_update: Force refresh channel data instead of using cache
        cache_file: Path to JSON file for caching channel data
        fetch_only_new: Only fetch videos newer than the last cached video
        
    Returns:
        List of video entries with metadata
    """
    import os
    import json
    from datetime import datetime
    
    # Load cache if it exists
    channel_cache = {}
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                channel_cache = json.load(f)
        except Exception as e:
            print(f"Error loading cache: {e}")
    
    # Get latest video date from cache if it exists
    latest_date = None
    if fetch_only_new and channel_url in channel_cache and channel_cache[channel_url]['videos']:
        latest_date = max(v['upload_date'] for v in channel_cache[channel_url]['videos'])
        print(f"Only fetching videos newer than {latest_date}")
    
    # Check cache first unless force update
    if not force_update and not fetch_only_new and channel_url in channel_cache:
        print(f"Using cached data for {channel_url}")
        videos = channel_cache[channel_url]['videos']
        if limit:
            return videos[:limit]
        return videos
            
    # If not in cache or force update or fetching new videos, fetch from YouTube
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'force_generic_extractor': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'extract_flat': 'in_playlist'
    }
    
    # Add date filter if we're only fetching new videos
    if fetch_only_new and latest_date:
        ydl_opts['dateafter'] = latest_date
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            results = ydl.extract_info(channel_url, download=False)
            if results and 'entries' in results:
                new_videos = [{
                    'id': entry.get('id', ''),
                    'title': entry.get('title', ''),
                    'url': f"https://www.youtube.com/watch?v={entry.get('id', '')}",
                    'duration': entry.get('duration', 0),
                    'upload_date': entry.get('upload_date', ''),
                    'view_count': entry.get('view_count', 0),
                    'description': entry.get('description', '')
                } for entry in results['entries']]
                
                # If fetching only new videos, merge with existing cache
                if fetch_only_new and channel_url in channel_cache:
                    existing_videos = channel_cache[channel_url]['videos']
                    # Remove duplicates by ID
                    existing_ids = {v['id'] for v in existing_videos}
                    new_videos = [v for v in new_videos if v['id'] not in existing_ids]
                    videos = existing_videos + new_videos
                else:
                    videos = new_videos
                
                # Save to cache
                channel_cache[channel_url] = {
                    'last_updated': datetime.now().isoformat(),
                    'videos': videos
                }
                try:
                    with open(cache_file, 'w') as f:
                        json.dump(channel_cache, f, indent=2)
                except Exception as e:
                    print(f"Error saving to cache: {e}")
                
                if limit:
                    return videos[:limit]
                return videos
    except Exception as e:
        print(f"Error getting channel videos: {e}")
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
