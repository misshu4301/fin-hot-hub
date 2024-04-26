import contextlib
import traceback
import re
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from util import logger

HOT_SEARCH_URL = "https://m.weibo.cn/api/container/getIndex"
HOT_SEARCH_ITEM_SEQ_PREFIX = "https://simg.s.weibo.com/wb_search_img_search"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
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


def _get_item_flag(url):
    if url.startswith('https://simg.s.weibo.com/moter/flags/1_0.png'):
        return '新'
    if url.startswith('https://simg.s.weibo.com/moter/flags/2_0.png'):
        return '热'
    if url.startswith('https://simg.s.weibo.com/moter/flags/32768_0.png'):
        return '暖'
    return ''


def _get_item_hot_value(desc_extra):
    try:
        if ' ' in str(desc_extra):
            desc_flag, hot_value = desc_extra.split(' ')
            return int(hot_value), desc_flag
        else:
            return int(desc_extra), ''
    except:
        return None, ''


class Weibo:

    @staticmethod
    def get_hot_search():
        """
        微博热搜
        """
        try:
            with request_session() as s:
                payload = {
                    "containerid": "106003type%3D25%26t%3D3%26disable_hot%3D1%26filter_type%3Drealtimehot",
                    "extparam": "filter_type%3Drealtimehot%26mi_cid%3D100103%26pos%3D0_0%26c_type%3D30%26display_time%3D1550505541",
                    "luicode": "10000011",
                    "lfid": "231583",
                }
                response = s.get(HOT_SEARCH_URL, params=payload)
                if response.status_code != 200:
                    logger.error(f'get hot search failed! code:{response.status_code}, text:{response.text}')
                    return None, response
                hot_search_data = response.json()
                if hot_search_data.get("ok", 0):
                    cards = hot_search_data["data"]["cards"]
                    if cards:
                        hot_items_group = cards[0]["card_group"]
                        item_list = [{
                            'title': item_topic.get("desc", ""),
                            'url': item_topic.get("scheme", ""),
                            'flag': _get_item_flag(item_topic.get("icon", "")),
                            'hot_value': _get_item_hot_value(item_topic.get("desc_extr", ""))[0],
                            'flag_ext':  _get_item_hot_value(item_topic.get("desc_extr", ""))[1],
                            'extra': item_topic.get("desc_extr", "")
                        } for item_topic in hot_items_group if HOT_SEARCH_ITEM_SEQ_PREFIX in item_topic.get("pic", "")]
                        return item_list, response
                return None, response
        except:
            logger.exception('get hot search failed')
            return None, None


if __name__ == "__main__":
    items, text = Weibo.get_hot_search()
    if items:
        for item in items:
            logger.info('item:%s', item)