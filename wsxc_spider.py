import os
import traceback
from contextlib import closing
from pprint import pprint

import redis
import requests
import time
import json
from retry import retry
import re
from tqdm import tqdm


class WsSpider(object):
    def __init__(self):
        self.next_page = ''
        self.type_name = 'ysl2022'
        self.type_id = '27134095'
        self.redis = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self.api_url = 'http://129.226.185.233'
        # self.api_url = 'http://127.0.0.1:8000'

    @retry()
    def download(self, path, filename, download_url, end):
        """
        下载文件
        :param path: 下载路径
        :param filename: 下载文件名字
        :param download_url: 下载地址
        :param end: 文件后缀
        :return: True:下载完毕 False：下载失败
        """
        try:
            proxies = {'http': 'http://localhost:7890', 'https': 'http://localhost:7890'}
            with closing(requests.get(download_url, stream=True, timeout=5, verify=False, proxies=proxies)) as r:
                chunk_size = 1024
                content_size = int(r.headers['content-length'])
                with open(path + filename + '.' + end, "wb") as f:
                    n = 1
                    with tqdm(r.iter_content(chunk_size=chunk_size)) as t:
                        for chunk in t:
                            loaded = n * 1024.0 / content_size
                            # 设置进度条左边显示的信息
                            t.set_description("正在下载 {}".format(filename + end))
                            f.write(chunk)
                            # 设置进度条右边显示的信息
                            t.set_postfix(下载进度=str(int(loaded * 100)) + '%')
                            n += 1
            return True

        except Exception as f:
            print(f)
            print(traceback.print_exc())
            return False

    @retry()
    def add_good(self, type_name, goods_id, update_time, title, good_urls):
        url = f'{self.api_url}/api/wsxc/goods'
        rsp = requests.post(url, data={
            "type_name": type_name,
            "goods_id": goods_id,
            "update_time": update_time,
            "title": title,
            "good_urls": good_urls

        }, timeout=10)

        if json.loads(rsp.text)['status'] == 0:
            print(json.loads(rsp.text))
            return True
        elif json.loads(rsp.text)['status'] == 1:
            print('已经存在')
            return False

    def add_pic_hash(self, data):
        result = self.redis.sadd('wsxc', data)  # 注意是 保存set的方式
        if result == 0:  # 若返回0,说明插入不成功，表示有重复
            return False
        else:
            return True

    def get_goods_info(self, tag_id):
        if self.next_page is None:
            url = 'https://www.szwego.com/album/personal/all?&searchValue=&searchImg=&startDate=&endDate=&albumId=_ds5vNk0VPqC9hi1fqC5BewJfjAcH-WsDBdv_L1A&requestDataType='
        else:
            url = f'https://www.szwego.com/album/personal/all?&searchValue=&searchImg=&startDate=&endDate=&albumId=_ds5vNk0VPqC9hi1fqC5BewJfjAcH-WsDBdv_L1A&slipType=1&timestamp={self.next_page}&requestDataType=&transLang=en'

        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Content-Length': '22',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Cookie': 'sajssdk_2015_cross_new_user=1; token=QzQ4NkFGN0UyOTI2MTVERDQ0QzhGRUQwMkJFRDQzODM5NzY5MTkzNDc4NTQzRUFGMEFDNjgxRDg3MkI4NENCNDQ3NDc1OEM3NTM4MTU1RjNBNDYwNDhCN0E2NUFFNTE3; client_type=net; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22_dvNvNTp0sDBl3ouNNl-_kCB0xsKxk8hYeFPXreQ%22%2C%22first_id%22%3A%22187221dea72b64-07c632b55794af-1e525634-1764000-187221dea73b26%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfbG9naW5faWQiOiJfZHZOdk5UcDBzREJsM291Tk5sLV9rQ0IweHNLeGs4aFllRlBYcmVRIiwiJGlkZW50aXR5X2Nvb2tpZV9pZCI6IjE4NzIyMWRlYTcyYjY0LTA3YzYzMmI1NTc5NGFmLTFlNTI1NjM0LTE3NjQwMDAtMTg3MjIxZGVhNzNiMjYifQ%3D%3D%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%24identity_login_id%22%2C%22value%22%3A%22_dvNvNTp0sDBl3ouNNl-_kCB0xsKxk8hYeFPXreQ%22%7D%2C%22%24device_id%22%3A%22187221dea72b64-07c632b55794af-1e525634-1764000-187221dea73b26%22%7D; JSESSIONID=D25CB4707D5984E07DCA15E5B053CD19',
            'Host': 'www.szwego.com',
            'Origin': 'https://www.szwego.com',
            'Referer': f'https://www.szwego.com/static/index.html?t={int(time.time() * 1000)}',
            'sec-ch-ua': '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
            'wego-channel': 'net',
            'wego-staging': '0',
            'X-Requested-With': 'XMLHttpRequest',
        }

        data = {
            'tagList': [str(tag_id)]
        }

        return_data = {
            'goods': [],
            'tag_title': []
        }
        proxies = {'http': 'http://localhost:7890', 'https': 'http://localhost:7890'}
        rsp = requests.post(url, headers=headers, data=data, proxies=proxies, verify=False)
        json_data = json.loads(rsp.text)
        if json_data['errcode'] == 0:
            result = json_data['result']
            return_data['tag_title'] = json_data['result']['tagTitle']

            pagination = result['pagination']
            if 'pageTimestamp' in pagination:
                # 有下一页
                self.next_page = result['pagination']['pageTimestamp']
            else:
                self.next_page = None

            items = result['items']
            for item in items:
                img_urls = []
                title = item['title']
                parent_shop_id = item['parent_shop_id']
                goods_id = item['goods_id']
                update_time = item['update_time']
                imgs = item['imgsSrc']
                video_url = item['videoUrl']

                if len(video_url) > 0:
                    img_urls.append(video_url)
                else:
                    for img in imgs:
                        img_urls.append(img)

                return_data['goods'].append({
                    'title': title,
                    'parent_shop_id': parent_shop_id,
                    'goods_id': goods_id,
                    'update_time': update_time,
                    'imgs': img_urls,
                })
            print(return_data)
            return return_data

        else:
            print('获取失败')

        time.sleep(10)

    @staticmethod
    def get_goods_type():
        return_data = []
        url = f'https://www.szwego.com/commodity/tags?hasVideo=0&hideUnCategorized=true&albumId=_ds5vNk0VPqC9hi1fqC5BewJfjAcH-WsDBdv_L1A&_={int(time.time() * 1000)}'
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Cookie': 'sajssdk_2015_cross_new_user=1; token=QzQ4NkFGN0UyOTI2MTVERDQ0QzhGRUQwMkJFRDQzODM5NzY5MTkzNDc4NTQzRUFGMEFDNjgxRDg3MkI4NENCNDQ3NDc1OEM3NTM4MTU1RjNBNDYwNDhCN0E2NUFFNTE3; client_type=net; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22_dvNvNTp0sDBl3ouNNl-_kCB0xsKxk8hYeFPXreQ%22%2C%22first_id%22%3A%22187221dea72b64-07c632b55794af-1e525634-1764000-187221dea73b26%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfbG9naW5faWQiOiJfZHZOdk5UcDBzREJsM291Tk5sLV9rQ0IweHNLeGs4aFllRlBYcmVRIiwiJGlkZW50aXR5X2Nvb2tpZV9pZCI6IjE4NzIyMWRlYTcyYjY0LTA3YzYzMmI1NTc5NGFmLTFlNTI1NjM0LTE3NjQwMDAtMTg3MjIxZGVhNzNiMjYifQ%3D%3D%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%24identity_login_id%22%2C%22value%22%3A%22_dvNvNTp0sDBl3ouNNl-_kCB0xsKxk8hYeFPXreQ%22%7D%2C%22%24device_id%22%3A%22187221dea72b64-07c632b55794af-1e525634-1764000-187221dea73b26%22%7D; producte_run_to_dev_tomcat=; JSESSIONID=E844031ECE5288968F2964C09B4F85F7',
            'Host': 'www.szwego.com',
            'Referer': 'https://www.szwego.com/static/index.html?link_type=pc_home&shop_id=_dvNqfnsUgKkzO1r9pom_ZMZbcGWb0uVHojY2Vbw&shop_name=Nemo',
            'sec-ch-ua': '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
            'wego-albumid': '',
            'wego-channel': 'net',
            'wego-staging': '0',
            'wego-uuid': '',
            'wego-version': '',
            'X-Requested-With': 'XMLHttpRequest',
        }
        proxies = {'http': 'http://localhost:7890', 'https': 'http://localhost:7890'}
        rsp = requests.get(url, headers=headers, proxies=proxies, verify=False)
        json_data = json.loads(rsp.text)
        tags = json_data['result']['allTags']
        for tag in tags:
            tag_name = tag['tagName']
            tag_id = tag['tagId']
            item_count = tag['itemCount']
            return_data.append({
                'tag_name': tag_name,
                'tag_id': tag_id,
            })

        return return_data

    def run(self):
        types = self.get_goods_type()
        for good_type in types:
            # 类型名字
            self.type_name = good_type['tag_name']
            # 类型id
            self.type_id = good_type['tag_id']

            print('type_name:' + self.type_name)
            print('type_id:' + str(self.type_id))
            print('----------')
            while True:
                good_infos = self.get_goods_info(self.type_id)
                if len(good_infos['goods']) > 0:
                    for good in good_infos['goods']:
                        title = good['title']
                        goods_id = good['goods_id']
                        imgs = good['imgs']
                        update_time = good['update_time']

                        # pic_cwd = os.getcwd() + '/pic/'
                        # filename = str(0) + str(goods_id)
                        # if imgs[0].endswith('.jpg'):
                        #     # self.download(pic_cwd, filename, imgs[0], 'jpg')
                        #     pass
                        #
                        # elif imgs[0].endswith('.mp4'):
                        #     self.download(pic_cwd, filename, imgs[0], 'mp4')

                        hash_existence = self.add_pic_hash(goods_id + '1')
                        if hash_existence is False:
                            # 已经存在
                            print(f'{goods_id}:此商品已经存在')
                            pass
                        elif hash_existence is True:
                            # pic_cwd = os.getcwd() + '/pic/'
                            # filename = str(0) + str(goods_id)
                            # if imgs[0].endswith('.jpg'):
                            #     # self.download(pic_cwd, filename, imgs[0], 'jpg')
                            #     pass
                            #
                            # elif imgs[0].endswith('.mp4'):
                            #     self.download(pic_cwd, filename, imgs[0], 'mp4')

                            self.add_good(self.type_name, goods_id, update_time, title, str(imgs))
                else:
                    print('没有作品')

                if self.next_page is None:
                    break
                else:
                    time.sleep(10)

        print('结束')


if __name__ == '__main__':
    obj = WsSpider()
    obj.run()