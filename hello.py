from knowledge_storm.merlin.youtube import get_video_info, search_videos

def main():
    #result = search_videos("bagger videos kinder")
    #print(result)
    result2 = get_video_info("https://www.youtube.com/watch?v=4UWgVAgSBEs")
    print(result2)
    


if __name__ == "__main__":
    main()
