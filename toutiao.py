import contextlib
import json

import requests
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import quote

from util import logger

HOT_SEARCH_URL = 'https://api.toutiaoapi.com/api/feed/hotboard_light/v1/'
HOT_DETAIL_URL = 'https://api.toutiaoapi.com/api/trending/topic/{0}/?rank=1'

QUERIES = {
    'category': 'hotboard_light',
    'aid': '13',
    'client_extra_params': '{"hot_board_source":"news_hot_external_h5","penetrate_data":{"hotboard_use_snapshot":true,"interestboard_use_snapshot":true}}'
}

HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Referer': 'https://api.toutiaoapi.com/feoffline/hotspot_and_local/html/hot_list_new/index.html',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
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


def _get_item_flag(label_type):
    # hot/new/participant
    if label_type == 'hot':
        return '热'
    if label_type == 'new':
        return '新'
    return ''


def _get_read_data(http_session, id_str, hot_read_cache):
    try:
        if id_str in hot_read_cache:
            return hot_read_cache.get(id_str)
        detail_url = HOT_DETAIL_URL.format(id_str)
        response = http_session.get(detail_url)
        if response.status_code != 200:
            return None, None
        rsp_data = json.loads(response.text)
        read_data = rsp_data.get('read_count', None), rsp_data.get('talk_count', None)
        hot_read_cache[id_str] = read_data
        return read_data
    except:
        return None, None


class Toutiao:
    board_category_list = ["normal", "health", "technology", "finance", "car", "international", "basketball", "football"]
    # 旅游:tourism、股市榜:stock、篮球榜:basketball、足球榜:football、游戏榜:game

    @staticmethod
    def get_hot_search():
        try:
            with request_session() as session:
                response = session.get(HOT_SEARCH_URL, params=QUERIES)
                if response.status_code != 200:
                    logger.error(f'get hot board failed! code:{response.status_code}, text:{response.text}')
                    return None, response
                rsp_data = json.loads(response.text)
                hot_map = {}
                read_data_cache = {}
                if 'message' in rsp_data and rsp_data.get('message') == 'success':
                    hot_list = rsp_data.get('data')
                    crawl_time = int(time.time())
                    for hot_item in hot_list:
                        content_data = json.loads(hot_item.get('content'))
                        if "raw_data" not in content_data:
                            continue
                        raw_data = content_data.get("raw_data")
                        if "board" not in raw_data:
                            continue
                        board_data = raw_data.get("board")[0]
                        board_category = board_data.get("category")
                        if board_category not in Toutiao.board_category_list:
                            continue
                        if "hot_board_items" not in board_data:
                            continue
                        hot_board_items = board_data.get("hot_board_items")
                        item_list = []
                        for board_item in hot_board_items:
                            item = {'title': board_item.get("title"),
                                    'url': board_item.get("url"),
                                    'flag': _get_item_flag(board_item.get("title_label_type", "")),
                                    'flag_ext': board_item.get("title_label_type", ""),
                                    'extra': board_item.get("title_label_desc", ""),
                                    'crawl_time': crawl_time
                                    }
                            read_data, talk_count = _get_read_data(session, board_item.get("id_str", ""),
                                                                   read_data_cache)
                            if read_data:
                                item['view_count'] = read_data
                            if talk_count:
                                item['talk_count'] = talk_count
                            item_list.append(item)
                        hot_map[board_category] = item_list
                    return hot_map, response
                return None, response
        except Exception as ex:
            logger.exception(f'toutiao get hot search failed!{ex}')
            return None, None


if __name__ == "__main__":
    items, text = Toutiao.get_hot_search()
    print(json.dumps(items))
