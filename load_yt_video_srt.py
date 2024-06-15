import asyncio
from pyppeteer import launch
from langchain.document_loaders import YoutubeLoader
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

async def get_youtube_videos(channel_url):
    # 启动浏览器
    browser = await launch(headless=True, args=['--proxy-server=http://127.0.0.1:10808'])
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

    # 等待视频标签加载
    # await page.waitForSelector('#video-title-link', timeout=10000)
    
    # 提取视频标题和URL
    video_data = await page.evaluate('''() => {
        let videos = [];
        let video_elements = document.querySelectorAll('a#video-title-link');
        video_elements.forEach(v => {
            let url = v.href;
            videos.push(url);
        });
        return videos;
    }''')

    # 关闭浏览器
    await browser.close()
    return video_data

async def extract_and_store_subtitles(video_url):
    loader = YoutubeLoader(video_url)
    documents = loader.load()
    
    # 设置Chroma数据库的存储路径
    chroma_db_path = "chroma_db"
    
    # 使用OpenAIEmbeddings进行文本嵌入
    embeddings = OpenAIEmbeddings()
    
    # 创建Chroma向量数据库
    vectorstore = Chroma(persist_directory=chroma_db_path, embedding_function=embeddings)
    
    # 将文档存储到Chroma数据库中
    vectorstore.add_documents(documents)
    
    # 持久化数据库
    vectorstore.persist()

def main(channel_name):
    channel_url = f'https://www.youtube.com/@{channel_name}/videos'  # 替换为实际的频道URL
    video_urls = asyncio.get_event_loop().run_until_complete(get_youtube_videos(channel_url))
    
    total_videos = len(video_urls)
    print(f"总视频数: {total_videos}")

    # 将数组转换为使用换行符分割的字符串
    videos = "\n".join(video_urls)

    extract_and_store_subtitles(videos)

    # 打印视频标题和URL，并显示进度
    # for index, video in enumerate(videos):
    #     print(f"Title: {video['title']}\nURL: {video['url']}\n")
    #     # 提取并存储字幕
    #     asyncio.get_event_loop().run_until_complete(extract_and_store_subtitles(video['url']))
    #     print(f"进度: {index + 1}/{total_videos} ({((index + 1) / total_videos) * 100:.2f}%)")

if __name__ == '__main__':
    main('Tankman2020')
