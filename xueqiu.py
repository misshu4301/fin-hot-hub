import contextlib
import json

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from util import logger

HOT_TOPIC_SEARCH_URL = 'https://xueqiu.com/query/v1/hot_event/tag.json'

HEADERS = {
    'Origin': 'https://xueqiu.com',
    'Referer': 'https://xueqiu.com/hot/spot',
    'Cookie': 'acw_tc=2760779917112687234676591e0a3636bfd0f9fef3806a6cfc9ea4e1b42e4a; xq_a_token=01b99d82fffd2faf8b614e98a00cbb35d6c7ddcf; xqat=01b99d82fffd2faf8b614e98a00cbb35d6c7ddcf; xq_r_token=7fe9b3213c399b15eee3c5bca4841433a03128a6; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOi0xLCJpc3MiOiJ1YyIsImV4cCI6MTcxMzY2MDQyOCwiY3RtIjoxNzExMjY4NzAwOTc5LCJjaWQiOiJkOWQwbjRBWnVwIn0.Iyjplh7irRp0fLlCGpjt5sTsV2rg3ZbHrS0CCzBVR53_tR8ckZ6nV_29EQTNmZBRH-jrdq9Sc1Xxq6JOjOt4yHC8ywNr8Fi8svIFflOzlK8WBRnfEGZbFkpdZ5caaRTQ6VhjpQDemRTmnw51JJTsXf0Njor0z62aFbvZHZFuLNLOCdHVWKEZri_8bYeo0GfHhoX0rU50YOufDTYzxqS7ATXuYRlBz0VwBoynjUz54mNMaF6MfCWHShe_IFkKHsnGm0STy7Jb72oo--nK6gOtunIYXIwQ3WCeZIBMDs_2tphQbYv6Tm55eyRTm7-egm32gsuBcc8xEvh9m_2lQwNTDg; cookiesu=141711268723501; u=141711268723501; device_id=32ac1147010a71d6a681b82332222f4d; Hm_lvt_1db88642e346389874251b5a1eded6e3=1711268727; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1711268727',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36'
}

QUERIES = {
    'since_id': -1,
    'size': 10
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


class XueQiu:

    @staticmethod
    def get_hot_topic():
        try:
            with request_session() as session:
                response = session.get(HOT_TOPIC_SEARCH_URL, params=QUERIES)
                if response.status_code != 200:
                    logger.error(f'get hot topic failed! code:{response.status_code}, text:{response.text}')
                    return None, response
                raw_data = json.loads(response.text)
                if 'success' in raw_data and raw_data.get('success'):
                    topic_list = raw_data.get('data')
                    item_list = [
                        {'title': item_topic.get("title"), 'url': item_topic.get("url")}
                        for item_topic in topic_list]
                    return item_list, response
                return None, response
        except:
            logger.exception('get hot topic failed')
            return None, None


if __name__ == "__main__":

    items, text = XueQiu.get_hot_topic()
    if items:
        for item in items:
            logger.info('item:%s', item)
