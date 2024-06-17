import asyncio
from pyppeteer import launch
from langchain_community.document_loaders import YoutubeLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import chromadb
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.embeddings import Embeddings

from langchain_astradb import AstraDBVectorStore
from astrapy.info import CollectionVectorServiceOptions
from datasets import load_dataset
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

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
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', '')
OLLAMA_URL = os.getenv('OLLAMA_URL', '')

ollama_embedding = OllamaEmbeddings(model=OLLAMA_MODEL, base_url=OLLAMA_URL, temperature=0.1)

# Initialize AstraDB
vstore = AstraDBVectorStore(
    embedding=ollama_embedding,
    collection_name=ASTRA_COLLECTION,
    api_endpoint=ASTRA_DB_ENDPOINT,
    token=ASTRA_TOKEN,
)

# 初始化 Chroma 客户端和集合
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection(name=CHROMA_COLLECTION_NAME)

async def get_youtube_videos(channel_url):
    # 启动浏览器
    browser = await launch(headless=True, args=[f'--proxy-server={PROXY_SERVER}'])
    page = await browser.newPage()
    
    # 打开YouTube频道页面
    await page.goto(channel_url)
    
    # 自动滚动页面，加载所有视频
    await page.evaluate('''(async () => {
        var scroll = setInterval(function(){ window.scrollBy(0, 1000); }, 1000);
        await new Promise((resolve, reject) => {
            setTimeout(() => {
                clearInterval(scroll);
                resolve();
            }, 30000); 
        });
    })''')
    
    # 提取视频标题和URL
    video_data = await page.evaluate('''() => {
        let videos = [];
        let video_elements = document.querySelectorAll('a#video-title-link');
        video_elements.forEach(v => {
            let title = v.title;
            let url = v.href;
            videos.push({title: title, url: url});
        });
        return videos;
    }''')
    
    # 关闭浏览器
    await browser.close()
    return video_data

def save_urls_to_file(videos, channel_name):
    filename = os.path.join(SAVE_DIRECTORY, f"{channel_name}_urls.txt")
    with open(filename, 'w', encoding='utf-8') as file:
        for video in videos:
            file.write(f"{video['title']}: {video['url']}\n")
    print(f"URLs saved to {filename}")

def save_script_to_file(script, title):
    filename = os.path.join(SAVE_DIRECTORY, f"{title}.txt")
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(script.page_content)
    print(f"Script saved to {filename}")

def save_to_chroma(split_texts, video_info):
    # 将每个分割的文本部分存入 Chroma
    for split_text in split_texts:
        collection.upsert(
            document=split_text,
            metadata={
                "title": video_info['title'],
                "url": video_info['url'],
                "channel_name": video_info['channel_name']
            }
        )
    print(f"Split script parts saved to Chroma for video: {video_info['title']}")

def save_to_astradb(split_texts):
    if len(split_texts) > 0:
        # if exists the same source
        source = split_texts[0].metadata.get('source')
        results = vstore.similarity_search(query=None, k=1, filter=dict(source=source))
        if len(results) > 0:
            print("documents already exist.")
            return
        inserted_ids_from_pdf = vstore.add_documents(split_texts)
        print(f"Inserted {len(inserted_ids_from_pdf)} documents.")

def main(channel_name):
    urls_filename = os.path.join(SAVE_DIRECTORY, f"{channel_name}_urls.txt")
    
    if os.path.exists(urls_filename):
        print(f"{urls_filename} already exists. Skipping video URL retrieval.")
        with open(urls_filename, 'r', encoding='utf-8') as file:
            videos = [{'title': line.split(': ')[0], 'url': line.split(': ')[1].strip()} for line in file]
    else:
        channel_url = f'https://www.youtube.com/@{channel_name}/videos'  # 替换为实际的频道URL
        videos = asyncio.get_event_loop().run_until_complete(get_youtube_videos(channel_url))
        save_urls_to_file(videos, channel_name)
    
    total_videos = len(videos)
    print(f"总视频数: {total_videos}")

    # 解析视频脚本并保存
    for video in videos:
        # script_filename = os.path.join(SAVE_DIRECTORY, f"{video['title']}.txt")
        # script = ""
        
        # if os.path.exists(script_filename):
        #     print(f"{script_filename} already exists. Skipping script retrieval.")
        #     with open(script_filename, 'r', encoding='utf-8') as file:
        #         script = file.read()
        # else:
        loader = YoutubeLoader.from_youtube_url(video['url'], language=YOUTUBE_LANG, add_video_info=True)
        result = loader.load()
        
        if len(result) > 0:
            script = result[0]  # Assuming `result` contains the script in 'text' key
            print(script.metadata, "exctracted")
        # else:
        #     print(f"无法解析视频: {video['title']}")
        #     continue
        # save_script_to_file(script, video['title'])
        
        # 使用RecursiveCharacterTextSplitter分割脚本
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP, add_start_index=True
        )
        split_texts = text_splitter.split_documents(result)

        # Save split texts to Chroma
        # video_info = {
        #     "title": video['title'],
        #     "url": video['url'],
        #     "channel_name": channel_name
        # }
        # save_to_chroma(split_texts, video_info)
        save_to_astradb(split_texts)

if __name__ == '__main__':
    main(CHANNEL_NAME)
