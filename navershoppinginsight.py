import numpy as np
import pandas as pd
import urllib
from urllib import request
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import json
import time
import datetime
import os.path
import configparser
import logging

class naverCrawler:
    def __init__(self):
        '''
            카테고리별 코드
        '''
        self.codeset = {"뮤지컬": "50001690", "콘서트": "50001691", "연극": "50001692", "전시/행사": "50001693", "클래식": "50001694",
                        "오페라": "50001695", "발레/무용": "50001696", "국악/전통예술": "50001697", "스포츠": "50005310",
                        "국내여행": "50001644",
                        "국내숙박": "50001646", "체험": "50006869", "강좌": "50001652", "구기스포츠": "50007193",
                        "아웃도어스포츠": "50007195"}

        self.config = configparser.ConfigParser()
        self.config.read('config/config.ini')
        self.delay = 0

        # logger 설정
        # logger 생성
        self.logger = logging.getLogger('naverCrawler_log')
        self.logger.setLevel(logging.DEBUG)

        # 로그 포멧팅 설정
        fommater = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # 스트림 핸들러 생성
        streamHandler = logging.StreamHandler()
        streamHandler.setLevel(logging.DEBUG)
        streamHandler.setFormatter(fommater)

        # 핸들러 등록
        self.logger.addHandler(streamHandler)

    def get_rank(self, startDate, endDate):
        '''
        This class is to crawl Top 20 rank info for the Naver Shoppinginsight.
        Atfer crawling the info, the info is stored into a csv file.
        if the crawling is not finished by any causes, then
        :param startDate:
        :param endDate:
        :return:
        '''

        error_code = None
        try:
            # Selenium 드라이버 획득
            driver = self.get_driver()
            self.logger.info('Get Selenium Driver: %s' % driver.session_id)

            basic_url = 'https://datalab.naver.com/shoppingInsight/sCategory.naver'

            driver.get(basic_url)

            # 검색 기간 먼저 설정
            list = driver.find_elements_by_class_name("select")

            '''
            list[0] : 분야 1
            list[1] : 분야 2
            list[2] : 기간 (일간/주간/월간)
            list[3, 4, 5] : 시작일자 (년/월/일)
            list[6, 7, 8] : 종료일자 (년/월/일)
            '''
            # 일간 선택
            list[2].click()
            list[2].find_elements_by_tag_name('li')[0].click()

            if startDate == datetime.datetime.strptime('201731-1', '%Y%W-%w'):
                startDate += datetime.timedelta(days=1)

            # 시작일자 선택
            self.select_date_li(startDate.year, list[3])
            self.select_date_li(startDate.month, list[4])
            self.select_date_li(startDate.day, list[5])

            # 종료일자 선택
            self.select_date_li(endDate.year, list[6])
            self.select_date_li(endDate.month, list[7])
            self.select_date_li(endDate.day, list[8])

            category = pd.DataFrame(
                np.array([['여행/문화', '공연/티켓', '뮤지컬', '50001690'], ['여행/문화', '공연/티켓', '콘서트', '50001691'],
                          ['여행/문화', '공연/티켓', '연극', '50001692'],
                          ['여행/문화', '공연/티켓', '전시/행사', '50001693'],
                          ['여행/문화', '공연/티켓', '클래식', '50001694'], ['여행/문화', '공연/티켓', '오페라', '50001695'],
                          ['여행/문화', '공연/티켓', '발레/무용', '50001696'],
                          ['여행/문화', '공연/티켓', '국악/전통예술', '50001697'],
                          ['여행/문화', '공연/티켓', '스포츠', '50005310'],
                          ['여행/문화', '여행/항공권', '국내여행', '50001644'],
                          ['여행/문화', '여행/항공권', '국내숙박', '50001646'], ['여행/문화', '레저이용권', '체험', '50006869'],
                          ['여행/문화', 'e컨텐츠', '강좌', '50001652'],
                          ['여행/문화', '스포츠/음악/미술 레슨', '구기스포츠', '50007193'],
                          ['여행/문화', '스포츠/음악/미술 레슨', '아웃도어스포츠', '50007195']]),
                columns=['분류1', '분류2', '분류3', '코드'])

            if stoppoint is not None:
                start_index = category[category['분류3'] == stoppoint.iloc[0]['category']].index.values[0]
                category = category[start_index:]
            else:
                weekly_ranking = []

            # 분야 선택
            for target in category.values:
                # 분야 1을 선정하는 단계
                list[0].click()
                items = list[0].find_elements_by_tag_name('li')

                if len(items) != 0:
                    for item in items:
                        if item.find_element_by_tag_name('a').text == target[0]:
                            item.click()  # 분야 1 선택
                            break
                        else:
                            pass
                    time.sleep(0.5)
                else:
                    raise TrafficOverError()

                # 분야 2를 선정하는 단계
                list[1].click()
                items = list[1].find_elements_by_tag_name('li')

                if len(items) != 0:
                    for item in items:
                        if item.find_element_by_tag_name('a').text == target[1]:
                            item.click()  # 분야 2 선택
                            break
                        else:
                            pass
                    time.sleep(0.5)
                else:
                    raise TrafficOverError()
                # 분야 3을 선정하는 단계
                '''
                분야 3 선택 리스트 생성에 따른 select 리스트 다시 읽기
                list[2] : 분야 3으로 추가
                '''
                list = driver.find_elements_by_class_name("select")
                list[2].click()
                items = list[2].find_elements_by_tag_name('li')

                if len(items) != 0:
                    for item in items:
                        if item.find_element_by_tag_name('a').text == target[2]:
                            item.click()  # 분야 3 선택
                            break
                        else:
                            pass
                    time.sleep(0.5)
                else:
                    raise TrafficOverError()
                # 성별 / 연령 셋팅
                '''
                [1] : gender {0: 전체, 1: 여성, 2: 남성}
                [2] : age {0: 전체, 1: 10대, 2: 20대, 3: 30대, 4: 40대, 5: 50대, 6: 60대}
                '''
                gender_age_option = driver.find_elements_by_class_name('set_chk')
                gender_option = gender_age_option[1].find_elements_by_xpath('descendant::span')
                age_option = gender_age_option[2].find_elements_by_xpath('descendant::span')

                gender_checker = True
                rank_last = []
                for gender in gender_option:
                    # gender 선택
                    if stoppoint is not None:
                        loop_checker = True

                        if stoppoint.iloc[0]['gender'] == gender.text:
                            gender.click()

                            last_age_check = True
                            for age in age_option:

                                if stoppoint.iloc[0]['age'] == 60:
                                    stoppoint = None
                                    break
                                elif (age.text[:2] not in str(stoppoint.iloc[0]['age'])) & loop_checker:
                                    pass
                                else:
                                    if last_age_check:
                                        last_age_check = False
                                        pass
                                    else:
                                        # age 선택
                                        age.click()

                                        time.sleep(0.5)
                                        # 조회버튼 클릭
                                        search_btn = driver.find_element_by_class_name('btn_submit')
                                        search_btn.click()
                                        time.sleep(0.5)

                                        result = self.get_rank_list(driver, startDate, endDate, gender.text,
                                                                    age.text[:2], target[2])

                                        # age 선택 해제
                                        age.click()

                                        '''if (gender.text == '전체') & (age.text == '전체') & (result == []):
                                            gender_checker = False
                                            break'''

                                        result_df = pd.DataFrame(result,
                                                                 columns=['startDate', 'endDate', 'category', 'gender',
                                                                          'age', 'rank', 'lastweekRank', 'keyword'])
                                        result_set = [x for x in result_df['keyword'].values.tolist() if
                                                      x not in set(rank_last)]
                                        if result_set == []:
                                            print('트래픽 초과 오류 발생')
                                            raise TrafficOverError('랭크 결과과 비었음')
                                        else:
                                            rank_last = result_df

                                        loop_checker = False

                                        weekly_ranking += result
                            gender.click()
                            stoppoint = None
                        else:
                            pass
                    # elif gender_checker == False:
                    # break
                    else:
                        gender.click()
                        for age in age_option:
                            # age 선택
                            age.click()

                            time.sleep(0.5)
                            # 조회버튼 클릭
                            search_btn = driver.find_element_by_class_name('btn_submit')
                            search_btn.click()
                            time.sleep(0.5)

                            result = self.get_rank_list(driver, startDate, endDate, gender.text, age.text[:2],
                                                        target[2])

                            # age 선택 해제
                            age.click()

                            '''if (gender.text == '전체') & (age.text == '전체') & (result == []):
                                gender_checker = False
                                break'''

                            result_df = pd.DataFrame(result,
                                                     columns=['startDate', 'endDate', 'category', 'gender', 'age',
                                                              'rank',
                                                              'lastweekRank', 'keyword'])
                            result_set = [x for x in result_df['keyword'].values.tolist() if x not in set(rank_last)]

                            if result_set == []:
                                print('트래픽 초과 오류 발생')
                                raise TrafficOverError
                            else:
                                rank_last = result
                            weekly_ranking += result

                        # gender 선택 해제
                        gender.click()
        except DateSettingError as e:
            self.logger.error(e)

        except:
            print("Error occurs")
            error_code = 'Error'
            return weekly_ranking, error_code
        finally:
            driver.quit()
            print('%d-%d-%d, 주간 인기순위 수집 종료' % (startDate.year, startDate.month, startDate.day))
            return weekly_ranking, error_code

    def get_driver(self):
        # webdriver 설정
        options = webdriver.ChromeOptions()

        # headless 옵션 설정
        # options.add_argument('headless')
        # options.add_argument("no-sandbox")

        # 브라우저 윈도우 사이즈
        options.add_argument('window-size=1920x1080')

        # 사람처럼 보이게 하는 옵션들
        options.add_argument("disable-gpu")  # 가속 사용 x
        options.add_argument("lang=ko_KR")  # 가짜 플러그인 탑재
        options.add_argument(
            'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36')  # user-agent 이름 설정

        # 드라이버 위치 경로 입력
        driver = webdriver.Chrome(r'config/chromedriver', options=options)

        return driver

    def select_date_li(self, date, li):
        selected = False

        # 시기 설정 영역 클릭
        li.click()

        # 대상 일시와 동일한 영역 클릭
        target = li.find_elements_by_tag_name('li')
        for item in target:
            if item.text == str(date).zfill(2):
                item.click()
                selected = True
                break
            elif item.text == target[-1].text:
                target[0].click()
                selected = True
                break

        if selected:
            raise DateSettingError()



class TrafficOverError(Exception):
    def __init__(self):
        super().__init__("트래픽 과다에 대한 오류 발생")

class DateSettingError(Exception):
    def __init__(self):
        super().__init__("검색일자 선택에 대한 오류 발생")