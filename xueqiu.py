import contextlib
import json

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from util import logger, convert_chinese_to_arabic

HOT_TOPIC_SEARCH_URL = 'https://xueqiu.com/query/v1/hot_event/tag.json'

HEADERS = {
    'Origin': 'https://xueqiu.com',
    'Referer': 'https://xueqiu.com/hot/spot',
    'Cookie': 'cookiesu=661721631088076; u=661721631088076; device_id=f209dddad001c71ee26c2dc5056fad28; Hm_lvt_1db88642e346389874251b5a1eded6e3=1721631087; HMACCOUNT=2D32DF7EF328947D; smidV2=2024072214512644f3ddef55efaabee50c2d824a771eae00740c6fc191b7470; acw_tc=2760827f17241314407287656e27fc6fab60a116a7c5d1736d971f48aeee5a; xq_a_token=7747107a16c7844c358ac0bbe44530ab34c16e3d; xqat=7747107a16c7844c358ac0bbe44530ab34c16e3d; xq_r_token=517f2f4c758b1e5786699e0976d627a7ee5cbf5c; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOi0xLCJpc3MiOiJ1YyIsImV4cCI6MTcyNjYyMDc3OSwiY3RtIjoxNzI0MTMxMzkyMDE3LCJjaWQiOiJkOWQwbjRBWnVwIn0.LIKa66RtWeqC4WthyJVNMFJOEPgNnbmEkYLjBV57QcCQGdDcuQt-kL1ZtfJolsBUktvfTyUYmjxT9dVkp9Tuc4YmjMhtS9ReI45DTFo6F21Lj4VKLlgKg2AhBa6kGtidFCxt0yrEED4m7o7QQn8GOsfURgzZ4S8yhZgnTh6u2LBz7kn3holDfy_IRYtyGDOrwGuZ5K6I0Vjq-EPHQHs2fhM-o8yp-Zmn8xniWfWfl-uBk2VvxPtkwB8Pv6tQcsLbpIXLj0lGJi4Qu5NMTk0ddjAlxHQq-y6GQPbGhaYVZ34iGz8q8l1tqzlu1qdcxKLd9V6zwPHqptmg86d0yYZYSg; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1724131442; .thumbcache_f24b8bbe5a5934237bbc0eda20c1b6e7=MIs9j6gI5ZMCqwkUZa5knr/rjXCXdn5PY8cTH4XJ9ilA0uV5v2IW5ycc2g+KbeiVrMx0I6k7wFUJ5nnqKbpSag%3D%3D; ssxmod_itna=iq0xuDg70=Q4zxmxB4DIOlx+OP58q6hxe4X6=D/nDfgxiNDnD8x7YDvzIdfmf+7ahPLWx=jxrm3Lfi7EI3Djxr3PqbxCPd=ORDAoDhx7QDox0=DnxAQDj6E5GGUxBYDQxAYDGDDPBDGuN9WqDFRTtMnudciqQ9RqDEWuQDYT=DmMbDn2iDPQNX+YNDGRbDzLiDfRQDIuNceqGnD0Q7akRlD0fdHP9b=qGWbOUbdPGullQ2IGXV4W6spBfTSo44zGYinGDeKA4q+8G=nKhtC+ks+iEt7hDHnBhzzX4rMozxD=; ssxmod_itna2=iq0xuDg70=Q4zxmxB4DIOlx+OP58q6hxe4X=G9iLDBqP7jFGcDeLbD==',
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


def _convert_text_to_number(text):
    text = text.replace('阅读', '')
    return convert_chinese_to_arabic(text)


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
                    item_list = [{
                        'title': item_topic.get("title"),
                        'url': item_topic.get("url"),
                        'view_count': _convert_text_to_number(item_topic.get('reason'))
                    } for item_topic in topic_list]
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
