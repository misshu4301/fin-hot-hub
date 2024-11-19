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
    'Cookie': 'cookiesu=131730285358049; u=131730285358049; Hm_lvt_1db88642e346389874251b5a1eded6e3=1730285359; HMACCOUNT=AE67484C6C7D6122; device_id=f209dddad001c71ee26c2dc5056fad28; smidV2=20241030184918150478ff3c10586f6965acf16b8b82b40090efec1f867d250; s=bf1aqgon8g; .thumbcache_f24b8bbe5a5934237bbc0eda20c1b6e7=hgGcMsreFwQBIx0Z3kFWQQYky0+q82L9Nw1pECJOAH/qTE5Km9MuCNH2/g4kKmvVB8daK1u4MoxdizWfSbJYtQ%3D%3D; acw_tc=2760827f17320097484115368e27f47ba3f6c0473122f2ef243d5ece7961d1; xq_a_token=691d6f0a678b98a172affb89759b9c46fd23b4e2; xqat=691d6f0a678b98a172affb89759b9c46fd23b4e2; xq_r_token=de180625dcdde2e538953eb202d55300cae40fe1; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOi0xLCJpc3MiOiJ1YyIsImV4cCI6MTczNDM5Njg3MiwiY3RtIjoxNzMyMDA5NzM3NjU2LCJjaWQiOiJkOWQwbjRBWnVwIn0.h7o_tryWfMDQIIzvQ4PvcGnoxqCLXe9XQaHmgQ3EQHhVS_ObFPuoIln4o0IUVAjyEyce3reLoUeMOIJFxwD3XoIdnHo30lT6G1k_G8NbUN5_aCgSQH08vgXErCBBo4uUpFYA6KkG97QDZbHwBOp9KlSJvmuLuQI0JWpd1jKHDOen4pxHWM4Kv8avKCdqy8NewYcl85DE3g7eYO5g6jD-_5qni9xUzSV9zkqXdJ0Ptf162zm-X9lXMeejef9KxGiZrL8cMNA1h-URxKsDf7qfQ_z-xqWcnFlFNThSf2AtTRU0-AIIf9NhDtHA350OMsB9wWgG_hUeV-5eNw88iZ8Deg; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1732009754; ssxmod_itna=Yq+xyD9DnQDQWqmq0Lx0pI1QNGOCbKDceotjr0x05hBeGzDAxn40iDt==LDGTTawx+8Ybmfh1InobqalWAicRINw9lyKD=xYQDwxYoDUxGtDpxG=tVDen=D5xGoDPxDeDAjKDCgNHKDdncFCcpaOw6cOnxGWpPKDmaKDRooDSeBzZrHFqi5DiPoDXxYDaPKDupHO1xi8D79fpgY1D7pmIU3Ahxi3fBKAG40OO3FHFCvzlaIU3cW5VGPNTCP5e0TeKQGNrAGbl0q4YiG4HTr3V7zvNuhDD===; ssxmod_itna2=Yq+xyD9DnQDQWqmq0Lx0pI1QNGOCbKDceotjrDnF8qDsEDwg4jKG7=4D',
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
