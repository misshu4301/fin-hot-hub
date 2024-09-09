# -*- coding: utf-8 -*-
import contextlib
import json
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from util import logger

# 36kr热榜
# https://www.36kr.com/hot-list/renqi/2024-09-09/1
HOT_LIST_URL = "https://gateway.36kr.com/api/mis/nav/home/nav/rank/hot"
HOT_DETAIL_URL = "https://www.36kr.com/p/{0}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
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


class WebSite36Kr:

    @staticmethod
    def get_hot_list():
        try:
            payload = {
                "partner_id": "wap",
                "param": {"siteId": 1, "platformId": 2},
                "timestamp": int(time.time()),
            }
            with request_session() as s:
                response = s.post(HOT_LIST_URL, json=payload)
                if response.status_code != 200:
                    logger.error(f'get hot board failed! code:{response.status_code}, text:{response.text}')
                    return None, response
                raw_data = json.loads(response.text)
                if 'code' in raw_data and raw_data.get('code') == 0:
                    hot_list = raw_data.get('data').get('hotRankList')
                    item_list = [
                        {'title': item_topic.get('templateMaterial').get("widgetTitle"),
                         'url': HOT_DETAIL_URL.format(item_topic.get('itemId'))}
                        for item_topic in hot_list]
                    return item_list, response
                return None, response
        except Exception as ex:
            logger.exception(f'36kr get hot list failed!{ex}')
            return None, None


if __name__ == "__main__":
    items, text = WebSite36Kr.get_hot_list()
    print(json.dumps(items, ensure_ascii=False))
