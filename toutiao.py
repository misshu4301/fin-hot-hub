import contextlib
import json

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import quote

from util import logger

HOT_SEARCH_URL = 'https://api.toutiaoapi.com/api/feed/hotboard_light/v1/'
HOT_DETAIL_URL = 'https://www.xiaohongshu.com/search_result?keyword={0}&type=51'

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


class Toutiao:

    board_category_list = ["normal", "health", "technology", "finance", "international"]

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
                if 'message' in rsp_data and rsp_data.get('message') == 'success':
                    hot_list = rsp_data.get('data')
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
                        item_list = [{'title': board_item.get("title"), 'url': board_item.get("url")} for board_item in hot_board_items]
                        hot_map[board_category] = item_list
                    return hot_map, response
                return None, response
        except:
            logger.exception('get hot search failed')
            return None, None


if __name__ == "__main__":
    items, text = Toutiao.get_hot_search()
    print(json.dumps(items))