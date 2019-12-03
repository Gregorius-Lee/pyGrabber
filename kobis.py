# KOBIS 박스오피스 검색
import configparser
import requests
import bs4
import pandas as pd
import collections
import re
import os.path
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementNotVisibleException
import logging
import string
import datetime
import time
from gspreadapi import gspreadDocApi

class kobisCrawler:
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
        basic_url = 'http://www.kobis.or.kr/kobis/business/stat/boxs/findWeeklylyBoxOfficeList.do'

        driver.get(basic_url)

        time.sleep(5)

        # startDate = datetime.datetime.strptime('201945-1', '%Y%W-%w')
        endDate = startDate + datetime.timedelta(days=6)

        self.set_search_option(driver, startDate, endDate)

        time.sleep(5)

        more_btn = driver.find_element_by_class_name('more')
        more_btn.click()

        results = self.read_table(driver, startDate, endDate)

        return results

    def get_monthlyRank(self, driver, targetMonth):
        basic_url = 'http://www.kobis.or.kr/kobis/business/stat/boxs/findMonthlyBoxOfficeList.do'

        driver.get(basic_url)

        time.sleep(5)

        self.set_monthly_search_option(driver, targetMonth)

        time.sleep(5)

        more_btn = driver.find_element_by_class_name('more')
        more_btn.click()

        results = self.read_table(driver, targetMonth=targetMonth)

        return results

    def set_search_option(self, driver, startDate, endDate):
        start = driver.find_element_by_id('sSearchFrom')
        start.click()

        year_selector = driver.find_element_by_class_name('ui-datepicker-year')
        year_selector.click()
        year_selector.find_element_by_xpath("//option[@value='" + str(startDate.year) + "']").click()

        month_selector = driver.find_element_by_class_name('ui-datepicker-month')
        month_selector.click()
        month_selector.find_element_by_xpath("//option[@value='" + str(startDate.month - 1) + "']").click()  # -1 적용 필요함

        day_selector = driver.find_elements_by_class_name('ui-state-default')
        day_selector[startDate.day - 1].click()  # -1 적용 필요함

        end = driver.find_element_by_id('sSearchTo')
        end.click()

        year_selector = driver.find_element_by_class_name('ui-datepicker-year')
        year_selector.click()
        year_selector.find_element_by_xpath("//option[@value='" + str(endDate.year) + "']").click()

        month_selector = driver.find_element_by_class_name('ui-datepicker-month')
        month_selector.click()
        month_selector.find_element_by_xpath("//option[@value='" + str(endDate.month - 1) + "']").click()  # -1 적용 필요함

        day_selector = driver.find_elements_by_class_name('ui-state-default')
        day_selector[endDate.day - 1].click()  # -1 적용 필요함

        week_selector = driver.find_element_by_id('sWeekGb')
        week_selector.click()

        week_selector.find_element_by_xpath("//option[@value='" + str(0) + "']").click()  # 0: 주간, 1: 주말, 2: 주중

        search_btn = driver.find_element_by_class_name('btn_blue')
        search_btn.click()

    def set_monthly_search_option(self, driver, targetMonth):
        year_selector = driver.find_element_by_id('sSearchYearFrom')
        year_selector.click()
        year_selector.find_element_by_xpath("descendant::option[@value='" + str(targetMonth.year) + "']").click()

        month_selector = driver.find_element_by_id('sSearchMonthFrom')
        month_selector.click()
        month_selector.find_element_by_xpath("descendant::option[@value='" + str(targetMonth.month) + "']").click()
        time.sleep(1.5)
        end_year_selector = driver.find_element_by_id('sSearchYearTo')
        end_year_selector.click()
        end_year_selector.find_element_by_xpath("descendant::option[@value='" + str(targetMonth.year) + "']").click()

        end_month_selector = driver.find_element_by_id('sSearchMonthTo')
        end_month_selector.click()
        end_month_selector.find_element_by_xpath("descendant::option[@value='" + str(targetMonth.month) + "']").click()

        search_btn = driver.find_element_by_class_name('btn_blue')
        search_btn.click()

    def read_table(self, driver, startDate = None, endDate = None, targetMonth = None):
        # [startDate, endDate, movie_name, rank, rank_lastweek, openDate, poster, country]
        if targetMonth == None:
            startDate = str(startDate.year) + '-' + str(startDate.month) + '-' + str(startDate.day)
            endDate = str(endDate.year) + '-' + str(endDate.month) + '-' + str(endDate.day)
        else:
            startDate = targetMonth.year + '-' + targetMonth.month
            endDate = targetMonth.year + '-' + targetMonth.month

        rows = driver.find_elements_by_xpath("//*[@id='tbody_0']/tr")

        results = []

        for row in rows:
            row_items = row.find_elements_by_tag_name('td')

            movie_name = row_items[1].find_element_by_tag_name('a').get_attribute('title')
            rank = row_items[0].get_attribute('title')
            # 매출액
            sales = int(row_items[3].text.replace(',', '').strip())
            # 매출액 점유율
            sales_rate = float(row_items[4].text.replace('%', '').strip())
            # 누적매출액
            sales_total = int(row_items[5].text.replace(',', '').strip())
            # 관객수
            seats = int(row_items[6].text.replace(',', '').strip())
            # 누적관객수
            seats_total = int(row_items[7].text.replace(',', '').strip())
            # 스크린수
            screen = int(row_items[8].text.replace(',', '').strip())
            # 상영횟수
            play_num = int(row_items[9].text.replace(',', '').strip())

            # 영화 상세창 열기
            row_items[1].find_element_by_tag_name('a').click()
            time.sleep(2)
            poster = driver.find_element_by_class_name('thumb').get_attribute('href')
            country = driver.find_element_by_xpath("//div[2]/div/div[1]/div[2]/dl/dd[4]").text.split('|')[-1].strip()
            driver.find_element_by_xpath("//*[@class='close']").click()  # 상세창 닫기

            main_country = country.split(',')[0].strip()
            openDate = row_items[2].text

            # 이전 랭킹 검색
            year = int(targetMonth.year)
            last_month = int(targetMonth.month)-1
            if last_month == 0:
                file_name = 'resources/kobis-%s-%s.csv' % (str(year-1), str(12))
            else:
                file_name = 'resources/kobis-%s-%s.csv' % (str(year), str(last_month).zfill(2))

            if os.path.exists(file_name):
                last_df = pd.read_csv(file_name, index_col=0)
                same_item_row = last_df[last_df['movie_name'] == movie_name]

                if len(same_item_row) == 0:
                    rank_lastweek = 21
                else:
                    rank_lastweek = same_item_row['rank'].values[0]
            else:
                rank_lastweek = 0

            culture_office = (21-int(rank))*(20 if int(rank_lastweek) > 20 else int(rank_lastweek)/int(rank))

            if targetMonth == None:
                results.append([startDate, endDate, rank, rank_lastweek, culture_office, movie_name, rank, poster, openDate, sales, sales_rate, sales_total, seats, seats_total, screen, play_num, main_country, country])
            else:
                results.append(
                    [startDate, rank, rank_lastweek, culture_office, movie_name, rank, poster, openDate, sales,
                     sales_rate, sales_total, seats, seats_total, screen, play_num, main_country, country])

        return results

