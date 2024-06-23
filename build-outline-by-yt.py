import asyncio
import time
from functools import wraps
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
from langchain.llms import Ollama
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# 计时装饰器
def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} 执行时间: {end_time - start_time:.2f} 秒")
        return result
    return wrapper

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

ollama_embedding = OllamaEmbeddings(model=OLLAMA_EMBEDDIG_MODEL, base_url=OLLAMA_URL, temperature=0.1)
llm = Ollama(model=OLLAMA_LLM_MODEL, base_url=OLLAMA_URL, temperature=0.5)

# Initialize AstraDB
vstore = AstraDBVectorStore(
    embedding=ollama_embedding,
    collection_name=ASTRA_COLLECTION,
    api_endpoint=ASTRA_DB_ENDPOINT,
    token=ASTRA_TOKEN,
)

def save_script_to_file(script, title):
    filename = os.path.join(SAVE_DIRECTORY, f"{title}.txt")
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(script)
    print(f"Script saved to {filename}")

@timer
def analyze_channel_content():
    filename = os.path.join(SAVE_DIRECTORY, f"all_texts.txt")
    if os.exists(filename):
        with open(filename, 'r', encoding='utf-8') as file:
            all_texts = file.readlines()
    else:
        # 获取所有文档进行分析
        all_texts = " ".join([doc.page_content for doc in vstore.similarity_search("", k=1000)])
        save_script_to_file(all_texts, "all_texts")

    # 创建频道风格描述的 prompt
    style_prompt = PromptTemplate(
        input_variables=["channel_content"],
        template="基于以下来自YouTube频道的内容, 描频道的整体述风格和背景: {channel_content}"
    )

    # 创建 LLMChain 用于生成频道风格描述
    style_chain = LLMChain(llm=llm, prompt=style_prompt)

    # 生成频道风格描述
    channel_style = style_chain.run(all_texts)
    print("频道风格描述：", channel_style)
    return channel_style

@timer
def generate_topic(channel_style):
    # 创建选题生成的 prompt
    topic_prompt = PromptTemplate(
        input_variables=["channel_style"],
        template="你是一个自媒体写作专家，基于以下频道风格描述, 推荐5个爆款主题，要求内容有深度和广度，可以基于事实和案例写出5000到10000字的文章: {channel_style}"
    )

    # 创建 LLMChain 用于生成选题
    topic_chain = LLMChain(llm=llm, prompt=topic_prompt)

    # 生成选题
    topic = topic_chain.invoke(channel_style)
    print("建议的选题：", topic)
    return topic

@timer
def generate_outline(topic):
    # 创建大纲生成的 prompt
    outline_prompt = PromptTemplate(
        input_variables=["topic"],
        template="为以下每个主题创建相应的写作大纲，要求包括标题、背景、结论、所需论据和案例: {topic}"
    )

    # 创建 LLMChain 用于生成大纲
    outline_chain = LLMChain(llm=llm, prompt=outline_prompt)

    # 生成大纲
    outline = outline_chain.invoke(topic)
    print("视频大纲：", outline)

@timer
def main():
    channel_style = analyze_channel_content()
    topic = generate_topic(channel_style)
    generate_outline(topic)

if __name__ == "__main__":
    main()