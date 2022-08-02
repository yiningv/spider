import sys
import time
from pathlib import Path
from io import BytesIO

import requests
import random
from lxml import etree
from fake_useragent import UserAgent
from PIL import Image


BASE_DIR = Path(__file__).parent.absolute()

img_path = BASE_DIR / 'img' / 'xinwenba'

# 随机UA
def get_random_ua():
    ua = UserAgent()
    return ua.random

headers = {
    'User-Agent': get_random_ua(),
    'Connection': 'close',
}


def download_webp(webp_url, view_path):
    print('downloading', webp_url)
    # 获取url末尾中的图片名称
    webp_name = webp_url.split('/')[-1]
    jpeg_file = webp_name.replace('.webp', '.jpg')
    if (view_path / jpeg_file).exists():
        print(f'{jpeg_file} already exists')
        return
    response = requests.get(webp_url, headers=headers, timeout=10)
    if response.status_code != 200:
        print(f'{jpeg_file} download failed')
        # 将下载失败的信息记录到文件中
        with open(view_path / 'failed.txt', 'a') as f:
            f.write(f'{jpeg_file}\n')
        return
    Image.open(BytesIO(response.content)).save(view_path / jpeg_file)
    time.sleep(random.randint(1, 3))


def page_info(target_url):
    response = requests.get(target_url, headers=headers, timeout=10)
    if response.status_code == 200:
        html = etree.HTML(response.text)
        places = html.xpath('//div[@class="place"]/a/text()')[1:]
        info_text = html.xpath('//div[@class="view_img"]/div[@class="text"]/text()')[0]
        img_src_list = html.xpath('//div[@class="view_img"]/div[@class="picture"]/p/img/@src')
        pag_total = int(html.xpath('//div[@class="paging"]/li/a/text()')[0].replace('共', '').replace('页:', ''))
        return places, info_text, img_src_list, pag_total
    return None, None, None, None


def run():
    if not img_path.exists():
        img_path.mkdir()
    target_url = sys.argv[1]
    # https://www.xinwenba.net/plus/view-751844-1.html
    print(f'开始{target_url}的爬取')
    view_path = target_url.split('/')[-1]
    start_page = view_path.replace(".html", "").split("-")[-1]
    view_number = view_path.split('-')[-2]
    target_temp = target_url.replace(view_path, f'view-{view_number}-')
    places, info_text, img_src_list, pag_total = page_info(target_url)
    if places is None or info_text is None or img_src_list is None or pag_total is None:
        print('page_info failed')
        return
    print(f'{info_text} total_page: {pag_total}')
    view_path = img_path.joinpath(*places) / view_number
    if not view_path.exists():
        view_path.mkdir(parents=True)
    # 在view_path下创建一个info.txt文件，并写入info_text
    with open(view_path / 'info.txt', 'w') as f:
        f.write(info_text)
    print(f'page-{start_page}')
    for img_src in img_src_list:
        download_webp(img_src, view_path)
    # 从1到pag_total，每次加1，并且拼接成url
    for i in range(1, pag_total + 1):
        target_url_new = f'{target_temp}{i}.html'
        if target_url_new == target_url:
            continue
        print(f'page-{i}')
        _, _, img_src_list, _ = page_info(target_url_new)
        for img_src in img_src_list:
            download_webp(img_src, view_path)
    


if __name__ == '__main__':
    run()