import os
import random
import re
from contextlib import closing
import redis
from tqdm import tqdm
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import selenium.webdriver.support.ui as ui
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
import json
from retry import retry

from utils.files.file_tool import File


class PicSpider(File):
    def __init__(self):
        File.__init__(self)
        self.opt = webdriver.ChromeOptions()
        # 随机请求头
        # self.opt.add_argument('user-agent="{}"'.format(choice(User_Agent_list)))
        # 无界面模式，需要看界操作，注释此行
        # self.opt.add_argument('--headless')
        # 部署服务器上 需要使用此两行代码
        # display = Display(visible=0, size=(800, 600))
        # display.start()

        # 添加代理
        proxy_url = 'http://http.tiqu.alicdns.com/getip3?num=1&type=2&pro=0&city=0&yys=0&port=2&time=1&ts=0&ys=0&cs=0&lb=1&sb=0&pb=4&mr=1&regions='
        # proxy = requests.get(proxy_url)
        # proxy = json.loads(proxy.text)['data'][0]
        # self.proxies = {
        #     'https': 'http://{0}:{1}'.format(proxy['ip'], proxy['port'])
        # }
        # self.opt.add_argument("--proxy-server={}".format(self.proxies['https']))

        # 屏蔽图片
        # self.prefs = {"profile.managed_default_content_settings.images": 2}
        # self.opt.add_experimental_option("prefs", self.prefs)

        self.broser = webdriver.Chrome(options=self.opt)
        self.wait = WebDriverWait(self.broser, 20, 0.5)
        self.get_page = 0
        self.redis = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        # 数据库位置
        # self.engine = create_engine("mysql+pymysql://root:pythonman@127.0.0.1/Cartoon?charset=utf8")
        #
        # # 创建会话
        # self.session = sessionmaker(self.engine)
        # self.mySession = self.session()
        self.broser.maximize_window()
        self.brand = '未知'
        self.good_type = '箱包'
        self.api_url = 'http://129.226.185.233'
        self.good_id = ''

    def is_visible(self, locator, timeout=10):
        try:
            ui.WebDriverWait(self.broser, timeout).until(EC.visibility_of_element_located((By.XPATH, locator)))
            return True
        except Exception as f:
            print('加载不出元素')
            return False

    def add_pic_hash(self, data):
        result = self.redis.sadd('hash_pic3', data)  # 注意是 保存set的方式
        if result == 0:  # 若返回0,说明插入不成功，表示有重复
            return False
        else:
            return True

    def roll_window_to_bottom(self, browser, stop_length=None, step_length=500):
        """selenium 滚动当前页面，向下滑
        :param browser: selenium的webdriver
        :param stop_length: 滑动的最大值
        :param step_length: 每次滑动的值
        """
        original_top = 0
        while True:  # 循环向下滑动
            if stop_length:
                if stop_length - step_length < 0:
                    browser.execute_script("window.scrollBy(0,{})".format(stop_length))
                    break
                stop_length -= step_length

            browser.execute_script("window.scrollBy(0,{})".format(step_length))
            time.sleep(0.5 + random.random())  # 停顿一下
            check_height = browser.execute_script(
                "return document.documentElement.scrollTop || window.pageYOffset || document.body.scrollTop;")
            if check_height == original_top:  # 判断滑动后距顶部的距离与滑动前距顶部的距离
                break
            original_top = check_height

    def run(self):
        # brand_id = self.check_brand()
        url = 'https://gxhy1688.com/market/web/Shopindex?marketCode=gz&uid=c020685bfc714819a50f1514612ca3e1'
        self.broser.get(url)
        print('等待数据加载')
        time.sleep(15)
        business_name = self.broser.find_element(By.XPATH, '//*[@id="app"]/div/div/div[1]/div/div/div[1]/div[2]').text
        while True:
            if self.is_visible('//div[@class="trends_rows"]') is True:
                elements = self.broser.find_elements(By.XPATH, '//div[@class="trends_rows"]')
                for element in elements:
                    img_url = element.find_element(By.XPATH, './/img').get_attribute('src')
                    re_data = re.search(r'http://product.aliyizhan.com/person/(.*)/(.*)/(\d+).jpg', img_url)
                    if re_data:
                        hash1 = re_data.group(1)
                        hash2 = re_data.group(2)
                        hash_existence = self.add_pic_hash(hash2)
                        if hash_existence is False:
                            # 已经存在
                            pass
                        elif hash_existence is True:
                            for i in range(9):
                                hash_url = f'http://product.aliyizhan.com/person/{hash1}/{hash2}/{i}.jpg'
                                filename = r'D:\共享货源辽宁货\pic\{}/{}.jpg'.format(hash2, i)
                                dir_path = r'D:\共享货源辽宁货\pic\{}'.format(hash2)
                                isExists = os.path.exists(dir_path)
                                # 判断结果
                                if not isExists:
                                    os.makedirs(dir_path)

                                self.download(filename, hash_url, False)

                            # if self.add_good(hash2, '未设置', brand_id, 0) is True:


                print('往下滑动')
                self.roll_window_to_bottom(self.broser, stop_length=2000)

                if self.is_visible('//*[@id="app"]/div/div/div[3]/div[2]/div/button[2]') is True:
                    self.get_page += 1
                    if self.get_page == 100:
                        self.broser.quit()
                        break
                    else:
                        self.broser.find_element(By.XPATH, '//*[@id="app"]/div/div/div[3]/div[2]/div/button[2]').click()
                else:
                    self.roll_window_to_bottom(self.broser, stop_length=2000)
            else:
                self.broser.refresh()  # 刷新方法 refresh
                time.sleep(10)


if __name__ == '__main__':
    obj = PicSpider()
    obj.run()
