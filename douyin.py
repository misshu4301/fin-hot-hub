import contextlib
import json
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from util import logger

HOT_SEARCH_URL = 'https://aweme.snssdk.com/aweme/v1/hot/search/list/'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36'
}
QUERIES = {
    'device_platform': 'android',
    'version_name': '13.2.0',
    'version_code': '130200',
    'aid': '1128'
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


def _get_hot_item_flag(label):
    try:
        label_dict = {
            1: '新',
            3: '热',
            9: '挑战',
            11: '剧集',
            13: '综艺',
            17: '热议',
        }
        return label_dict.get(int(label), '')
    except:
        return ''


class Douyin:

    @staticmethod
    def get_hot_search():
        try:
            with request_session() as s:
                response = s.get(HOT_SEARCH_URL, params=QUERIES)
                if response.status_code != 200:
                    logger.error(f'get hot board failed! code:{response.status_code}, text:{response.text}')
                    return None, response
                obj = json.loads(response.text)
                if 'status_code' in obj and obj.get('status_code') == 0:
                    word_list = obj['data']['word_list']
                    word_items = [{'title': word_item.get("word"),
                                   'url': f"https://www.douyin.com/search/{quote(word_item.get('word'))}?type=general",
                                   'flag': _get_hot_item_flag(word_item.get("label", "")),
                                   'hot_value': word_item.get('hot_value'),
                                   'view_count': word_item.get('view_count'),
                                   'event_time': word_item.get('event_time')}
                                  for word_item in word_list]
                    return word_items, response
                return None, response
        except:
            logger.exception('get hot search failed')
            return None, None


if __name__ == "__main__":
    items, text = Douyin.get_hot_search()
    for item in items:
        logger.info('item:%s', item)
