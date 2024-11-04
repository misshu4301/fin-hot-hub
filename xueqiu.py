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
    'Cookie': 'cookiesu=131730285358049; u=131730285358049; Hm_lvt_1db88642e346389874251b5a1eded6e3=1730285359; HMACCOUNT=AE67484C6C7D6122; device_id=f209dddad001c71ee26c2dc5056fad28; smidV2=20241030184918150478ff3c10586f6965acf16b8b82b40090efec1f867d250; acw_tc=ac11000117307086886412498e00d6a59dcb0d26de66511193434385520dbe; xq_a_token=7716f523735d1e47a3dd5ec748923068ab8198a8; xqat=7716f523735d1e47a3dd5ec748923068ab8198a8; xq_r_token=0483ea3986e45954e03c9294444a1af14d7579d3; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOi0xLCJpc3MiOiJ1YyIsImV4cCI6MTczMzEwMDgxNywiY3RtIjoxNzMwNzA4NjYwNzEwLCJjaWQiOiJkOWQwbjRBWnVwIn0.KdcdeUyTU1R9PJ4G6HsZo5-ldpRgnHIpWkjOz7NhIF0W7IDk274vCYflLWwZTbSTRmPlgOhqqojcjHquhjYjzZrbOBr298ZoOleCXeE4lZyH_anp1eYjGWrVKsnmnp4tFSCqCwtZuDymF0JEoz4V305TWllEov2NYtAdTsB20mkHhR6vK-nTyJfHQJ90RZqTftD7zghntwC9FEJPM6BjftdxA4ROOW_sre53z5zkf-1pEr97MxhzWSts5sulngoh_wQ7FqhgOfBE54J-5e75DqWtyLfWDbeEm57xTZDzynCaGy0RSJGTJosN9uHWBS81cT8G0100bwJ_OfWFJYVTQQ; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1730708690; .thumbcache_f24b8bbe5a5934237bbc0eda20c1b6e7=Xpctrguc4ya/Sue8iHVtx/wl1bTU+7bxxGI/bt4UDoyeclKk/9839WEhbvdUwyE33aHOpZlZoBcZGf5o6t3/rw%3D%3D; ssxmod_itna=YqAxci0=e7qDqhDl8DC2a5biQo0QtotDB0Dmq7b455DskKbDSxGKidDqxBmm=2Aq3tK70hxq63Sr+5Tt8=3bLINwbAcuG8DneG0DQKGmDBKDSDWKD9BeeiiSDCeDIDWeDiDGbkD06NZOD72UyIMU6tLjUbutDmSj2DGjuDit3xivxMMNM98DMDDfoxB=xxAf2D7UZtMdDbqDu8ZQY6qDLAecFP1QDbEPBeaWDtkTR/f+lBuXuBpEvDr46Ko8jB7wrQohxDRmol7mb77q4R9eF48wAVQYnPD=; ssxmod_itna2=YqAxci0=e7qDqhDl8DC2a5biQo0QtotDB0Dmq7b45ikjtDl24QFQ08D+gYD=',
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
