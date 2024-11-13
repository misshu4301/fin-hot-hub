import contextlib
import json

import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import quote

from util import logger

HOT_SEARCH_URL = 'https://www.xiaohongshu.com/fe_api/burdock/v3/user/hotlist'
# HOT_DETAIL_URL = 'xhsdiscover://search/result?keyword={0}'
HOT_DETAIL_URL = 'https://www.xiaohongshu.com/search_result?keyword={0}&type=51'

HEADERS = {
    'Host': 'www.xiaohongshu.com',
    'X-Sign': 'X3a39e2e09a99a049bc1fe186f033953e',
    'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1',
    'Referer': 'https://www.xiaohongshu.com/explore'
}

RETRIES = Retry(total=3,
                backoff_factor=1,
                status_forcelist=[k for k in range(500, 600)])


@contextlib.contextmanager
def request_session():
    session = requests.session()
    try:
        session.headers.update(HEADERS)
        session.mount("https://", HTTPAdapter(max_retries=RETRIES))
        yield session
    finally:
        session.close()


def _get_item_flag(url):
    if not url:
        return ''
    if url.startswith('https://picasso-static.xiaohongshu.com/fe-platform/cfd317ff14757c7ede6ef5176ec487589565e49e.png'):
        return '热'
    if url.startswith('https://sns-img-qc.xhscdn.com/search/trends/icon/label/new/version/1'):
        return '新'
    if url.startswith('https://picasso-static.xiaohongshu.com/fe-platform/4d6304d79d71bd1f68611ae09184b778ec1a6d97.png'):
        return '独家'
    return ''


class XHS:

    @staticmethod
    def get_hot_search():
        try:
            with request_session() as session:
                response = session.get(HOT_SEARCH_URL)
                if response.status_code != 200:
                    logger.error(f'get hot topic failed! code:{response.status_code}, text:{response.text}')
                    return None, response
                raw_data = json.loads(response.text)
                if 'success' in raw_data and raw_data.get('success'):
                    hot_list = raw_data.get('data')
                    crawl_time = int(time.time())
                    item_list = [
                        {'title': item_topic.get("title"),
                         'url': HOT_DETAIL_URL.format(quote(item_topic.get("title"))),
                         'flag': _get_item_flag(item_topic.get("icon", "")),
                         'crawl_time': crawl_time
                         }
                        for item_topic in hot_list]
                    return item_list, response
                return None, response
        except:
            logger.exception('get hot search failed')
            return None, None


if __name__ == "__main__":

    items, text = XHS.get_hot_search()
    if items:
        for item in items:
            logger.info('item:%s', item)
