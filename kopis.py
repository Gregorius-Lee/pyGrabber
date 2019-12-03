# KOPIS 예매상황판 검색
import configparser
import logging
import os

import requests
import bs4
import pandas as pd
import collections
import re
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementNotVisibleException
import time
import string
import datetime

from gspreadapi import gspreadDocApi


class kopisCrawler:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('config/config.ini')
        self.delay = 0

        # logger 설정
        # logger 생성
        self.logger = logging.getLogger('kobisCrawler_log')
        self.logger.setLevel(logging.DEBUG)

        # 로그 포멧팅 설정
        fommater = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # 스트림 핸들러 생성
        streamHandler = logging.StreamHandler()
        streamHandler.setLevel(logging.DEBUG)
        streamHandler.setFormatter(fommater)

        # 핸들러 등록
        self.logger.addHandler(streamHandler)

    def get_driver(self):
        # webdriver 설정
        options = webdriver.ChromeOptions()

        # headless 옵션 설정
        # options.add_argument('headless')
        # options.add_argument("no-sandbox")

        # 브라우저 윈도우 사이즈
        options.add_argument('window-size=1920x1080')

        # 사람처럼 보이게 하는 옵션들
        options.add_argument("disable-gpu")   # 가속 사용 x
        options.add_argument("lang=ko_KR")    # 가짜 플러그인 탑재
        options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36')  # user-agent 이름 설정

        # 드라이버 위치 경로 입력
        driver = webdriver.Chrome('config/chromedriver', options=options)

        return driver

    def get_weeklyRank(self, driver, startDate, endDate):
        basic_url = 'http://www.kopis.or.kr/por/boxoffice/boxoffice.do?menuId=MNU_00024&searchWord=&searchType=total'

        driver.get(basic_url)

        startDate = datetime.datetime.strptime('201946-1', '%Y%W-%w')
        endDate = startDate + datetime.timedelta(days=6)

        results = self.get_kopis_rank(driver, startDate, endDate)
        results_lastweek = self.get_kopis_rank(startDate - datetime.timedelta(weeks=1), endDate - datetime.timedelta(weeks=1))

        return results, results_lastweek

    def get_monthlyRank(self, driver, targetMonth):
        basic_url = 'http://www.kopis.or.kr/por/boxoffice/boxoffice.do?menuId=MNU_00024&searchWord=&searchType=total'

        driver.get(basic_url)

        results = self.get_kopis_rank(driver, targetMonth=targetMonth)

        return results

    def get_kopis_rank(self, driver, startDate = None, endDate = None, targetMonth = None):
        category_selector = driver.find_element_by_xpath('//*[@id="su_con"]/div[1]/ul')
        tabs = category_selector.find_elements_by_tag_name('li')
        results = []

        if targetMonth == None:
            startDate = str(startDate.year) + '-' + str(startDate.month).zfill(2) + '-' + str(startDate.day).zfill(2)
            endDate = str(endDate.year) + '-' + str(endDate.month).zfill(2) + '-' + str(endDate.day).zfill(2)
        else:
            startDate = str(targetMonth.year) + '-' + str(targetMonth.month).zfill(2)

        tabs[0].click()
        time.sleep(1)

        playName = ''

        for i in range(1, len(tabs)):
            if i == 1:
                tabs[i].click()
                time.sleep(1.5)
                tabs[i].click()
                time.sleep(1.5)

                # 기간 설정
                duration_selector = driver.find_element_by_xpath('//*[@id="su_con"]/div[1]/div/div[2]/ul')
                duration_options = duration_selector.find_elements_by_tag_name('li')
                if targetMonth == None:
                    duration_options[1].click()  # 0: 일간, 1: 주간, 2: 월간, 3: 연간
                else:
                    duration_options[2].click()  # 0: 일간, 1: 주간, 2: 월간, 3: 연간

                if targetMonth == None:
                    startDate_picker = driver.find_element_by_xpath('//*[@id="startDate"]')
                    startDate_picker.clear()
                    startDate_picker.send_keys(startDate.replace('-', '.'))  # 시작일자 설정
                    startDate_picker.send_keys('\ue007')
                    startDate_picker.send_keys('\ue007')

                    endDate_picker = driver.find_element_by_xpath('//*[@id="endDate"]')
                    endDate_picker.clear()
                    endDate_picker.send_keys(endDate.replace('-', '.'))  # 시작일자 설정
                    endDate_picker.send_keys('\ue007')
                    startDate_picker.send_keys('\ue007')
                else:
                    startDate_picker = driver.find_element_by_xpath('//*[@id="startDate"]')
                    startDate_picker.clear()
                    startDate_picker.send_keys('%s.%s.%s' % (targetMonth.year, targetMonth.month, targetMonth.day))  # 시작일자 설정
                    startDate_picker.send_keys('\ue007')
                    startDate_picker.send_keys('\ue007')

            else:
                tabs[i].click()
                time.sleep(1.5)
                tabs[i].click()

            time.sleep(5)

            # 순위 크롤링
            ranking_area = driver.find_element_by_xpath('//*[@id="su_con"]/div[3]/ul')
            ranking_items = ranking_area.find_elements_by_tag_name('li')
            category = tabs[i].text.strip()

            for item in ranking_items:
                # [startDate, endDate, category, playName, rank, rank_lastweek, duration, place, poster, playId, link]
                playName = item.find_element_by_xpath('descendant::div/div/div[2]/h4/a').text.strip()
                rank = item.find_element_by_xpath('descendant::span[@class="num"]').text.strip()
                rank_lastweek = '0'  # 지난주 랭킹을 찾아오는 로직 필요
                duration = item.find_element_by_xpath('descendant::p[@class="dy"]').text.strip()
                place = item.find_element_by_xpath('descendant::p[@class="plc"]').text.strip()
                temp = item.find_element_by_xpath('descendant::div/div/div[1]/a')
                poster = temp.find_element_by_xpath('descendant::img').get_attribute('src')
                playId = temp.get_attribute('href')[23:31]
                link = 'http://www.kopis.or.kr/por/db/pblprfr/pblprfrView.do?menuId=MNU_00020&mt20Id=' + playId

                seats, shows, sub_category = self.get_detail_info(driver, link)

                # 이전 랭킹 검색
                year = int(targetMonth.year)
                last_month = int(targetMonth.month) - 1
                if last_month == 0:
                    file_name = 'resources/kopis-%s-%s.csv' % (str(year - 1), str(12))
                else:
                    file_name = 'resources/kopis-%s-%s.csv' % (str(year), str(last_month).zfill(2))

                if os.path.exists(file_name):
                    last_df = pd.read_csv(file_name, index_col=0)
                    same_item_row = last_df[last_df['playId'] == playId]

                    category_num = len(last_df[last_df['category'] == category])
                    if len(same_item_row) == 0:
                        rank_lastweek = category_num + 1
                    else:
                        rank_lastweek = same_item_row['rank'].values[0]

                    culture_office = (category_num - int(rank)) * (rank_lastweek - int(rank) + 1)
                else:
                    rank_lastweek = 0
                    culture_office = 0

                if targetMonth == None:
                    results.append(
                        [startDate, endDate, category, sub_category, playName, culture_office, rank, rank_lastweek, duration, place, seats,
                         shows, poster, playId])
                else:
                    results.append(
                        [startDate, category, sub_category, playName, culture_office, rank, rank_lastweek, duration, place,
                         seats,
                         shows, poster, playId])

        return results

    def get_detail_info(self, driver, link):
        script = "window.open('%s')" % link
        driver.execute_script(script)
        driver.switch_to_window(driver.window_handles[1])

        driver.find_element_by_xpath('//*[@id="perf"]').click()
        seats = driver.find_element_by_xpath('//*[@id="su_con"]/div[5]/ul/li[2]/div/dl/dd').text.replace(',', '').replace('편', '')  # 좌석수

        driver.find_element_by_xpath('//*[@id="stats"]').click()
        shows = driver.find_element_by_xpath('//*[@id="stats_data5"]').text.replace(',', '')  # 상영횟수
        sub_category = driver.find_element_by_xpath('//*[@id="su_con"]/div[1]/div[1]/span').text.strip()

        driver.close()
        driver.switch_to_window(driver.window_handles[0])

        return seats, shows, sub_category

