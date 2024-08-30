import asyncio
import os
from pyppeteer import launch
from langchain_community.document_loaders import YoutubeLoader
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# 从环境变量中获取配置
PROXY_SERVER = os.getenv('PROXY_SERVER', 'http://127.0.0.1:1087')
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 1000))
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', 200))
CHANNEL_NAME = os.getenv('CHANNEL_NAME', 'Tankman2020')
YOUTUBE_LANG = str(os.getenv('YOUTUBE_LANG', 'zh-CN')).split(",")
CHROMA_COLLECTION_NAME = os.getenv('CHROMA_COLLECTION_NAME', 'youtube_scripts')
ASTRA_TOKEN = os.getenv('ASTRA_TOKEN', '')
ASTRA_DB_ENDPOINT = os.getenv('ASTRA_DB_ENDPOINT', '')
ASTRA_COLLECTION = os.getenv('ASTRA_COLLECTION', '')
SAVE_DIRECTORY = os.getenv('SAVE_DIRECTORY', './data')
OLLAMA_EMBEDDIG_MODEL = os.getenv('OLLAMA_EMBEDDIG_MODEL', '')
OLLAMA_LLM_MODEL = os.getenv('OLLAMA_LLM_MODEL', '')
OLLAMA_URL = os.getenv('OLLAMA_URL', '')
    

def save_script_to_file(script, title):
    filename = os.path.join(SAVE_DIRECTORY, f"{title}.txt")
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(script.page_content)
    print(f"Script saved to {filename}")

def extract_and_save_subtitles(video_url):
    loader = YoutubeLoader.from_youtube_url(video_url, language=YOUTUBE_LANG, add_video_info=True)
    documents = loader.load()

    if len(documents) > 0:
        script = documents[0].page_content
        title = documents[0].meta_data.get('title')

        save_script_to_file(script, title)

if __name__ == '__main__':
    # main('Tankman2020')
    extract_and_save_subtitles('https://www.youtube.com/watch?v=kOluwsYyd_c')
