import contextlib
import json

import requests
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from util import logger, convert_chinese_to_arabic

HOT_TOPIC_SEARCH_URL = 'https://xueqiu.com/query/v1/hot_event/tag.json'

HEADERS = {
    'Origin': 'https://xueqiu.com',
    'Referer': 'https://xueqiu.com/hot/spot',
    'Cookie': 'acw_tc=1a0c640317285636867533945e00a49ad41ad29417ae7055d0520784420b4c; xq_a_token=dbc1dc6d13bd101dd06f18c5b7f2fb2eb276fb5a; xqat=dbc1dc6d13bd101dd06f18c5b7f2fb2eb276fb5a; xq_r_token=8009cc86908134cef1e05f27b0fbea84bea0abb7; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOi0xLCJpc3MiOiJ1YyIsImV4cCI6MTczMDUwODgwMCwiY3RtIjoxNzI4NTYzNjYwNDUxLCJjaWQiOiJkOWQwbjRBWnVwIn0.kPXxnXqaJr854tVpBodJ8WSszDOQmPWiapX1-JiYPZinLIBEDmXSImwfKI01JibDcVdEcLMFi04-4xvOb_zZTLPWBpUu9AExUKTL-3CVaOxAG5nTUUdKG2TZKfZBsvutz7Dh0fsp2p0Xk7uvnC4DO2pIl2cvcYl8Y5Pi-2NhSaJdvAC96g1jJFwHRBPTR0TF63Nv1VOUeBPTna1FJiFqs65RiYAYmgIS06i2otnPxH-F8MFi0FmI6XLULN4Kkf2e7PEI76US_2Qgopf-dtD4whLPWO6ogEnA_JRiJoQUw6QUATskQvXjWvP9HIcwMCZBhKotSGKee_J05Nx2NySeSg; cookiesu=301728563686761; u=301728563686761; device_id=72745116fbdb5a21441a2724959c5eed; Hm_lvt_1db88642e346389874251b5a1eded6e3=1728563688; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1728563688; HMACCOUNT=71B7DD8ECAE5CBBE; smidV2=20241010203448759077d04661c983487e882fd960745a009331318b32565d0; .thumbcache_f24b8bbe5a5934237bbc0eda20c1b6e7=N2i0sITkGKmibPZXefu0UTbtQViaOqBy5AF3J6Fvukh0CQaHnulso3RTl3pqX+7c1533I0i8TpBZgefrsj38vw%3D%3D; ssxmod_itna=eqIxcDgieCuDnGDzxmxB4DKdat7WDCQDjh7eOG3ELqGXxqoDZDiqAPGhDCbR/xeTPQf070idq7YYhD4Q6DZBrLINwtZOitD84i7DKqibDCqD1D3qDk144YY1Dt4DTD34DYDiE=DB9v/QDj7yku1yFvaFHEO5Db197Di9ODY5pDAuGZZv1krh1DDcmDlIGDWc7DQyzvZPDExGO6zKm9xGaW+8L+tKDEn4C+33Dv6oOsOrzlgyOlRnTeemFGYrF1QDYYlxiYlDTGDRYwDr9TQDcjG2vryhDD==; ssxmod_itna2=eqIxcDgieCuDnGDzxmxB4DKdat7WDCQDjh7eOG3EqA=FQD/7xKdK7=D20eD=',
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
                    crawl_time = int(time.time())
                    item_list = [{
                        'title': item_topic.get("title"),
                        'url': item_topic.get("url"),
                        'crawl_time': crawl_time,
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
