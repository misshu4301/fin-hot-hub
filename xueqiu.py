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
    'Cookie': 'cookiesu=661721631088076; u=661721631088076; device_id=f209dddad001c71ee26c2dc5056fad28; Hm_lvt_1db88642e346389874251b5a1eded6e3=1721631087; HMACCOUNT=2D32DF7EF328947D; smidV2=2024072214512644f3ddef55efaabee50c2d824a771eae00740c6fc191b7470; acw_tc=2760826617229082845907947e719ae60a764c6034255dd7b97ec871b1f713; xq_a_token=fb0f503ef881090db449e976c330f1f2d626c371; xqat=fb0f503ef881090db449e976c330f1f2d626c371; xq_r_token=967c806e113fbcb1e314d5ef2dc20f1dd8e66be3; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOi0xLCJpc3MiOiJ1YyIsImV4cCI6MTcyNTMyNDc3NSwiY3RtIjoxNzIyOTA4MjQzODM4LCJjaWQiOiJkOWQwbjRBWnVwIn0.CaAwA8wfd4F7Y1UZ32nRgd-wI9Gugsv3CnVIAb4ZnBmlbGC-N2J_OPiNVY9Z6dwke5s36o9m1LWx5jTPPpi4MX3KJvQHiIvYoah0W_V6-Xc5RA2i3eYaNYa68aPGY07rl8BU3a1RF_v7gUaxlYp7wgZjoVJAFOlhzAntDkF6kZhNFrYJbs7IRBeLlodDfyEHqkQUASB7R3b7m6V1QOXz5QiHFvmQL8_crTgwsytgfkNS6iG7x9GBJBzKCjfmzKY29Rsf-68jqQo7x4qU5Z38y10liBfDzCv5wcqW9eE1MGuEpci5Zksj7lCfD9VE9U5TPGtZZcJAFFXVBXLdO_gGmg; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1722908292; .thumbcache_f24b8bbe5a5934237bbc0eda20c1b6e7=tX0ynMgnLJvTBgg4XpcT1+x0KF89gk9m7rNhbJGUabNBsFmfX9vkXc9AorosgREpWVv8dXv4D7bep6AvGEq5Mg%3D%3D; ssxmod_itna=YqRx9DBDyD0DclWDXKDH7cheew8W7i3iDAx7KKttD/9CmDnqD=GFDK40oo8bmnxKqGB023YImC+234IKjboTvLF/T4GIDeKG2DmeDyDi5GRD0KvWD445GwD0eG+DD4DWbqDUMp5qGPgLskULKdjj3TtDm8jXDGj2DitYxivVRkNgU8DgDDf5xB=VDAfXD7UMKkdDbqDub1QKpqDLGmnWZldDbOP9lnTDtMb09f+S0TX20a4WFxPo/xxvE+w=iGDNlhDbWKxeQ0G=Y284Wop=CzuW3HD=; ssxmod_itna2=YqRx9DBDyD0DclWDXKDH7cheew8W7i3iDAx7KKtG9WODBTP7jHGcDewrD===',
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