class TargetMonth:
    def __init__(self, year, month):
        self.year = year
        self.month = month
        self.day = '1'

if __name__ == "__main__":
    '''crawler = kopisCrawler()
    driver = crawler.get_driver()
    month_set = ['01'] #, '02', '03', '04', '05', '06', '07', '08', '09', '10', '11']
    try:
        for month in month_set:
            targetMonth = TargetMonth('2019', month)
            results = crawler.get_monthlyRank(driver, targetMonth=targetMonth)
            df = pd.DataFrame(results,
                              columns=['startDate', 'category', 'sub_category', 'playName', 'culture_office', 'rank', 'rank_lastweek', 'duration', 'place',
                                       'seats', 'shows', 'poster', 'playId'])

            file_name = 'resources/kopis-%s-%s.csv'%(targetMonth.year, targetMonth.month)
            df.to_csv(file_name, encoding='utf-8-sig')
    except Exception as e:
        print(e)
    finally:
        driver.quit()'''
    google_spread = gspreadDocApi()

    df = pd.read_csv('resources/kopis-2019-01.csv', index_col=0)

    data = []

    for index, row in df.iterrows():
        data.append(row.tolist())

    json_file_name = 'config/myculturelife-4b07b1c269c8.json'
    spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1aUkN8Dg4pdA6ex50Fr4xCfisjBIWj8F-PFHRPoLAMVc/edit#gid=1842400863'
    startIndex = 'KOPIS_월간!A2'

    google_spread.appendData(json_file_name, spreadsheet_url, startIndex, data)