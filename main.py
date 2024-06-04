import asyncio
from pyppeteer import launch

async def get_youtube_videos(channel_url):
    # 启动浏览器
    browser = await launch(headless=True, args=['--proxy-server=http://127.0.0.1:1087'])
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
            let title = v.title;
            let url = v.href;
            videos.push({title: title, url: url});
        });
        return videos;
    }''')

    # 关闭浏览器
    await browser.close()
    return video_data

# 主函数
def main(channel_name):
    channel_url = f'https://www.youtube.com/@{channel_name}/videos'  # 替换为实际的频道URL
    videos = asyncio.get_event_loop().run_until_complete(get_youtube_videos(channel_url))
    
    total_videos = len(videos)
    print(f"总视频数: {total_videos}")

    # 打印视频标题和URL，并显示进度
    for video in enumerate(videos):
        print(f"Title: {video['title']}\nURL: {video['url']}\n")
        # print(f"进度: {index}/{total_videos} ({(index / total_videos) * 100:.2f}%)")
    return total_videos

if __name__ == '__main__':
    main('Tankman2020')