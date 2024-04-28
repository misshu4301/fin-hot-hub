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
    'Cookie': 'cookiesu=491711545514312; u=491711545514312; Hm_lvt_1db88642e346389874251b5a1eded6e3=1711545515; s=al12hlsv19; smidV2=20240327211835e331676f9e8800153b9491951b7341e40039407a6841a0430; device_id=32ac1147010a71d6a681b82332222f4d; acw_tc=2760827d17137893726075241ec6ed0806993ee5791d6585b44d58b7069172; xq_a_token=5eeab96bfda3e05af7b6ef9e4626c2d12040b664; xqat=5eeab96bfda3e05af7b6ef9e4626c2d12040b664; xq_r_token=7548941cfe5a4311622757e10bf21aacf79c4843; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOi0xLCJpc3MiOiJ1YyIsImV4cCI6MTcxNjI1MjY4MCwiY3RtIjoxNzEzNzg5MzU1MzQyLCJjaWQiOiJkOWQwbjRBWnVwIn0.o2STrwz39zk_IHw5sZgam3XXv-h-dS2UHG0PIts-VpfIdwYDHwqRnR46FKiYFgF55zgL-tLgjTdo2f7kQ7u9OlEojTTYTYrNkiWUB75_W-CddwnTjA8Re9fZ0j5AOP-ozE48k3685Zg0-j3KL_R0MQDiroAvfp_V-AYWm1DvyyWUNUAJzpoOs-lsxlRmupjTG5PrzsWv4y3rdclaDz7c7KL9MMyZUnIx8ILYpOjXAc1NC9e6bp4DA0mZKpcGFGpUkUUCFfEWq9_U_bT-ro1yy5rGg2Quury4oeYJwK8Brc4W0YagwElTlNYOWxgHAOgXD84RXMxvuAZ1PG-eBDT-SA; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1713789374; .thumbcache_f24b8bbe5a5934237bbc0eda20c1b6e7=e7hWypQn9MKryfB5EcY7jyZheN4GMJf9mzdmCiG53H/q8Sb1Dfwk7yZvbo+KX6rgv4qlrceGMqUHXL+OKO6cJQ%3D%3D',
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
    try:
        text = text.replace('阅读', '')
        if '万' in text:
            number = float(text[:-1]) * 10000
        elif '千' in text:
            number = float(text[:-1]) * 1000
        else:
            number = float(text)
        return str(int(number))
    except:
        return ""


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
                        'hot_value': _convert_text_to_number(item_topic.get('reason'))
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
