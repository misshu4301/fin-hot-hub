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
    'Cookie': 'cookiesu=241754301107530; device_id=c0eb5c1f701fdf57d6ba35636609f6cc; xq_a_token=089d79f06ee92d795d3698468670a5d9dbadf407; xqat=089d79f06ee92d795d3698468670a5d9dbadf407; xq_r_token=33c99b4c5478c77154f46091eb752528dea18955; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOi0xLCJpc3MiOiJ1YyIsImV4cCI6MTc2NTUwMjE0MSwiY3RtIjoxNzYzOTYxMjQ3OTAwLCJjaWQiOiJkOWQwbjRBWnVwIn0.gFiBtsl1ed5zrBdQduFFSYP23ODHSvPHCTBMAk1yvEtZhe3ixTQvJz_8OOUPoZqiXTD9C0Lk7dMVGe-fC4u6xmWoO_g7IjIbbnox8kglvhvOBhHCoAt_ivNMpIktLpSwZoFfsLPmmCnJs1SC7g74pJLVaOie32EvILlYXY7ccSGlF6i93BC5ilX3gjPwaenr_CPdqi_alBK5hBu_9aM9EM5z1-C7SJr7VOBYh5NhczHKKr-8eMVGKRSubt5I-z0CQvk9iU8cAwJhbmllNMZa2skMgZSWHAyzMT0dLTr3KUeJ-qq8pJU22nTAECirSm9bn4QVkW1YZ-VwaW0eq-Z7rQ; u=241754301107530; Hm_lvt_1db88642e346389874251b5a1eded6e3=1763961299; HMACCOUNT=BCDECB157B43BC87; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1763980165; acw_tc=3ccdc15017639801686372308e6ee0b35b39b27c5cdeae465f8e16e3243f0e; ssxmod_itna=1-YqGxuD9DB7uD2DAxe9qmw4CTQq3TcODQKGHDycxYK0CDmxjKidqDU7idcb/mh7GrBx_dDfr2U5MD0yq_mDA5Dn_x7YDtr3FePe9hYqx_=s0CiKdo5NioIcfa8BxxB3WtsCe93Cdz64_K7v1mQDoDnne_DibDBKDncxDj6THDemaDCeDQxirDD4DAWoD0=8m1DDdzzgIs875ttrmz4GW107d1DGCM4GtLFSEz8BDz4DWS40kf4iaQURA1Y4DExGOTyrdz4GaMURnouYDEAeIovQDvoCw_iTAm885_T_xuaNo1=0re2WC37retD4_Do_DeR0qzGOKYbWieBhOQ0rbbHAYoQKotbHSRqrDoQHSF5w8HKyxVY4VYqOS_7YD7CECYntS2NB4NYG/C4rjGPK7KKDr3W/jGDD; ssxmod_itna2=1-YqGxuD9DB7uD2DAxe9qmw4CTQq3TcODQKGHDycxYK0CDmxjKidqDU7idcb/mh7GrBx_dDfr2U5mDDPo_OYp2bKDLinicQDBd9q4TdQ=bm6YI/70WqK9_tb8Pks7tCWRUklttvEOWmI7COGI4Fm9Teib_YUYoqjTNVAiiOi0D3ieoQfEDD',
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
