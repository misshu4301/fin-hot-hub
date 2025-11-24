import contextlib
import traceback
import re
import time
import requests
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from util import logger, convert_chinese_to_arabic, extract_text_from_html

HOT_SEARCH_URL = "https://m.weibo.cn/api/container/getIndex"
HOT_SEARCH_ITEM_SEQ_PREFIX = "https://simg.s.weibo.com/wb_search_img_search"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
    "Cookie": "SUB=_2AkMWJrkXf8NxqwJRmP8SxWjnaY12zwnEieKgekjMJRMxHRl-yj9jqmtbtRB6PaaX-IGp-AjmO6k5cS-OH2X9CayaTzVD",
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


def _get_item_detail(http_session, detail_url):
    try:
        detail_api_url = detail_url.replace('https://m.weibo.cn/search', HOT_SEARCH_URL)
        response = http_session.get(detail_api_url)
        if response.status_code != 200:
            return None
        rsp_data = json.loads(response.text)
        if not rsp_data.get('ok'):
            return {}

        rsp_data = rsp_data.get('data')
        read_count = None
        talk_count = None
        if 'cardlistInfo' in rsp_data and 'cardlist_head_cards' in rsp_data.get('cardlistInfo'):
            card_head = rsp_data.get('cardlistInfo').get('cardlist_head_cards')[0]
            if 'head_data' in card_head:
                midtext = card_head.get('head_data').get('midtext').strip()
                read_text, talk_text = [item for item in midtext.split(' ') if '阅读量' in item or '讨论量' in item]
                read_count = convert_chinese_to_arabic(read_text.replace('阅读量', ''))
                talk_count = convert_chinese_to_arabic(talk_text.replace('讨论量', ''))

        talk_texts = []
        for card_item in rsp_data.get('cards')[:5]:
            try:
                if 'mblog' in card_item:
                    card_text = card_item.get('mblog').get('text')
                    card_text = extract_text_from_html(card_text)
                    talk_texts.append(card_text)
            except:
                traceback.print_exc()
        return {'view_count': read_count, 'talk_count': talk_count, 'summary': '\n'.join(talk_texts)}
    except:
        traceback.print_exc()
        return {}


class Weibo:

    @staticmethod
    def get_hot_search():
        """
        微博热搜
        """
        try:
            rsp_text = None
            with request_session() as s:
                payload = {
                    "containerid": "106003type%3D25%26t%3D3%26disable_hot%3D1%26filter_type%3Drealtimehot",
                    "extparam": "filter_type%3Drealtimehot%26mi_cid%3D100103%26pos%3D0_0%26c_type%3D30%26display_time%3D1550505541",
                    "luicode": "10000011",
                    "lfid": "231583",
                }
                response = s.get(HOT_SEARCH_URL, params=payload)
                if response.status_code != 200:
                    logger.error(f'weibo: get hot search failed! code:{response.status_code}, text:{response.text}')
                    return None, response
                rsp_text = response.text
                hot_search_data = json.loads(rsp_text)
                if hot_search_data.get("ok", 0):
                    cards = hot_search_data["data"]["cards"]
                    if cards:
                        crawl_time = int(time.time())
                        hot_items_group = cards[0]["card_group"]
                        item_list = []
                        for item_topic in hot_items_group:
                            if not HOT_SEARCH_ITEM_SEQ_PREFIX in item_topic.get("pic", ""):
                                continue
                            item_data = {
                                'title': item_topic.get("desc", ""),
                                'url': item_topic.get("scheme", ""),
                                'flag': _get_item_flag(item_topic.get("icon", "")),
                                'hot_value': _get_item_hot_value(item_topic.get("desc_extr", ""))[0],
                                'flag_ext':  _get_item_hot_value(item_topic.get("desc_extr", ""))[1],
                                'extra': item_topic.get("desc_extr", ""),
                                'crawl_time': crawl_time
                            }
                            item_data.update(_get_item_detail(s, item_topic.get("scheme", "")))
                            item_list.append(item_data)
                            logger.info(f"get hot search item:{item_data.get('title')} ")
                        return item_list, response
                return None, response
        except:
            logger.exception(f'weibo: get hot search failed! rsp_text:{rsp_text}')
            return None, None


if __name__ == "__main__":
    items, text = Weibo.get_hot_search()
    if items:
        for item in items:
            logger.info('item:%s', item)