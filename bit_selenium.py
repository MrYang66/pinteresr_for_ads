from bit_api.bit_api import *
from selenium.webdriver.chrome.service import Service
import base64
import configparser
import os
import time
import pyperclip
import requests
from multiprocessing import Pool
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from utils.db.mongo_tool import MongoDB
from utils.db.redis_tool import Redis
from utils.files.file_tool import File
from utils.loggers.log import Loguru
from utils.power.ads_power import AdsPower
from loguru import logger
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from utils.pic.Picture import collection_pic


class Pinterest(AdsPower, File):
    def __init__(self):
        AdsPower.__init__(self)
        File.__init__(self)
        self.cf = configparser.RawConfigParser()
        self.cf.read(os.path.join(os.path.split(os.path.abspath(__file__))[0], 'config.ini'))

    def set_goods_info(self, driver, result, bit_dict):
        if result:
            mkdir_path = rf'{self.cf.get("path", "download_path")}\{time.strftime("%Y-%m-%d")}\{result["tag_name"]}'
            if os.path.exists(mkdir_path) is True:
                pass
            else:
                os.makedirs(mkdir_path)

            files = ''
            img_path_list = []
            # 判断什么数据类型
            if result['video_url']:
                filename = os.path.join(mkdir_path, str(random.randint(1, 1000000)) + '.mp4')
                logger.info(f'账号: {bit_dict["name"]} 正在下载作品')
                video_path = self.download(filename, result['video_url'], self.cf.get('proxy', 'download_proxy'))
                if video_path:
                    logger.info(f'账号: {bit_dict["name"]}  下载作品成功')
                    files += video_path
                else:
                    logger.warning(f'账号: {bit_dict["name"]}  下载作品失败')
                    return

            elif len(result['img_list']) > 0 and not result['video_url']:
                print(len(result['img_list']))
                logger.info(f'账号: {bit_dict["name"]} 正在下载作品')
                range_num = ''
                if self.cf.get('ads', 'mode') == 'idea':
                    if self.cf.get('mode', 'upload_pic_type') == 'collection':
                        range_num = 5
                    else:
                        range_num = 1
                elif self.cf.get('ads', 'mode') == 'pin':
                    range_num = 5

                for img_url in result['img_list'][0:range_num]:
                    filename = os.path.join(mkdir_path, str(random.randint(1, 1000000)) + '.jpg')
                    if self.download(filename, img_url, self.cf.get('proxy', 'download_proxy')):
                        logger.info(f'账号: {bit_dict["name"]}  下载作品成功')
                        img_path_list.append(filename)
                    else:
                        logger.warning(f'账号: {bit_dict["name"]}   下载作品失败')
                        return

                if self.cf.get('mode', 'upload_pic_type') == 'collection':
                    out_path = os.path.join(mkdir_path, str(random.randint(1, 1000000)) + '.jpg')
                    print(len(img_path_list))
                    out_path = collection_pic(img_path_list, out_path)
                    img_path_list.clear()
                    img_path_list.append(out_path)

            for index, img_file in enumerate(img_path_list):
                if index == len(img_path_list) - 1:
                    files += img_file
                elif index != len(img_path_list) - 1:
                    files += img_file + '\n'

            print(files)
            try:
                if self.cf.get('ads', 'mode') == 'idea':
                    driver.find_element(By.CSS_SELECTOR, '#storyboard-upload-input').send_keys(files)
                elif self.cf.get('ads', 'mode') == 'pin':
                    driver.find_element(By.XPATH, '//input[@aria-label="File upload"]').send_keys(files)

                time.sleep(5)
            except:
                pass

            if self.element_click(driver, '//*[text()="Create a collage"]', in_timeout=10, in_ms=3):
                self.element_click(driver, '//*[text()="Create Pin"]', in_timeout=10, in_ms=5)

            try:
                # 设置图版
                if self.element_click(driver, '//*[@data-test-id="board-dropdown-select-button"]', in_timeout=10,
                                      in_ms=3):
                    driver.find_element(By.XPATH, '//*[@id="pickerSearchField"]').send_keys(result['type'])
                    time.sleep(3)
                    if self.element_locate(driver, f"""//div[@title="{result['type']}"]""", in_timeout=5):
                        self.element_click(driver, f"""//div[@title="{result['type']}"]""", in_ms=2)
                    else:
                        self.element_click(driver, '//div[@title="Create board"]', in_ms=5)
                        self.element_click(driver, '//button[@type="submit"]', in_ms=5)

            except Exception as f:
                pass

            # try:
            #     # 设置标签
            #     if self.element_locate(driver, '//input[@id="storyboard-selector-interest-tags"]', in_timeout=10):
            #         if len(self.trends_tag_list) > 0:
            #             for tag in random.sample(self.trends_tag_list, 5):
            #                 tag_element = driver.find_element(By.XPATH,
            #                                                   '//input[@id="storyboard-selector-interest-tags"]')
            #                 tag_element.send_keys(Keys.CONTROL, 'a')
            #                 tag_element.send_keys(tag)
            #                 tag_element.click()
            #                 time.sleep(3)
            #                 if self.element_locate(driver,
            #                                        '//div[@data-test-id="storyboard-suggestions-list"]//div[@data-test-id="storyboard-suggestions-item"]',
            #                                        in_timeout=3) is not False:
            #                     tags = driver.find_elements(By.XPATH,
            #                                                 '//div[@data-test-id="storyboard-suggestions-list"]//div[@data-test-id="storyboard-suggestions-item"]')
            #                     driver.find_element(By.XPATH, f"//*[text()='{tags[0].text}']").click()
            #
            #         else:
            #             pass
            #
            # except Exception as f:
            #     pass

        # 设置点子图标题
        if self.element_locate(driver, '//input[@id="storyboard-selector-title"]', in_timeout=10):
            title_element = driver.find_element(By.XPATH, '//input[@id="storyboard-selector-title"]')
            title_element.send_keys(Keys.CONTROL, 'a')
            if result:
                title_element.send_keys(f'If you need this {result["type"]}, {self.cf.get("introductions", "title")}')
            else:
                title_element.send_keys(f'If you need this goods, {self.cf.get("introductions", "title")}')

        # 设置pin图标题
        elif self.element_locate(driver, '//textarea[@placeholder="Add your title"]', in_timeout=10):
            title_element = driver.find_element(By.XPATH, '//textarea[@placeholder="Add your title"]')
            title_element.send_keys(Keys.CONTROL, 'a')
            if result:
                title_element.send_keys(f'If you need this {result["type"]}, {self.cf.get("introductions", "title")}')
            else:
                title_element.send_keys(f'If you need this goods, {self.cf.get("introductions", "title")}')

        # 设置点子图简介
        if self.element_locate(driver, '//div[@aria-autocomplete="list"]', in_timeout=10):
            description = ''
            if int(self.cf.get("introductions", "set_product_introduction")) == 1:
                description_list = self.cf.get("introductions", "self_introductions").split('-')
                for dec in description_list:
                    description += dec + '\n'

            if self.cf.get('ads', 'mode') == 'idea':
                for i in range(3):
                    description += '\n'

                if len(description) < 400:
                    condition = {"type": self.cf.get("mongodb", "tag_type")}
                    mongo_object = MongoDB(self.cf.get('mongodb', 'host'), self.cf.get('mongodb', 'port'),
                                           self.cf.get('mongodb', 'dbName'), self.cf.get('mongodb', 'tags_tb_name'))

                    res = mongo_object.mongo_filter_many(condition)
                    for temp in random.sample(res, 10):
                        description += f"#{temp['tag_name']}"
                else:
                    pass

            dec_element = driver.find_element(By.XPATH, '//div[@aria-autocomplete="list"]')
            dec_element.click()
            dec_element.send_keys(Keys.CONTROL, 'a')
            pyperclip.copy(description)
            act = ActionChains(driver)
            act.key_down(Keys.CONTROL).send_keys("v").key_up(Keys.CONTROL).perform()

        # 设置链接
        if self.element_locate(driver, '//input[@id="storyboard-selector-link"]', in_timeout=5):
            link_element = driver.find_element(By.XPATH, '//input[@id="storyboard-selector-link"]')
            link_element.click()
            link_element.send_keys(Keys.CONTROL, 'a')
            link_element.send_keys(self.cf.get("introductions", "ws_url"))
        elif self.element_locate(driver, '//input[@placeholder="Add a link"]', in_timeout=5):
            link_element = driver.find_element(By.XPATH, '//input[@placeholder="Add a link"]')
            link_element.click()
            link_element.send_keys(Keys.CONTROL, 'a')
            link_element.send_keys(self.cf.get("introductions", "ws_url"))
        elif self.element_locate(driver, '//textarea[@placeholder="Add a destination link"]', in_timeout=5):
            link_element = driver.find_element(By.XPATH, '//textarea[@placeholder="Add a destination link"]')
            link_element.click()
            link_element.send_keys(Keys.CONTROL, 'a')
            link_element.send_keys(self.cf.get("introductions", "ws_url"))

        time.sleep(2)
        # 发布作品
        if self.element_click(driver, '//*[text()="Publish"]', in_timeout=10, in_ms=3):
            self.element_click(driver, '//*[text()="Publish"]', in_timeout=5, in_ms=3)
            self.element_click(driver, '//*[text()="Publish"]', in_timeout=5, in_ms=3)
            logger.info(f'账号: {bit_dict["name"]} 正在上传作品')
            refresh_flag = 0
            while True:
                current_url = str(driver.current_url)
                if current_url.startswith('https://www.pinterest.com/pin/') or current_url.startswith(
                        'https://www.pinterest.co.uk/pin') and self.cf.get('ads', 'mode') == 'idea':
                    logger.info(f'账号: {bit_dict["name"]} 上传作品完毕')
                    break
                elif self.element_locate(driver, '//*[text()="You created a Pin!"]', in_timeout=2):
                    self.element_click(driver, '//*[text()="See your Pin"]', in_timeout=5, in_ms=3)
                    break
                elif self.element_locate(driver, '//*[text()="See it"]', in_timeout=2):
                    break
                else:
                    refresh_flag += 1
                    time.sleep(3)
                    if refresh_flag % 15 == 0:
                        logger.info(f'账号: {bit_dict["name"]} 长时间未上传成功, 刷新页面...')
                        driver.refresh()
                        time.sleep(3)
                        try:
                            logger.info(f'账号: {bit_dict["name"]} 切换到弹窗')
                            alert = driver.switch_to.alert  # 切换到弹窗
                            alert.accept()  # 接受
                            break
                        except Exception as f:
                            print(f)
                            break

    def get_good_info(self, bit_dict):
        mongo_object = MongoDB(self.cf.get('mongodb', 'host'), self.cf.get('mongodb', 'port'),
                               self.cf.get('mongodb', 'dbName'), self.cf.get('mongodb', 'tbName'))

        redis_object = Redis(self.cf.get('redis', 'host'), self.cf.get('redis', 'port'),
                             self.cf.get('redis', 'db'))

        # 获取上传媒体类型
        good_media = self.cf.get('bit', 'good_media')
        redis_key = ''
        good_type = random.choice(self.cf.get('bit', 'good_type').split(','))
        # 获取redis_key
        if good_media == 'video':
            redis_key = base64.b64encode((f"video_{bit_dict['user_id']}" + good_type).encode('utf-8'))
        elif good_media == 'img':
            redis_key = base64.b64encode((f"img_{bit_dict['user_id']}" + good_type).encode('utf-8'))

        good_id = redis_object.lpop_data(redis_key)
        logger.info(f'{bit_dict["name"]}: 获取商品id: {good_id}')
        # redis 还有缓存数据
        if good_id is not None:
            query = {
                '$and': [
                    {'_id': good_id},
                    {'type': good_type},
                    {'$where': 'this.img_list.length > 4'}  # img_list字段的元素数量大于4
                ]
            }
            result = mongo_object.mongo_filter_once(query)
            # 查询到数据
            if result is not None:
                return result
            else:
                logger.error(f'{bit_dict["name"]}: 查询mongodb数据失败')
                return False

        # redis 没有缓存
        else:
            logger.warning(f'{bit_dict["name"]}: redis没有缓存数据')
            return False

    def upload_idea_goods(self, driver, bit_dict):
        print(bit_dict)
        driver.get('https://www.pinterest.com/idea-pin-builder/')
        if self.element_locate(driver, '//*[text()="It looks like we are having trouble connecting."]', in_timeout=5):
            driver.refresh()
            time.sleep(5)

        # 有草稿
        if self.element_locate(driver, '//*[@data-test-id="storyboard-drafts-sidebar"]', in_timeout=5):
            logger.info(f'账号: {bit_dict["name"]} 有草稿')
            self.element_click(driver, '//*[@id="__PWS_ROOT__"]/div/div[1]/div/div[2]/div/div/div/div[2]/div['
                                       '2]/div/div[2]/div/div/div/div', in_ms=3)
            self.set_goods_info(driver, '', bit_dict)

        # 有输入框
        if self.element_locate(driver, '//*[text()="Upload assets to create Pins"]', in_expression_type='xpath',
                               in_timeout=5):
            logger.info(f'账号: {bit_dict["name"]} 有输入框')
            create_clicks = driver.find_elements(By.XPATH, '//*[text()="Create new"]')
            for create_click in create_clicks:
                try:
                    create_click.click()
                except Exception as f:
                    pass

            result = self.get_good_info(bit_dict)
            if result is not False:
                self.set_goods_info(driver, result, bit_dict)
            # else:
            #     requests.get(close_url)

        # 没有输入框, 没有草稿, 点击新建
        else:
            try:
                logger.info(f'账号: {bit_dict["name"]} 没有输入框, 没有草稿, 点击新建')
                create_clicks = driver.find_elements(By.XPATH, '//*[text()="Create new"]')
                for create_click in create_clicks:
                    try:
                        create_click.click()
                    except Exception as f:
                        pass

                result = self.get_good_info(bit_dict)
                if result is not False:
                    self.set_goods_info(driver, result, bit_dict)

            except Exception as f:
                result = self.get_good_info(bit_dict)
                print(result)
                if result is not False:
                    self.set_goods_info(driver, result, bit_dict)
                else:
                    pass

    def upload_pin_goods(self, driver, bit_dict):
        print(bit_dict)
        driver.get('https://www.pinterest.com/pin-builder/')
        # 有输入框
        if self.element_exists_and_clickable(driver, By.XPATH, '//input[@aria-label="File upload"]', wait_time=10,
                                             click_element=False,
                                             pause_time=2,
                                             raise_exception=False):

            logger.info(f'账号: {bit_dict["name"]} 有输入框')
            result = self.get_good_info(bit_dict)
            if result is not False:
                self.set_goods_info(driver, result, bit_dict)

    def main(self, bit_dict, index):
        Loguru(f"logs/{time.strftime('%Y-%m-%d')}/pinterest_{bit_dict['name']}.log")
        try:
            res = openBrowser(bit_dict['user_id'])
            # selenium 连接代码
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_experimental_option("debuggerAddress", res['data']['http'])
            chrome_service = Service(res['data']['driver'])
            driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
            driver.maximize_window()
            # 获取流行标签
            # self.get_trends_tag(driver)
            # 获取用户信息
            # self.get_user_info(driver, ads_dict)
            # 上传点子图
            for i in range(int(self.cf.get('bit', 'upload_num'))):
                if self.cf.get('ads', 'mode') == 'idea':
                    self.upload_idea_goods(driver, bit_dict)
                elif self.cf.get('ads', 'mode') == 'pin':
                    self.upload_pin_goods(driver, bit_dict)

            close_url = f'{url}/browser/close'
            data = {
                'id': bit_dict['user_id']
            }
            time.sleep(5)
            requests.post(close_url, data=data)

        except Exception as f:
            print(f)
            close_url = f'{url}/browser/close'
            data = {
                'id': bit_dict['user_id']
            }
            time.sleep(5)
            requests.post(close_url, data=data)
            logger.exception(f"账号: {bit_dict['name']}  发生异常...")

    def run(self):
        asd_dict_list = []
        res = requests.post(f"http://127.0.0.1:54345/browser/list",
                            data=json.dumps({'page': 0, 'pageSize': 1000}),
                            headers={'Content-Type': 'application/json'}).json()

        group_lists = res['data']['list']
        for group_info in group_lists:
            if 'groupName' in group_info and group_info['groupName'] == self.cf.get('bit', 'group_name'):
                window_name = group_info['name']
                user_id = group_info['id']
                asd_dict_list.append({'user_id': user_id, 'name': window_name})

        if len(asd_dict_list) > 0:
            pool_num = 2
            p = Pool(pool_num)
            for index, bit_dict in enumerate(asd_dict_list):
                print(bit_dict)
                if self.cf.get('bit', 'only_id') and bit_dict['user_id'] == self.cf.get('bit', 'only_id'):
                    p.apply_async(func=self.main, args=(bit_dict, index * 1))
                elif not self.cf.get('bit', 'only_id'):
                    p.apply_async(func=self.main, args=(bit_dict, index * 1))

            p.close()
            p.join()

        else:
            logger.warning(f"此分组没有id")


if __name__ == '__main__':
    Pinterest().run()
