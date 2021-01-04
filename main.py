# -*- coding: utf-8 -*-
import json
import platform
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
import threading

SLEEP_TIME = 60
# 通过第一次运行生成的screenshot.png截图 手动获取验证码的位置(左，顶，右，底)
VERIFY_CODE_LOCATION = (702, 785, 900, 877)


class Student:
    def __init__(self, username, password, name, fangtang):
        self.username = username
        self.password = password
        self.name = name
        self.fangtang = fangtang


class course:
    def __init__(self, name, score):
        self._name = name
        self._score = score

    def __str__(self):
        return self._name + ":" + self._score


class YjsWebsite:

    def __init__(self, student):
        self._student = student
        self._driver = webdriver.Chrome()
        self._driver.minimize_window()
        self._cookies = None
        self.course_name_list = []

    def get_cookie(self):
        logging.info("[%s]:Start to get cookie", self._student.username)

        self._login_success = False
        while not self._login_success:
            self.login()
            try:
                WebDriverWait(self._driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div/div[1]/div[1]/img')))
                self._login_success = True
            except:
                logging.warning("[%s]:Error login due to wrong verify code", self._student.username)
        self._cookies = self._driver.get_cookies()
        self._SINDEXCOOKIE = self._cookies[0]["value"]
        self._ASP_NET_SessionId = self._cookies[2]["value"]
        logging.info("[%s]:Get cookie success __SINDEXCOOKIE__:%s; ASP.NET_SessionId:%s;", self._student.username,
                     self._SINDEXCOOKIE,
                     self._ASP_NET_SessionId)

    def login(self):
        logging.info("[%s]:Start to login by selenium", self._student.username)
        self._driver.get("http://yjss.hhu.edu.cn/gmis/home/stulogin")

        img_verify_locator = (By.XPATH, '//*[@id="imgVerifi"]')
        WebDriverWait(self._driver, 1).until(EC.visibility_of_element_located(img_verify_locator))

        self._driver.find_element_by_xpath('//*[@id="UserId"]').send_keys(self._student.username)
        self._driver.find_element_by_xpath('//*[@id="Password"]').send_keys(self._student.password)
        self._driver.get_screenshot_as_file('screenshot.png')

        im = Image.open('screenshot.png')
        im = im.crop(VERIFY_CODE_LOCATION)
        verify_code = identify_verify_code(im)

        self._driver.find_element_by_xpath('//*[@id="VeriCode"]').send_keys(verify_code)
        self._driver.find_element_by_xpath('//*[@id="ff"]/div/div[1]/div[5]/button').click()

    def quit(self):
        self._driver.quit()

    def check_score(self):
        while self._cookies == None:
            self.get_cookie()
        logging.info("[%s]:Start to check score", self._student.username)

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
            # logging.info("[%s]:Return json info %s", self._student.username,
            #              str(json.loads(requests.get(url=url, headers=headers).text)))
            scores = json.loads(requests.get(url=url, headers=headers).text)['cj']
            for score in scores:
                if score['cj'] != "无" and score['kcmc'] not in self.course_name_list:
                    self.course_name_list.append(score['kcmc'])
                    logging.info("[%s]:Query new course", self._student.username)
                    send2wx(self._student.name + str(course(score['kcmc'], score['cj'])),
                            self._student.name + str(course(score['kcmc'], score['cj'])))
                    new_score_flag = True
            if not new_score_flag:
                logging.info("[%s]:None new course", self._student.username)
        except Exception as e:
            logging.error("[%s]:Cookie lose effectiveness", self._student.username)
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


def send2wx(text, msg, fangtang):
    url = "https://sc.ftqq.com/" + fangtang + ".send?text=" + text + "&desp=" + msg
    res_text = requests.get(url=url).text
    res = json.loads(res_text)
    if res['errmsg'] == "success":
        logging.info(":Send to weixin success!")
    else:
        logging.error(":Send to weixin error, try again after 2 seconds:" + res_text)
        time.sleep(2)
        send2wx("Re:" + text, msg, fangtang)


def loop_check_score(student):
    yjs_website = YjsWebsite(student)
    while True:
        yjs_website.check_score()
        time.sleep(SLEEP_TIME)
        logging.info("[System]:Start to sleep %d seconds", SLEEP_TIME)
    yjs_website.quit()


def loop_check_thread_alive():
    while True:
        for student in students:
            if not student[1].isAlive():
                thread = threading.Thread(target=loop_check_score, args=(student,))
                thread.start()
                student[1] = thread
                logging.warning("[Check Alive Thread]:%s loss, restart success", str(student[0]))

        logging.info("[Check Alive Thread]:Start to  check threads")
        time.sleep(SLEEP_TIME)


if platform.system() == "Windows":
    # pytesseract exe文件目录 用于识别二维码
    pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - [%(funcName)s] - %(levelname)s- %(message)s')  # logging.basic
# Student(学号，密码，姓名，Server酱 Sckey 用于推送微信)
students = [[Student("20162001xxxx", "xxxxx", 'xx',"xxx"), None]]

for student in students:
    thread = threading.Thread(target=loop_check_score, args=(student[0],))
    thread.start()
    student[1] = thread
check_alive_thread = threading.Thread(target=loop_check_thread_alive, args=())
check_alive_thread.start()
