# -*- coding: utf-8 -*-
import contextlib
import json
import logging
import re
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from util import convert_chinese_to_arabic

HOME_URL = "https://www.kuaishou.com/?isHome=1"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
}

RETRIES = Retry(
    total=3, backoff_factor=1, status_forcelist=[k for k in range(400, 600)]
)


@contextlib.contextmanager
def request_session():
    s = requests.session()
    try:
        s.headers.update(HEADERS)
        s.mount("http://", HTTPAdapter(max_retries=RETRIES))
        s.mount("https://", HTTPAdapter(max_retries=RETRIES))
        yield s
    finally:
        s.close()


class KuaiShou:
    @staticmethod
    def get_hot_search():
        try:
            with request_session() as s:
                resp = s.get(HOME_URL)
                content = resp.text
                regex = r"window.__APOLLO_STATE__=(.*);\(function\(\)"
                result = re.search(regex, content, re.DOTALL)
                if result:
                    raw_data = json.loads(result.group(1))["defaultClient"]
                    print(result.group(1))
                    ret = []
                    for item in raw_data['$ROOT_QUERY.visionHotRank({"page":"home"})']["items"]:
                        tag_type = raw_data[item["id"]]["tagType"]
                        if tag_type == '置顶':
                            continue
                        view_count = raw_data[item["id"]]["viewCount"]  ## null
                        hot_value = raw_data[item["id"]]["hotValue"]  ## 1154.7万
                        image = raw_data[item["id"]]["poster"]
                        _id = re.search(r"clientCacheKey=([A-Za-z0-9]+)", image).group(1)
                        ret.append(
                            {
                                "title": raw_data[item["id"]]["name"],
                                "url": f"https://www.kuaishou.com/short-video/{_id}",
                                'hot_value': convert_chinese_to_arabic(hot_value),
                                'view_count': view_count,
                                'flag': tag_type
                            }
                        )
                    return ret, None
                return None, None
        except:
            logging.exception("KuaiShou get data failed")
            return None, None


if __name__ == "__main__":
    print(json.dumps(KuaiShou.get_hot_search()[0]))
