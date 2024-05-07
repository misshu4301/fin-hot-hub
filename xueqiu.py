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
    'Cookie': 'cookiesu=851711269429979; device_id=e97d164930dd3d78d0e7743613c02e2e; smidV2=20240407162313dfce9c8a61a64a0c45e557b8ead655ee00802b9f8aadc31b0; acw_tc=2760825e17150651605224117eb128075f56597e8d904cd976a81446e12c74; xq_a_token=ea6ef3abf0b64fa4ec4343c5608361ed54114204; xqat=ea6ef3abf0b64fa4ec4343c5608361ed54114204; xq_r_token=38fbe8417b7b1b21f8f4c0a40a8e75e1f538990a; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOi0xLCJpc3MiOiJ1YyIsImV4cCI6MTcxNzU0ODcxMCwiY3RtIjoxNzE1MDY1MTM1MTk0LCJjaWQiOiJkOWQwbjRBWnVwIn0.NDeCNK1u_V4Blcw3GsYwa72lNgXICQSbfYhMvLXDjt5O_k9xOtoYVsuVMYV28sXttoyOKTkHFAAvXLuH-nODbYQcNYqvim2EqzxLTrb7twUTKlujpfSc8wieteMA1UlFWVVlBF3p-DomLbF5IZiq0eDf4Xdtf-SKJq5o_ZQWidGH3k-sLLoqJ8lQYFBFskIjpxOelSX7mHRXoDjS8GBEjFmOm71Lydo64LTcoVfxE3Jsf2DuQkppfrhiLhBWPEh1cOxBoClltFR6MfBFiM6DtpBcI3dAwePYKjmDZORaKvRgPMT__qX6kuW4s0CGOSthkroP9fvP7xf7K8JLLnMYKA; u=851711269429979; Hm_lvt_1db88642e346389874251b5a1eded6e3=1712478194,1715065161; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1715065161; .thumbcache_f24b8bbe5a5934237bbc0eda20c1b6e7=onBojnNRKAMb5RH7Dz760oeWPz/Pxin/YbTM4PdG4cKyU84uK+HAx2tYOuscFoEcNpggsn5MkUStBmw+MTgvPw%3D%3D',
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
