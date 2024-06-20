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
    'Cookie': 'cookiesu=491711545514312; u=491711545514312; s=al12hlsv19; smidV2=20240327211835e331676f9e8800153b9491951b7341e40039407a6841a0430; device_id=32ac1147010a71d6a681b82332222f4d; Hm_lvt_1db88642e346389874251b5a1eded6e3=1717575348; acw_tc=2760828017188713349697401e0e904c8e2b171363f7c3a8730c5f03fff83b; xq_a_token=483932c5fb313ca4c93e7165a31f179fb71e1804; xqat=483932c5fb313ca4c93e7165a31f179fb71e1804; xq_r_token=f3a274495a9b8053787677ff7ed85d1639c6e3e0; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOi0xLCJpc3MiOiJ1YyIsImV4cCI6MTcyMTQzNjcyOSwiY3RtIjoxNzE4ODcxMzE4OTYxLCJjaWQiOiJkOWQwbjRBWnVwIn0.JF2CBVsmbw_rRWE8MMogxUdhWLZpznF49Ekortt8Sm61gdKetkz05MXGaq49trCc8e6-ryQr3WyKd0cWRVPS6qlzjAp59z3qcVZBHm38TqyqX2lJnJRpODnAjzhJmip9YgjxuoGic_ahgDJmUwdrayBufA5f_slDzQtdoxnEhueBFR_i-sFoAwFaGdc9YO6C7IgaO-zr4fAMhWPvkJwmzn4hZdzjsi4ASsGHTpJNvvoH-coMpJsBDeMjAGtpS0Hk9cHxT7j6Ewpp-GsOi3AfYRN5PSZxoCw4tc4LFcSPDsipNJldf6nOMhCiA9O7mScB1gzT-zFUzA45QCOhdtuJkQ; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1718871335; .thumbcache_f24b8bbe5a5934237bbc0eda20c1b6e7=ENL8M+sX4uZ5bLVXJ0idhm21+IHhFdt9a2f6z25UNylZ96INsgn1PPoQslTaJIL00KMCzrWl7iRKJfMZ1m7pXQ%3D%3D',
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
