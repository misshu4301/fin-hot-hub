import json
import os
import time
import urllib

from requests import Response

import util
from eastmoney import EastMoney
from xueqiu import XueQiu
from xhs import XHS
from toutiao import Toutiao
from weibo import Weibo
from douyin import Douyin
from baidu import Baidu
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
    hot_searches, resp = Weibo.get_hot_search()
    save_raw_response(hot_searches, 'weibo-hot-search')

    hot_searches, resp = Douyin.get_hot_search()
    save_raw_response(hot_searches, 'douyin-hot-search')

    hot_topics, resp = EastMoney.get_hot_topic()
    save_raw_response(hot_topics, 'eastmoney-hot-topic')

    hot_topics, resp = XueQiu.get_hot_topic()
    save_raw_response(hot_topics, 'xueqiu-hot-topic')

    hot_searches, resp = XHS.get_hot_search()
    save_raw_response(hot_searches, 'xhs-hot-search')

    hot_boards, resp = Toutiao.get_hot_search()
    for board, hot_searches in hot_boards.items():
        save_raw_response(hot_searches, f'toutiao-hot-{board}')

    hot_searches, resp = Baidu.get_hot_search()
    save_raw_response(hot_searches, 'baidu-hot-search')


if __name__ == "__main__":
    try:
        run()
    except:
        logger.exception('run failed')