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
    'Cookie': 'acw_tc=1a0c655817302853580416699e0058a2be0e669d58f8b19cbad730f27a67b6; xq_a_token=f84a0b79c9e449cb1003cb36412faa34001a6697; xqat=f84a0b79c9e449cb1003cb36412faa34001a6697; xq_r_token=b24e38a4224932f5c7abd28126e8fc377b42755b; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOi0xLCJpc3MiOiJ1YyIsImV4cCI6MTczMTgwNDgwNiwiY3RtIjoxNzMwMjg1MzI5MDYxLCJjaWQiOiJkOWQwbjRBWnVwIn0.MqGld6hlH0C3zHnJHKuvT2HE5vWpnfFRYePZjuNsUiaLqjihU1YJhMW1cUeI5JLsitXiL8PiV1jWMI2Di9E4-wq-d7zofU4F1cHA5sA_OOK8gMlROuxWiHJxlw45w03l-nWhxdibyoraky6mX5LPSayRGj8RsPBjFLJgp5QWXTLJCU8dOqJny1EbWjK_RyEOdL6iimvmcnXi16KgN8rj3YybPAAyE-dVreVEh3sXDB2YRqHZVsxrpQUqrp9uOfOHLwaJ-aXVv_anAOQurzeGmxIde6oQnldaRvu5qk56tyAXDCqDsl_raPTmb8C-fNM3HINjS49qCZPCkZwf0NzfwQ; cookiesu=131730285358049; u=131730285358049; Hm_lvt_1db88642e346389874251b5a1eded6e3=1730285359; HMACCOUNT=AE67484C6C7D6122; device_id=f209dddad001c71ee26c2dc5056fad28; smidV2=20241030184918150478ff3c10586f6965acf16b8b82b40090efec1f867d250; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1730285366; .thumbcache_f24b8bbe5a5934237bbc0eda20c1b6e7=cavjAuLEBSM1MxxFHzGby+yduoBNl2Rh0fhVZU77M1EStswmDJgfAZgPdJn9TQrTsNHc2oP732OtXdDsCX4IRg%3D%3D; ssxmod_itna=iq+x0DgidYT4z2DU7mj5xCq7KqqGqi=kseD9lphhx05rBqGzDAxn40iDtZWNlOe2TYqh428BI5ki7Gcvxq76jguA=xzxiTD4q07Db4GkDAqiOD7qqiDxpq0rD74irDDxD3LxDH/upx0416PH1Oa97k1K1DYaOhxDOpxGCb4GtxUHsnpPqnxDWr40kD4iahx0CgaFHDmKDI68Otb5DFoEEL487Dm4dUx3ADCFI+cpeyE5spELb=c2q7Z2ujDn4sGiKGm0D3Z25I74xqC=4LiZu14ec4D=; ssxmod_itna2=iq+x0DgidYT4z2DU7mj5xCq7KqqGqi=kseD9lphxn9fxDsLDwxqjKG7K4D==',
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
