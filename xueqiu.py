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
    'Cookie': 'acw_tc=2760828017216310880702979e98876e21dc38b700fea868d8c1e1d03f12ab; xq_a_token=aeb5755652c41b7828c9412ee90b26e08840b0c8; xqat=aeb5755652c41b7828c9412ee90b26e08840b0c8; xq_r_token=9ee9347bb54fea0445403de921297a01af9f4646; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOi0xLCJpc3MiOiJ1YyIsImV4cCI6MTcyNDAyODc2OCwiY3RtIjoxNzIxNjMxMDc1NzYzLCJjaWQiOiJkOWQwbjRBWnVwIn0.dI2QCQzzKJnPhHSA0UZBTtlTHI9rigC6tNKliO7x1wCrPk2St_HxyvxWNqAx5dYQUCWGjN6yVkQF3RAnQfP0FrZfxtburY_dd5VldMcyNp7m636WtLqHw6ZjEI1EfUy1lx4bUeYx49VU4uQEasC1VKvvrMYwuuI9-__KWEOAd7i1KXmhi-J6mg53s98Yv-08Ks_VTC-2ckp99FDbYPqVrE2dUHcv77AWWDZeG0rjdriEcsOVW7KumgI9b8RZjgrLa-JfpTRNhZmiBCQqstw-5o19y7JR4gvyg9hACxLdT5itXU8-nIrNf_0XqY6Ms-4VHpd9nnsEGafXMyoiCsnqFA; cookiesu=661721631088076; u=661721631088076; device_id=f209dddad001c71ee26c2dc5056fad28; Hm_lvt_1db88642e346389874251b5a1eded6e3=1721631087; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1721631087; HMACCOUNT=2D32DF7EF328947D; smidV2=2024072214512644f3ddef55efaabee50c2d824a771eae00740c6fc191b7470; .thumbcache_f24b8bbe5a5934237bbc0eda20c1b6e7=zbbEw7nz7PIO5fQ9YnDDMt6xKfk/8GejyydXr/P/yeHWQE1ZOY4LV1UqVYwnPWKXVpY3cxIu6RZLNH9tgWRiVA%3D%3D',
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
