#Import things that are needed generically
from langchain.llms import OpenAI
from langchain import LLMMathChain, SerpAPIWrapper
from langchain.agents import AgentType, Tool, initialize_agent, tool
from langchain.chat_models import ChatOpenAI
from langchain.tools import BaseTool

import json
import os
from typing import Type
import yt_dlp
from yt_utils import yt_get, yt_transcribe



'''
CustomYTSearchTool searches YouTube videos related to a person and returns a specified number of video URLs.
Input to this tool should be a comma separated list,
 - the first part contains a person name
 - and the second(optional) a number that is the maximum number of video results to return
'''
class CustomYTSearchTool(BaseTool):
    name = "CustomYTSearch"
    description = "search for youtube videos associated with a person. the input to this tool should be a comma separated list, the first part contains a person name and the second a number that is the maximum number of video results to return aka num_results. the second part is optional"

    def _search(self, person:str, num_results) -> list:
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'force_generic_extractor': True,
            'no_warnings': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            results = ydl.extract_info(f"ytsearch{num_results}:{person}", download=False)
            if 'entries' in results:
                return [f"https://youtube.com/watch?v={entry['id']}" for entry in results['entries']]
        return []
    
    def _run(self, query: str) -> str:
        """Use the tool."""
        values = query.split(",")
        person = values[0]
        if len(values)>1:
            num_results = int(values[1])
        else:
            num_results=2
        return self._search(person,num_results)
    
    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("YTSS  does not yet support async")

'''
CustomYTTranscribeTool transcribes YouTube videos associated with someone and
saves the transcriptions in transcriptions.json in your current directory
'''

class CustomYTTranscribeTool(BaseTool):
    name = "CustomeYTTranscribe"
    description = "transcribe youtube videos associated with someone"

    def _summarize(self, url_csv:str) -> str:
        values_list = url_csv.split(",")
        url_set = set(values_list)
        datatype = type(url_set)
        print(f"[YTTRANSCIBE***], received type {datatype} = {url_set}")

        transcriptions = {}

        # Load cache if it exists
        cache_file = "transcripts_cache.json"
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    transcriptions = json.load(f)
            except Exception as e:
                print(f"Error loading cache: {e}")
                transcriptions = {}

        for video_url in url_set:
            # Extract video ID from URL
            try:
                with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                    info = ydl.extract_info(video_url, download=False)
                    video_id = info.get('id', '')
            except Exception as e:
                print(f"Error getting video ID for {video_url}: {e}")
                continue

            # Check if transcript is already cached
            if video_url in transcriptions:
                print(f"Using cached transcript for {video_url}")
                continue

            # Download and transcribe if not in cache
            video_path = yt_get(video_url)
            if video_path:
                transcription = yt_transcribe(video_path)
                transcriptions[video_url] = transcription
                print(f"Transcribed {video_url}")

        with open("transcriptions.json", "w") as json_file:
            json.dump(transcriptions, json_file)
            
        return
    
    def _run(self, query: str) -> str:
        """Use the tool."""
        return self._summarize(query)
    
    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("YTSS  does not yet support async")



if __name__ == "__main__":
    llm = OpenAI(temperature=0)
    tools = []

    tools.append(CustomYTSearchTool())
    tools.append(CustomYTTranscribeTool())
    
    agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)
    agent.run("search youtube for Laszlo Bock's youtube videos, and return upto 3 results. list out the results for  video URLs. for each url_suffix in the search JSON output transcribe the youtube videos")
