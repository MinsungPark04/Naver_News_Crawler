import re
import time
import html
import json
import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging

logging.basicConfig(level=logging.ERROR)

class Crawler:
    def __init__(self, base_url, sections):
        self.base_url = base_url
        self.sections = sections
        self.urls = [f"{self.base_url}{section}" for section in self.sections]
        self.crawled_urls = set()

    def fetch(self, url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                logging.info(f"Fetched {url}")
                return response.text
        except Exception as e:
            logging.error(f"Error fetching {url}: {e}")
            return None
        
    def parse_links(self, html):
        try:
            soup = BeautifulSoup(html, 'html.parser')
            links = soup.find_all('a', href=True)
            links = [link['href'] for link in links if link['href'].startswith('https://n.news.naver.com/mnews/article')]
            return links
        except Exception as e:
            logging.error(f"Error parsing HTML for links: {e}")
            return []
    
    def parse_content(self, html):
        try:
            soup = BeautifulSoup(html, 'html.parser')
            title_tag = soup.find('div', {'class': 'media_end_head_title'}).find('h2')
            title = title_tag.get_text(strip=True) if title_tag else None
            content_tag = soup.find('article', {'id': 'dic_area'})
            content = content_tag.get_text(strip=True) if content_tag else None

            script = soup.find('script', text=re.compile('var section ='))
            section_info_json = re.search(r'var section = (.*?);', script.string, re.DOTALL | re.MULTILINE).group(1) if script else None
            section_info = json.loads(section_info_json)['name'] if section_info_json else None
            return title, content, section_info
        
        except Exception as e:
            logging.error(f"Error parsing HTML for content: {e}")
            return None, None, None

    def save_to_db(self, url, title, content, section_info):
        try:
            conn = sqlite3.connect('news.sqlite')
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS articles (url text, title text, content text, section_info text, crawl_time text)")
            crawl_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Get current time
            cursor.execute("INSERT INTO articles (url, title, content, section_info, crawl_time) VALUES (?, ?, ?, ?, ?)", (url, title, content, section_info, crawl_time))
            conn.commit()
            logging.info(f"Saved {url} to database")
        except Exception as e:
            logging.error(f"Error saving {url} to database: {e}")
        finally:
            if conn:
                conn.close()

    def crawl(self):
        for url in self.urls:
            section_html = self.fetch(url)
            if section_html:
                links = self.parse_links(section_html)
                for link in links:
                    if link not in self.crawled_urls:
                        article_html = self.fetch(link)
                        if article_html:
                            title, content, section_info = self.parse_content(article_html)
                            if title and content and section_info:
                                self.save_to_db(link, title, content, section_info)  # Save data to database
                                self.crawled_urls.add(link)
                                time.sleep(1)