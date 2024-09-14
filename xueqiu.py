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
    'Cookie': 'acw_tc=2760827017262788697786953eaf4f98606848ecba75ab26853c08a6e988de; xq_a_token=49c5e355d2fc1b871fde601c659cf9ae1457a889; xqat=49c5e355d2fc1b871fde601c659cf9ae1457a889; xq_r_token=250d5a132310b89c6cf1193e084989736506a297; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOi0xLCJpc3MiOiJ1YyIsImV4cCI6MTcyNzkxNjc3OCwiY3RtIjoxNzI2Mjc4ODYzNTE4LCJjaWQiOiJkOWQwbjRBWnVwIn0.CAFU9V90ktg0hPo-kbLoYRywI0JzJiUAVPRz1zmJpheZQXnZNWLEbxpRjPS_O2MahrropTlKeQMyW_Ur70873ShhbDnZxLACHPgK2_p03Y9uYW3LTF4D-y0B5uHs8q59vQ6SxhwKWxDP19i4dyAYNraGq09aEuN1OfN9miE4Ak2XyVGNL5oEQjh8S2X_JovbObut965_IuaemFZ-r1lSjkQ720-htl8CHGKgtYTo_6sgjyfLmyfZSAYKapMhfVMjkLxwm7ok8uR1pxH7XN0c4n31B83QXEg8RYsO7IubnOSNcIOZSjvOiP8Vq_JOd0CJEPKBmG-DHaFnmdcq_KvyyQ; cookiesu=281726278869787; u=281726278869787; device_id=f209dddad001c71ee26c2dc5056fad28; Hm_lvt_1db88642e346389874251b5a1eded6e3=1726278870; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1726278870; HMACCOUNT=AAFFC100D24791E0; smidV2=20240914095430d82ad68c922a42abc78d51d589a0531000cc707ff78d6cb10; .thumbcache_f24b8bbe5a5934237bbc0eda20c1b6e7=A8tP2hIa45vetPEuEbQgduc6S8Z9pw4qMQRiPb8ZvCjbKjxAKADu9lavjwnHl/p3H+RZO+b5lkPwBEpqdLtwDA%3D%3D; ssxmod_itna=euD=DKAK7K0IqCuxBPiKGdvk1tGcI3YDCKhFKxROELqGXhmoDZDiqAPGhDC8SU7ep35fmir4HKO6YcxHw3W0PTvipSWBeD=xYQDwxYoDUxGtDpxG6tWDentD5xGoDPxDeDA0KDCSrkKDdcgIC9EpOm2P8cxGWIoKDmOKDR=oDSYYs/avFaW5DiooDXPYDaoKDuEvOzxi8D7KLIZ71D7cmvR8A+xi3UlFAh40O8tIHHGyzZO9UTjGTtNhiwe6dWiG3seW3PnCo=nGxEDr3671nzbhc4D=; ssxmod_itna2=euD=DKAK7K0IqCuxBPiKGdvk1tGcI3YDCKhFKxROEqA69qD/8xKTK7=D2teD',
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
