import argparse
import os
import asyncio
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests
import string
import random
from difflib import SequenceMatcher
from pyppeteer import launch
from pypub import Epub

class Crawler:
    def __init__(self):
        pass

    async def crawl_topic(self, url, encode):
        topic = {"url": url, "encode": encode}
        print(f"Topic URL: {url}")
        self.topic = await self.get_hrefs_from_url(topic)
        print(f"Got links: {len(self.topic['hrefs'])}")
        await self.generate_epub(self.topic)

    def filter_links(self, links):
        clusters = self.cluster_links(links)
        max_cluster = max(clusters, key=len)
        return sorted(max_cluster, key=lambda x: x["index"])

    def cluster_links(self, links):
        clusters = []
        for link in links:
            placed = False
            for cluster in clusters:
                if self.similarity(cluster[0]["url"], link["url"]) > 0.6:
                    cluster.append(link)
                    placed = True
                    break
            if not placed:
                clusters.append([link])
        return clusters

    @staticmethod
    def similarity(a, b):
        return SequenceMatcher(None, a, b).ratio()

    def parse_link(self, base, link):
        return urljoin(base, link)


    async def generate_epub(self, topic):
        metadata = {
            "title": topic["name"],
            "author": "Anonymous",
            "lang": "zh",
            "cover": topic.get("cover", ""),
            "content": []
        }

        chapters = await asyncio.gather(*[
            self.get_chapter(self.parse_link(topic["url"], link["url"]), link["title"], topic["encode"])
            for link in topic["hrefs"]
        ])

        metadata["content"] = sorted([chapter for chapter in chapters if chapter], key=lambda x: x["index"])
        # epub = Epub(metadata, f"{topic['output']}{topic['name']}.epub")
        # epub.create()
        book = Epub(metadata.get("title"), creator=metadata.get("author"))
        # iterate page urls and retrieve chapters
        with book.builder as builder:
            dirs = builder.begin()
            print('building ebook at', dirs.basedir)
            for n, chapter in enumerate(chapters, 1):
                print(f'loading chapters {n}/{len(chapters)}')
                book.add_chapter(chapter['title'], chapter['data'])
                #NOTE: this random sleep time is to avoid bot
                # detection from spacebattles. if pages are queried
                # too quickly, the requests start getting denied.
                # sleep = random.randint(2, 15)
                # print('sleeping', sleep, 'seconds')
                # time.sleep(sleep)
            builder.finalize(f"{topic['name']}.epub")

    async def get_chapter(self, url, title, encoding):
        try:
            print(f"Crawling chapter URL: {url}")
            response = requests.get(url, timeout=30)
            response.encoding = encoding if encoding else "utf-8"
            soup = BeautifulSoup(response.content, "html.parser")
            chapter = {"title": title, "data": str(soup)}
            return chapter
        except Exception as e:
            print(f"Error fetching chapter: {e}")
            return None

    async def get_hrefs_from_url(self, topic):
        browser = await launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        page = await browser.newPage()
        await page.setUserAgent("Opera/9.80 (Windows NT 6.0) Presto/2.12.388 Version/12.14")
        await page.goto(topic["url"], {"timeout": 0})
        topic["name"] = self.escape_chars(await page.title())

        hrefs = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a')).map((a, i) => ({
                index: i,
                url: a.href,
                title: a.innerText.replace(/\\|\\//g, '')
            }));
        }''')

        await browser.close()

        links = [href for href in hrefs if href["url"] and not href["url"].startswith('javascript') and len(href["title"]) > 4]
        topic["hrefs"] = self.filter_links(links)
        return topic

    @staticmethod
    def escape_chars(title):
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        return ''.join(c for c in title if c in valid_chars)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate EPUB from website")
    parser.add_argument("-u", "--url", required=True, help="URL of the book")
    parser.add_argument("-e", "--encode", required=False, help="Encoding of the website", default="utf-8")
    args = parser.parse_args()

    crawler = Crawler(
    )

    asyncio.get_event_loop().run_until_complete(crawler.crawl_topic(args.url, args.encode))
