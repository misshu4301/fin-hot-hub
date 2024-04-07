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
    'Cookie': 'cookiesu=851711269429979; device_id=e97d164930dd3d78d0e7743613c02e2e; acw_tc=2760827c17124781934634255ecfa66b5372fd924cd2b661efb4fc33134a4b; xq_a_token=4b8bc7136c9fd7b4395f9ca0a65c38363243df2b; xqat=4b8bc7136c9fd7b4395f9ca0a65c38363243df2b; xq_r_token=3f230866347670b258c76aecd81456e63e6aa98b; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOi0xLCJpc3MiOiJ1YyIsImV4cCI6MTcxNDk1NjQ2MiwiY3RtIjoxNzEyNDc4MTkwODc3LCJjaWQiOiJkOWQwbjRBWnVwIn0.MKVDytvAHaSzt4fqxcbRr_vzKJfJ4UQ68i6ED_xRV1Vf_DQ2uitpib5YZsizcdjlqS4Ul0xdQfXvVT21qGcsXQinUtFtHluWQBBHVxfFn_C62F7r557WeX3qbg0I-mHX6ocs8Fumek3QGjs9rzLYcpftEe6EpD1A7JSv97AZwPjb4bXYxEt4mAw0geKuIEz0xwdlcSxfg7v_BPTBEx8ogJDCyEfd8QZHrRPTJh8Wd8ApUxmBCd4H7C0I4tMOL_1cirSSUin1-SDVp_BG7g-yx-mYy8N0sWoltTD7k3U8y3ZZO2Macrs2mDYEl0-7GtW9DU8ymSiUoKmufgwT9VFr1A; u=851711269429979; Hm_lvt_1db88642e346389874251b5a1eded6e3=1711269433,1712478194; smidV2=20240407162313dfce9c8a61a64a0c45e557b8ead655ee00802b9f8aadc31b0; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1712478670; .thumbcache_f24b8bbe5a5934237bbc0eda20c1b6e7=jmtQilmj9oZmU7BHV2jKK6snYw/z2J+UT/qX5n0z89GT+w00h0tBleAKCJLEnSYyILdrXgwU/bj1uFoTsG5iGQ%3D%3D',
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
