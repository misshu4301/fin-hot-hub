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
    'Cookie': 'cookiesu=491711545514312; u=491711545514312; s=al12hlsv19; smidV2=20240327211835e331676f9e8800153b9491951b7341e40039407a6841a0430; device_id=32ac1147010a71d6a681b82332222f4d; acw_tc=276077a417205772080257053e0d5e6bc23769b0dacd29967bfc87f1d6ee0d; xq_a_token=64274d77bec17c39d7ef1934b7a3588572463436; xqat=64274d77bec17c39d7ef1934b7a3588572463436; xq_r_token=3f3592acdffbaaee3a7ea110c5d151d2710b7318; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOi0xLCJpc3MiOiJ1YyIsImV4cCI6MTcyMjczMjcyOCwiY3RtIjoxNzIwNTc3MjAzODk1LCJjaWQiOiJkOWQwbjRBWnVwIn0.ALhyW4D4wcaSb9ifNdlHr40gvO0IJcIc8j-CCCPaMvBwepNEbAE_0eO0TWX6hNxRLbkNAUos24nGzqE7LryERjhqpgvSJaJznvODLKRbMq3UKsYzttVHqtCH3C8g7i0xZfuXnjA07CKN44E9TAXKrwpS80qdHHIkvI8p2ji1bWGb40PflMZmr--XK6Qx5za8OX0AhxxswSKlAxFcUaR8NvfJta4Og_GBRNjb9Ic3o12sOyPIo0EiFn6OzWeq6vVH-GjvU4VVNCZGducBPV8PBTPvb4CDvLoWA5efdTczACu9nvHR8MIB0Zu4Jy1oXGIHk0ih1vfzZ1OKterHWkp_5A; Hm_lvt_1db88642e346389874251b5a1eded6e3=; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1720577209; HMACCOUNT=99DABFFA91D82313; .thumbcache_f24b8bbe5a5934237bbc0eda20c1b6e7=tBlKpBx5pRgktgDqLJMJtlX+QyG+F/Bynv8Zgmf+x6aZQYLBHowjFLcu8CLHwSg0AwJ9avKnUnn2zIrwI0ezgQ%3D%3D',
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
