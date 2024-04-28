import contextlib
import json
import datetime
import traceback

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from util import logger

HOT_TOPIC_SEARCH_URL = 'https://emcreative.eastmoney.com/FortuneApi/GuBaApi/common'
HOT_TOPIC_DETAIL_URL = "https://mgubatopic.eastmoney.com/list?id={0}"

HEADERS = {
    'Content-type': 'application/json',
    'Origin': 'https://vipmoney.eastmoney.com',
    'Referer': 'https://vipmoney.eastmoney.com/',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36'
}

QUERIES = '{"url":"newctopic/api/Topic/HomeTopicRead?deviceid=IPHONE&version=10001000&product=Guba&plat=Iphone&p=1&ps=20","type":"get","parm":""}'
#
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


def _convert_to_timestamp(date_time_str):
    try:
        # 定义日期时间字符串的格式
        datetime_format = "%Y-%m-%dT%H:%M:%S"

        # 将字符串转换为datetime对象
        date_time_obj = datetime.datetime.strptime(date_time_str, datetime_format)

        # 转换为自Unix纪元以来的整数秒数
        timestamp = int(date_time_obj.timestamp())

        return timestamp
    except:
        return None


class EastMoney:

    @staticmethod
    def get_hot_topic():
        try:
            with request_session() as session:
                response = session.post(HOT_TOPIC_SEARCH_URL, data=QUERIES)
                if response.status_code != 200:
                    logger.error(f'get hot topic failed! code:{response.status_code}, text:{response.text}')
                    return None, response
                raw_data = json.loads(response.text)
                if 'rc' in raw_data and raw_data.get('rc') == 1:
                    topic_list = raw_data.get('re')
                    item_list = [{
                        'title': item_topic.get("name"),
                        'url': HOT_TOPIC_DETAIL_URL.format(item_topic.get("topicid")),
                        'hot_value': item_topic.get('clickCount', None),
                        'view_count': item_topic.get('clickCount', None),
                        'participant_count': item_topic.get('participantCount', ''),
                        'event_time': _convert_to_timestamp(item_topic.get('mTime', '')),
                        'extra': item_topic.get("summary", "")
                    } for item_topic in topic_list]
                    return item_list, response
                return None, response
        except:
            logger.exception('get hot topic failed')
            return None, None


if __name__ == "__main__":

    items, text = EastMoney.get_hot_topic()
    if items:
        for item in items:
            logger.info('item:%s', item)
