import logging
import os
from datetime import datetime
from bs4 import BeautifulSoup


logging.basicConfig(format='%(asctime)s %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)


def extract_text_from_html(rich_text):
    try:
        soup = BeautifulSoup(rich_text, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        return text
    except:
        return rich_text


def convert_chinese_to_arabic(text):
    multipliers = {
        '亿': 100000000,
        '千万': 10000000,
        '百万': 1000000,
        '万': 10000,
        '千': 1000
    }
    try:
        for key, value in multipliers.items():
            if key in text:
                number = float(text.replace(key, '')) * value
                return str(int(number))
        return str(int(float(text)))
    except:
        return ""


def current_time():
    return datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %z')


def current_date():
    return datetime.now().astimezone().strftime('%Y-%m-%d')


def ensure_dir(file):
    directory = os.path.abspath(os.path.dirname(file))
    if not os.path.exists(directory):
        os.makedirs(directory)


def write_text(file: str, text: str):
    ensure_dir(file)
    with open(file, mode='w') as f:
        f.write(text)
