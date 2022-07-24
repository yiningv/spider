import os
import time
from pathlib import Path
import requests
import random
from lxml import etree
from fake_useragent import UserAgent


page_url = 'https://qingbuyaohaixiu.com/'
# https://s3.qingbuyaohaixiu.com/image/6f711a138b6582a6a189bf315afb6577.jpeg
img_url = 'https://s3.qingbuyaohaixiu.com/image/'
img_path = Path(__file__).parent.absolute() / 'img' / 'qingbuyaohaixiu'

# 随机UA
def get_random_ua():
    ua = UserAgent()
    return ua.random

headers = {
    'User-Agent': get_random_ua(),
    'Connection': 'close',
}


def get_page_hrefs():
    response = requests.get(page_url, headers=headers, timeout=10)
    if response.status_code == 200:
        html = etree.HTML(response.text)
        get_page_hrefs = html.xpath('//ul[@class="pagination"]/li/a/@href')
        return get_page_hrefs[:-1]
    return []


def get_img_srcs(page):
    url = f'{page_url}{page}'
    print(url)
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 200:
        html = etree.HTML(response.text)
        get_img_srcs = html.xpath('//div[@class="rcm4"]/a/amp-img/@src')
        return get_img_srcs
    return []


def download_img(jpeg_file):
    print('downloading', jpeg_file)
    if os.path.exists(img_path / jpeg_file):
        print(f'{jpeg_file} already exists')
        return
    url = f'{img_url}{jpeg_file}'
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code != 200:
        print(f'{jpeg_file} download failed')
        # 将下载失败的信息记录到文件中
        with open(img_path / 'failed.txt', 'a') as f:
            f.write(f'{jpeg_file}\n')
        return
    with open(img_path / jpeg_file, 'wb') as f:
        f.write(response.content)
    

def run():
    count = 1
    page_hrefs = get_page_hrefs()
    for page_href in page_hrefs:
        print(f'page {count}')
        img_srcs = get_img_srcs(page_href)
        for img_src in img_srcs:
            img_path = img_src.split('/')[-2]
            download_img(f'{img_path}.jpeg')
        count += 1
        time.sleep(random.randint(1, 3))
            
if __name__ == '__main__':
    run()