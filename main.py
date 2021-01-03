import json
import re
import time
import requests
import pytesseract
from PIL import Image
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import logging

USERNAME = "201620010022"
PASSWORD = "zhiyou123."


class student:
    def __init__(self, username, password, name):
        self.username = username
        self.password = password
        self.name = name


class course:
    def __init__(self, name, score):
        self._name = name
        self._score = score

    def __str__(self):
        return self._name + ":" + self._score


class YjsWebsite:

    def __init__(self, username, password):
        self._username = username
        self._password = password
        self._driver = webdriver.Chrome()
        self._driver.minimize_window()
        self._cookies = None
        self.course_name_list = []

    def get_cookie(self):
        logging.info("[%s]:Start to get cookie", self._username)

        self._login_success = False
        while not self._login_success:
            self.login()
            try:
                WebDriverWait(self._driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div/div[1]/div[1]/img')))
                self._login_success = True
            except:
                logging.warning("[%s]:Error login due to wrong verify code", self._username)
        self._cookies = self._driver.get_cookies()
        self._SINDEXCOOKIE = self._cookies[0]["value"]
        self._ASP_NET_SessionId = self._cookies[2]["value"]
        logging.info("[%s]:Get cookie success __SINDEXCOOKIE__:%s; ASP.NET_SessionId:%s;", self._username,
                     self._SINDEXCOOKIE,
                     self._ASP_NET_SessionId)

    def login(self):
        logging.info("[%s]:Start to login by selenium", self._username)
        self._driver.get("http://yjss.hhu.edu.cn/gmis/home/stulogin")

        img_verify_locator = (By.XPATH, '//*[@id="imgVerifi"]')
        WebDriverWait(self._driver, 1).until(EC.visibility_of_element_located(img_verify_locator))

        self._driver.find_element_by_xpath('//*[@id="UserId"]').send_keys(USERNAME)
        self._driver.find_element_by_xpath('//*[@id="Password"]').send_keys(PASSWORD)
        self._driver.get_screenshot_as_file('screenshot.png')

        im = Image.open('screenshot.png')
        im = im.crop((702, 785, 900, 877))
        verify_code = identify_verify_code(im)

        self._driver.find_element_by_xpath('//*[@id="VeriCode"]').send_keys(verify_code)
        self._driver.find_element_by_xpath('//*[@id="ff"]/div/div[1]/div[5]/button').click()

    def quit(self):
        self._driver.quit()

    def check_score(self):
        logging.info("[%s]:Start to check score", self._username)
        while self._cookies == None:
            self.get_cookie()
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_0_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
            "Cookie": ".ASPXAUTH=616DDDD143E457FBB177243539A3FE9F56A57CD70D5D4E6871971442CD1F6003760DBA8895EF5EFE3EE9C0A3A8DC9FE2FA2F742441AD0B7F1A2B1A7D1FCFFD7EAF67DF37C540F14F7F80BBD1AF333B582ACC1FC3BCC6248A4F8ACA79DD992C28C422A2114AD47A8C2008E9CEF1B3DD0A8DEE074801075342DE113A3F68D0367D5447DFC20C46158E35F6954B16EBCDDE981E20727B67A41FD193A9DF520958AD593FFA373E01B2DED41D9E6F98AC8CAC73C06AB3CC2FE811A3CC5CBECB30EF43BE21A096F874DB3F2D1A81240C115A00; "
                      "__SINDEXCOOKIE__=" + self._SINDEXCOOKIE + "; "
                                                                 "ASP.NET_SessionId=" + self._ASP_NET_SessionId + "; "
                                                                                                                  "__LOGINCOOKIE__="
        }
        url = 'http://yjss.hhu.edu.cn/gmis/student/pygl/cxhkbksq_list'
        new_score_flag = False
        try:
            logging.info("[%s]:Return json info %s", self._username,
                         str(json.loads(requests.get(url=url, headers=headers).text)))
            scores = json.loads(requests.get(url=url, headers=headers).text)['cj']
            for score in scores:
                if score['cj'] != "无" and score['kcmc'] not in self.course_name_list:
                    self.course_name_list.append(score['kcmc'])
                    logging.info("[%s]:Query new course %s", self._username,
                                 "李凡：" + str(course(score['kcmc'], score['cj'])))
                    send2wx("李凡：" + str(course(score['kcmc'], score['cj'])),
                            "李凡：" + str(course(score['kcmc'], score['cj'])))
                    new_score_flag = True
            if not new_score_flag:
                logging.info("[%s]:None new course")
        except Exception as e:
            logging.error("[%s]:Cookie lose effectiveness", self._username)
            self._cookies = None


