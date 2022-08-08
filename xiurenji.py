from pathlib import Path
import logging

from grab.spider import Spider, Task

BASE_DIR = Path(__file__).parent

IMG_DIR = BASE_DIR / 'img' / 'xiurenji'

BASE_URL = 'https://www.xiurenb.cc'


class XiuRenJiSpider(Spider):
    
    initial_urls = [BASE_URL]
    
    def prepare(self):
        if not IMG_DIR.exists():
            IMG_DIR.mkdir(parents=True)
    
    
    # 获取分类页面的信息
    def task_initial(self, grab, task):
        # print('开始获取秀人集分类页面信息')
        for elem in grab.doc.select('//li[@id="menu-item-205"]/ul[@class="sub-menu"]/li[@id="menu-item-1001"]/a'):
            href = elem.attr('href')
            title = elem.attr('title')
            print(f'{title}: {href}')
            cat_path = IMG_DIR / title
            if not cat_path.exists():
                cat_path.mkdir(parents=True)
            yield Task('category', url=f'{task.url}{href}', cat_path=cat_path, category=title, page=1)
    
    
    def task_category(self, grab, task):
        # print(f'开始获取{task.category}分类的第{task.page}页信息: {task.url}')
        category = task.category
        page = task.page
        cat_path = task.cat_path
        page_no = grab.doc.select('//div[@class="page"]')[0].select('a')[-1].text()
        if not page_no.isdigit() or page != int(page_no):
            next_page = page + 1
            next_url = '/'.join(task.url.split('/')[:-1]) + f'/index{next_page}.html'
            self.add_task(Task('category', url=next_url, cat_path=cat_path, category=category, page=next_page))
        for elem in grab.doc.select('//ul[@class="update_area_lists cl"]/li'):
            img_href = elem.select('a')[0].attr('href')
            title = elem.select('a')[0].attr('title')
            meta_title = elem.select('div[@class="case_info"]/div[@class="meta-title"]')[0].text().replace(f'[{category}]No.', '')
            girl_name = elem.select('a/div[@class="postlist-imagenum"]/span')[0].text()
            vol_path = cat_path / f'{meta_title}-{girl_name}'
            if not vol_path.exists():
                vol_path.mkdir(parents=True)
            with open(vol_path / 'info.txt', 'w') as f:
                f.write(title)
            img_url = '/'.join(task.url.split('/')[:-2]) + img_href
            yield Task('image', url=img_url, vol_path=vol_path, page=1)
        
    
    def task_image(self, grab, task):
        page = task.page
        vol_path = task.vol_path
        page_no = grab.doc.select('//div[@class="content_left"]/div[@class="page"]')[0].select('a')[-1].text()
        if not page_no.isdigit() or page != int(page_no):
            next_url = task.url.replace(f'{"" if page == 1 else f"_{page-1}"}.html', f'_{page}.html')
            next_page = page + 1
            self.add_task(Task('image', url=next_url, vol_path=vol_path, page=next_page))
        for elem in grab.doc.select('//div[@class="content"]/p/img/@src'):
            yield Task('download', url=f'{BASE_URL}{elem.text()}', vol_path=vol_path, priority=10)
    
            
    def task_download(self, grab, task):
        img_name = task.url.split('/')[-1]
        img_path = task.vol_path / img_name
        if img_path.exists():
            print(f'{img_path}已存在')
        grab.doc.save(task.vol_path / img_name)
    
        
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    bot = XiuRenJiSpider(thread_number=4)
    bot.setup_queue(backend='mongodb', database='xiurenji')
    bot.run()
