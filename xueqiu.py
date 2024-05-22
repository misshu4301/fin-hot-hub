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
    'Cookie': 'cookiesu=491711545514312; u=491711545514312; s=al12hlsv19; smidV2=20240327211835e331676f9e8800153b9491951b7341e40039407a6841a0430; device_id=32ac1147010a71d6a681b82332222f4d; Hm_lvt_1db88642e346389874251b5a1eded6e3=1714303208; acw_tc=2760826a17163638828896490eb1195404325c467b5d64b773e644c214af7d; xq_a_token=c2aefa380b9072a563e961143570e259329d659f; xqat=c2aefa380b9072a563e961143570e259329d659f; xq_r_token=2823a23fcab28b5723fbd7c5220a4ba4cc755a52; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOi0xLCJpc3MiOiJ1YyIsImV4cCI6MTcxODg0NDcxMiwiY3RtIjoxNzE2MzYzODQ1Mjc1LCJjaWQiOiJkOWQwbjRBWnVwIn0.ImpOMtBicG3xP_HgXKhcwIB6Eh8pWW0cdhZ0aDWvq7sAcctQZkkBMsMLecyEj9EaS4APhWa0CJLCz2DiWcN0C-N_WaMJXhTK-vubNuq8HXlcORxNLh1yCldCnYemUOMiivHfqqh4ynt5AGmGodmjothQjFEnphPHfM6cvhFhiTj7W5IyAiX8FLN6JdAVk_tyGhPGt6ewWbNfrDUO_Xu21TwFKqAWEV2d6cR6BJ9sOW-KJdSPYpA01bLT-zAiEG_mbBYE8agbQGeT6y0ZG82YzdxKh6SSZ-YCiCdoFycTGR9fWKhiZi0GaNZdJ4pmX74osEBIGY2WoTrEQkzQn3pKLQ; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1716363883; .thumbcache_f24b8bbe5a5934237bbc0eda20c1b6e7=YM+5AAEVr+IEyRGoHOOzRzByFdQnHmO14QONyB3KcXDMXeTK37LdNiAaLBP+TLTwZHf0JMHuGH/oajgK5tFtHg%3D%3D',
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
