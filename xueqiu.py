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
    'Cookie': 'cookiesu=491711545514312; u=491711545514312; s=al12hlsv19; smidV2=20240327211835e331676f9e8800153b9491951b7341e40039407a6841a0430; device_id=32ac1147010a71d6a681b82332222f4d; xq_a_token=0518d12486f7876b2f98097d9ec9214afa97c2a0; xqat=0518d12486f7876b2f98097d9ec9214afa97c2a0; xq_r_token=fc7d679707be09bbf6da361632fe9a5facb99f94; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOi0xLCJpc3MiOiJ1YyIsImV4cCI6MTcyMDE0MDcyMCwiY3RtIjoxNzE3NTc1MzIwNTI4LCJjaWQiOiJkOWQwbjRBWnVwIn0.ps8_Nz0eAAY1t0u8Z-_w1zv1_gCDQO-8JEgki1ntnCpX4XP5Rup2l-1MLqf8VDClr4uPaTj-QTpF8bsnlLsHGW-mw-NaXW55hICAUBYF0tW4gxiXWBbLvo1RPR3niCR3UcIate3-g31v4oSFoL7T8mUYic3DbubxqM7yXVsDgz_hZ_kyseSsS4aXZqlWmExnds3176UDDwmWMAjRWqxLZi01rDnQWrDhxwm48kgPp1VjEc7lAiKW5kFetBhYm0O9hBysRBQwhPepsjV9x_TaSAWQNYuR4nIrtSRe2DYK18Hlg-mGOBfJxs8mQv3t7Jb6rzYoaiw05dussU55_3sctg; Hm_lvt_1db88642e346389874251b5a1eded6e3=1717575348; acw_tc=276077a417176522631021056e2556edfdecfc25f18bdbcf0928d4c47b200f; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1717652264; .thumbcache_f24b8bbe5a5934237bbc0eda20c1b6e7=Lv+nG9Uf16OVyzcNIvK5j28eGSiOgVJoZ3eBSdyAomks0/l5nAP8SkCgTQUgZjni/g+onKg0nLbqdRvgjj028A%3D%3D',
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
