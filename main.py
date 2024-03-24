import json
import os
import time
import urllib

from requests import Response

import util
from eastmoney import EastMoney
from xueqiu import XueQiu
from util import logger


def save_raw_response(resp, filename: str):
    """保存数据
    """
    if resp:
        content = json.dumps(resp, ensure_ascii=False, indent=4)
        filename = '{}.json'.format(filename)
        logger.info('save response:%s', filename)
        date = util.current_date()
        file = os.path.join('raw', date, filename)
        util.write_text(file, content)



def run():
    # 获取数据
    # 热门话题
    hot_topics, resp = EastMoney.get_hot_topic()
    save_raw_response(hot_topics, 'eastmoney-hot-topic')

    hot_topics, resp = XueQiu.get_hot_topic()
    save_raw_response(hot_topics, 'xueqiu-hot-topic')


if __name__ == "__main__":
    try:
        run()
    except:
        logger.exception('run failed')