class TargetMonth:
    def __init__(self, year, month):
        self.year = year
        self.month = month

if __name__ == "__main__":
    '''crawler = kobisCrawler()
    driver = crawler.get_driver()
    month_set = ['03', '04', '05', '06', '07', '08', '09', '10', '11']
    try:
        for month in month_set:
            targetMonth = TargetMonth('2019', month)
            results = crawler.get_monthlyRank(driver, targetMonth=targetMonth)
            df = pd.DataFrame(results,
                              columns=['startDate', 'rank', 'rank_lastweek', 'culture_office', 'movie_name', 'rank', 'poster',
                                       'openDate', 'sales',
                                       'sales_rate', 'sales_total', 'seats', 'seats_total', 'screen', 'play_num',
                                       'main_country', 'country'])

            file_name = 'resources/kobis-%s-%s.csv'%(targetMonth.year, targetMonth.month)
            df.to_csv(file_name, encoding='utf-8-sig')
    except Exception as e:
        print(e)
    finally:
        driver.quit()'''
    google_spread = gspreadDocApi()

    df = pd.read_csv('resources/kobis-total.csv', index_col=0)

    data = []

    for index, row in df.iterrows():
        data.append(row.tolist())

    json_file_name = 'config/myculturelife-4b07b1c269c8.json'
    spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1dE8WJBij6NQ3qav3dFuyDehIjYZjwirohmpUs0TeK78/edit#gid=12416882'
    startIndex = 'KOBIS_월간!A2'

    google_spread.appendData(json_file_name, spreadsheet_url, startIndex, data)
