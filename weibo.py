import contextlib
import traceback
import re
import time
import requests
import json
from html import unescape
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from util import logger, convert_chinese_to_arabic, extract_text_from_html

HOT_SEARCH_URL = "https://s.weibo.com/top/summary"
HOT_SEARCH_ITEM_SEQ_PREFIX = "https://simg.s.weibo.com/wb_search_img_search"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
    "Cookie": "SUB=_2AkMWJrkXf8NxqwJRmP8SxWjnaY12zwnEieKgekjMJRMxHRl-yj9jqmtbtRB6PaaX-IGp-AjmO6k5cS-OH2X9CayaTzVD"
}

RETRIES = Retry(total=3,
                backoff_factor=1,
                status_forcelist=[k for k in range(400, 600)])


@contextlib.contextmanager
def request_session():
    session = requests.session()
    try:
        session.headers.update(HEADERS)
        session.mount("http://", HTTPAdapter(max_retries=RETRIES))
        session.mount("https://", HTTPAdapter(max_retries=RETRIES))
        yield session
    finally:
        session.close()


class Weibo:

    @staticmethod
    def get_hot_search():
        """
        微博热搜
        """
        rsp_text = None
        try:
            with request_session() as s:
                response = s.get(HOT_SEARCH_URL)
                if response.status_code != 200:
                    logger.error(f'weibo: get hot search failed! code:{response.status_code}, text:{response.text}')
                    return None, response

                result = response.text
                regexp = re.compile(r'<a href="(/weibo\?q=[^"]+)".*?>(.+?)</a>', re.S)
                words = []
                crawl_time = int(time.time())
                for m in regexp.finditer(result):
                    raw_url = m.group(1)
                    # 若 raw_url 已包含 http(s) 则保持，否则补全为主机 https://s.weibo.com/
                    full_url = raw_url if raw_url.startswith(("http://", "https://")) else urljoin("https://s.weibo.com", raw_url)

                    raw_html = m.group(2)
                    soup = BeautifulSoup(raw_html, "html.parser")
                    span = soup.find("span")
                    if span:
                        # 删除 <em>（热度数字）并获取纯文本
                        for em in span.find_all("em"):
                            em.decompose()
                        title = unescape(span.get_text(strip=True))
                    else:
                        # 回退：移除所有 <em> 并取剩余文本
                        for em in soup.find_all("em"):
                            em.decompose()
                        title = unescape(soup.get_text(" ", strip=True))
                    word = {"url": full_url, "title": title, 'crawl_time': crawl_time}
                    words.append(word)
                    logger.info(f"weibo: get hot search item:{title} ")

                return words, response
        except:
            logger.exception(f'weibo: get hot search failed! rsp_text:{rsp_text}')
            return None, None


if __name__ == "__main__":
    items, text = Weibo.get_hot_search()
    if items:
        for item in items:
            logger.info('item:%s', item)