def identify_verify_code(image):
    # image = Image.open("code.png")
    lim = image.convert('L')
    threshold = 150
    table = []
    for j in range(256):
        if j < threshold:
            table.append(0)
        else:
            table.append(1)
    bim = lim.point(table, '1')
    bim.save('code_threshold.png')
    # code =  pytesseract.image_to_string(bim)
    code = re.sub("\D", "", pytesseract.image_to_string(bim))
    return code


def send2wx(text, msg):
    url = "https://sc.ftqq.com/SCU142595Td1df92c3e6709f63b1f8fb38b3c581355fed676e8b478.send?text=" + text + "&desp=" + msg
    requests.get(url=url)


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - [%(funcName)s] - %(levelname)s- %(message)s')  # logging.basic
yjs_website = YjsWebsite(USERNAME, PASSWORD)
while True:
    yjs_website.check_score()
    time.sleep(60)
yjs_website.quit()

# # option = webdriver.ChromeOptions()
# # option.add_argument('headless')  # 设置option
# driver = webdriver.Chrome()
# driver.get("http://yjss.hhu.edu.cn/gmis/home/stulogin")
#
# img_verify_locator = (By.XPATH, '//*[@id="imgVerifi"]')
# WebDriverWait(driver, 1).until(EC.visibility_of_element_located(img_verify_locator))
#
# driver.find_element_by_xpath('//*[@id="UserId"]').send_keys(USERNAME)
# driver.find_element_by_xpath('//*[@id="Password"]').send_keys(PASSWORD)
# driver.get_screenshot_as_file('screenshot.png')
#
# im = Image.open('screenshot.png')
# im = im.crop((702, 785, 900, 877))
# # im.save('code.png')
# verify_code = identify_verify_code(im)
# driver.find_element_by_xpath('//*[@id="VeriCode"]').send_keys(verify_code)
# driver.find_element_by_xpath('//*[@id="ff"]/div/div[1]/div[5]/button').click()
#
# try:
#     element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="xslb"]')))
# except:
#     print("can't find that")
# finally:
#     driver.quit()
# # driver.quit()


# def check_score():
#     headers = {
#         "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_0_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
#         "Cookie": ".ASPXAUTH=616DDDD143E457FBB177243539A3FE9F56A57CD70D5D4E6871971442CD1F6003760DBA8895EF5EFE3EE9C0A3A8DC9FE2FA2F742441AD0B7F1A2B1A7D1FCFFD7EAF67DF37C540F14F7F80BBD1AF333B582ACC1FC3BCC6248A4F8ACA79DD992C28C422A2114AD47A8C2008E9CEF1B3DD0A8DEE074801075342DE113A3F68D0367D5447DFC20C46158E35F6954B16EBCDDE981E20727B67A41FD193A9DF520958AD593FFA373E01B2DED41D9E6F98AC8CAC73C06AB3CC2FE811A3CC5CBECB30EF43BE21A096F874DB3F2D1A81240C115A00; __SINDEXCOOKIE__=e9f308be3711df8208a453f3ca5e999c; ASP.NET_SessionId=zrxadadl3zh4o1hud4rerxa4; __LOGINCOOKIE__="
#
#     }
#     while True:
#         print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "开始查成绩")
#         url = 'http://yjss.hhu.edu.cn/gmis/student/pygl/cxhkbksq_list'
#         print(requests.get(url=url, headers=headers).text)
#
#         try:
#             print(json.loads(requests.get(url=url, headers=headers).text))
#             scores = json.loads(requests.get(url=url, headers=headers).text)['cj']
#             course_name_list = []
#
#             for score in scores:
#                 if score['cj'] != "无" and score['kcmc'] not in course_name_list:
#                     course_name_list.append(score['kcmc'])
#                     # send2wx("李凡：" + str(course(score['kcmc'], score['cj'])), str(course(score['kcmc'], score['cj'])))
#         except Exception as e:
#             # send2wx("爬虫挂了！", str(e))
#             exit()
#         # time.sleep(60)
