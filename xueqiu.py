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
    'Cookie': 'cookiesu=131730285358049; u=131730285358049; HMACCOUNT=AE67484C6C7D6122; device_id=f209dddad001c71ee26c2dc5056fad28; smidV2=20241030184918150478ff3c10586f6965acf16b8b82b40090efec1f867d250; s=bf1aqgon8g; .thumbcache_f24b8bbe5a5934237bbc0eda20c1b6e7=hgGcMsreFwQBIx0Z3kFWQQYky0+q82L9Nw1pECJOAH/qTE5Km9MuCNH2/g4kKmvVB8daK1u4MoxdizWfSbJYtQ%3D%3D; acw_tc=2760827217334017547678562e7196d3b53b9ac7fc0651dcaf25c18d6f3186; xq_a_token=220b0abef0fac476d076c9f7a3938b7edac35f48; xqat=220b0abef0fac476d076c9f7a3938b7edac35f48; xq_r_token=a57f65f14670a8897031b7c4f10ea42a50894850; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOi0xLCJpc3MiOiJ1YyIsImV4cCI6MTczNTY5Mjg4OSwiY3RtIjoxNzMzNDAxNzE4MjY1LCJjaWQiOiJkOWQwbjRBWnVwIn0.Ea9_lwhX9_3ryVyNL4nDLFSAZ6q_TvR0h8Mg1I6ufcZ6NH2wvHa1gFFum5TMYt1NGtyYrmEMWoKtixjhhyKeeGlcfQ5ihWCZiYdR87Xf02p4WDc7TBEc5T6xuymhPSj1jvKPbrmanhnNtBn-xZEE9KwRNMVgCBebMYk1NeCz4MsHXSdmV6v9HTYP9jJ2HyZz5lqwZho5zOijMlIdM_CcZgyd40ELWk2ZtSFdURZWCIrkmsX95Cg7D50UyGuB2UNtBq4GgvUGjMpDCHNJWxONcOFs7FpV3WYndU2e2wa8W3QnEwOoYx9B42m6mH3uouHXxBK0Te71EhWfERgHvQSAKw; Hm_lvt_1db88642e346389874251b5a1eded6e3=; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1733401756; ssxmod_itna=eq0xRDyDg7i=G=NGHKGdD7fKgDxI2qGILU5w5bttD/K8mDnqD=GFDK40ooSi+dfdtUnA2fKHl0E2DqLWC0YhxL/QcqhaV9DAoDhx7QDox0=DnxAQDj2g5GG0xBYDQxAYDGDDp9DGksSuD0+1X=y1k1FO1pI1DYcOwxDOvxGCW4Gtq9ys96px9xDWT40k44iawx0CM19HDmKDIcSOi85DFrof63S7DmR30ofADC9ImZaPg2vsv2LezC23NdhFeYrrqBrx3Q+5Ne458wGx/j6umCxxYYcDsN0nfC2vVluD4D==; ssxmod_itna2=eq0xRDyDg7i=G=NGHKGdD7fKgDxI2qGILU5w5btG9WXDBTP7jHGcDeMbD===',
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
