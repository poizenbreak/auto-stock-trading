import pandas as pd
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.common.exceptions import NoSuchWindowException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import os
import sys

from config.stockConfig import *
import socket
from selenium.webdriver.remote.command import Command
import traceback



class SeleniumDriverManager:

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            print("__new__ is called\n")
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # init 한번만 호출
        cls = type(self)

        if not hasattr(cls, "_init"):
            print("__init__ is called\n")
            cls._init = True

            self.driver = webdriver.Chrome('C:/Users/KDH/PycharmProjects/AutoStock/chromedriver')

    def getDriver(self):
        return self.driver

    def close(self):
        self.driver.quit()

    def reConnect(self):
        self.driver = webdriver.Chrome('C:/Users/KDH/PycharmProjects/AutoStock/chromedriver')

    def click(self, att):
        # 암묵적 대기
        self.driver.implicitly_wait(5)
        element = self.driver.find_element_by_xpath(att)
        # element.click()
        element.send_keys(Keys.ENTER)
        # self.driver.execute_script("arguments[0].click();",element)

    def getUrl(self, url):
        self.driver.get(url)

    def getStatus(self):
            try:
                self.driver.execute(Command.STATUS)
                return True
            except Exception as e:
                return False

class ScrapCore:
    def __init__(self):
        self.driver = SeleniumDriverManager().getDriver()

    def fetchOnCurrentUrl(self, WAIT_TYPE, PARSE_TYPE, att):
        """
            :param att:
            :param PARSE_TYPE:
            :param WAIT_TYPE:
            :param ticker: 종목코드
            :param
            :return:
            """

        html = None
        try:
            # 암묵적 대기
            if WAIT_TYPE == 'IMP':
                self.driver.implicitly_wait(5)
                if PARSE_TYPE == 'CLS':
                    elements = self.driver.find_elements_by_class_name(att)
                    html = []
                    for element in elements:
                        html.append(element.get_attribute('innerHTML'))
                elif PARSE_TYPE == 'XPATH':
                    elements = self.driver.find_elements_by_xpath(att)
                    html = []
                    for element in elements:
                        html.append(element.get_attribute('innerHTML'))

            # 명시적 대기
            if WAIT_TYPE == 'EXP':
                if PARSE_TYPE == 'TAG':
                    element = WebDriverWait(self.driver, timeout=5).until(
                        EC.presence_of_element_located((By.TAG_NAME, att)))
                    # print("text = ", element.text)
                    html = element.get_attribute('innerHTML')
                elif PARSE_TYPE == 'CLS':
                    element = WebDriverWait(self.driver, timeout=5).until(
                        EC.presence_of_element_located((By.CLASS_NAME, att)))
                    # print("text = ", element.text)
                    html = element.get_attribute('innerHTML')
        finally:
            # self.driver.quit()
            pass

        return html


class ScrapFnguideCore(ScrapCore):
    def __init__(self):
        self.driver = SeleniumDriverManager().getDriver()

    def fetch(self, url, WAIT_TYPE, PARSE_TYPE, att):

        """
            :param ticker: 종목코드
            :param gb: 데이터 종류 (0 : 재무제표, 1 : 재무비율, 2: 투자지표, 3:컨센서스 )
            :return:
            """

        html = None
        self.driver.get(url)
        time.sleep(0.3)
        try:
            # 암묵적 대기
            if WAIT_TYPE == 'IMP':
                self.driver.implicitly_wait(5)
                if PARSE_TYPE == 'CLS':
                    elements = self.driver.find_elements_by_class_name(att)
                    html = []
                    for element in elements:
                        html.append(element.get_attribute('innerHTML'))
                elif PARSE_TYPE == 'XPATH':
                    elements = self.driver.find_elements_by_xpath(att)
                    html = []
                    for element in elements:
                        html.append(element.get_attribute('innerHTML'))

            # 명시적 대기
            if WAIT_TYPE == 'EXP':
                if PARSE_TYPE == 'TAG':
                    element = WebDriverWait(self.driver, timeout=5).until(
                        EC.presence_of_element_located((By.TAG_NAME, att)))
                    # print("text = ", element.text)
                    html = element.get_attribute('innerHTML')
                elif PARSE_TYPE == 'CLS':
                    element = WebDriverWait(self.driver, timeout=5).until(
                        EC.presence_of_element_located((By.CLASS_NAME, att)))
                    # print("text = ", element.text)
                    html = element.get_attribute('innerHTML')
        finally:
            # self.driver.quit()
            pass

        return html


class ScrapNaverCore(ScrapCore):
    def __init__(self):
        self.driver = SeleniumDriverManager().getDriver()

    def fetch(self, url, WAIT_TYPE, PARSE_TYPE, att):
        """
            :param att:
            :param PARSE_TYPE:
            :param WAIT_TYPE:
            :param ticker: 종목코드
            :param url:
            :return:
            """

        html = None
        self.driver.get(url)
        time.sleep(0.5)
        try:
            # 암묵적 대기
            if WAIT_TYPE == 'IMP':
                self.driver.implicitly_wait(5)
                if PARSE_TYPE == 'CLS':
                    elements = self.driver.find_elements_by_class_name(att)
                    html = []
                    for element in elements:
                        html.append(element.get_attribute('innerHTML'))
                elif PARSE_TYPE == 'XPATH':
                    elements = self.driver.find_elements_by_xpath(att)
                    html = []
                    for element in elements:
                        html.append(element.get_attribute('innerHTML'))

            # 명시적 대기
            if WAIT_TYPE == 'EXP':
                if PARSE_TYPE == 'TAG':
                    element = WebDriverWait(self.driver, timeout=5).until(
                        EC.presence_of_element_located((By.TAG_NAME, att)))
                    # print("text = ", element.text)
                    html = element.get_attribute('innerHTML')
                elif PARSE_TYPE == 'CLS':
                    element = WebDriverWait(self.driver, timeout=5).until(
                        EC.presence_of_element_located((By.CLASS_NAME, att)))
                    # print("text = ", element.text)
                    html = element.get_attribute('innerHTML')

        finally:
            # self.driver.quit()
            pass

        return html


class ScrapFnguide:
    def __init__(self):
        pass
        # urlList = []
        #
        # urlList.append(
        #     "https://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?pGB=1&gicode=A" + ticker + "&cID=&MenuYn=Y&ReportGB=&NewMenuID=103&stkGb=701")
        # urlList.append(
        #     "https://comp.fnguide.com/SVO2/ASP/SVD_FinanceRatio.asp?pGB=1&gicode=A" + ticker + "&cID=&MenuYn=Y&ReportGB=&NewMenuID=104&stkGb=701")
        # urlList.append(
        #     "https://comp.fnguide.com/SVO2/ASP/SVD_Invest.asp?pGB=1&gicode=A" + ticker + "&cID=&MenuYn=Y&ReportGB=&NewMenuID=105&stkGb=701")
        # urlList.append(
        #     "https://comp.fnguide.com/SVO2/ASP/SVD_Consensus.asp?pGB=1&cID=&MenuYn=Y&ReportGB=&NewMenuID=108&stkGb=701")
        # urlList.append(
        #     "https://comp.fnguide.com/SVO2/ASP/SVD_EarSurprise.asp?pGB=1&gicode=A005930&cID=&MenuYn=Y&ReportGB=&NewMenuID=203&stkGb=701")

    def getSnapShot(self, ticker: str):
        """
                기본정보 가져오기
                :param ticker:
                :return:
                """
        url = "https://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=A"+ticker+"&cID=&MenuYn=Y&ReportGB=&NewMenuID=101&stkGb=701"
        html = ScrapFnguideCore().fetch(url, 'IMP', 'XPATH', '//*[@id="svdMainGrid1"]')
        # print(html)
        dfList = None

        if type(html) is list:
            for item in html:
                dfList = pd.read_html(item)
                # print(dfList[0].columns)
                # print(dfList[0])

        return dfList[0]

    def getPerformance(self, ticker: str):
        """
        실적 가져오기
        :param ticker:
        :return:
        """
        url = "https://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?pGB=1&gicode=A" + ticker + "&cID=&MenuYn=Y&ReportGB=&NewMenuID=103&stkGb=701"
        html = ScrapFnguideCore().fetch(url, 'IMP', 'XPATH', '//div[@class="ul_co1_c pd_t1"]')
        # print(html)
        dfList = None

        if type(html) is list:
            for item in html:
                dfList = pd.read_html(item)
                # print(dfList[0].columns)
                # print(dfList[0])

        return dfList[0]

    def getYearlyConsensus(self, ticker: str):
        """
        컨센서스
        :param ticker:
        :return:
        """
        url = "https://comp.fnguide.com/SVO2/ASP/SVD_Consensus.asp?pGB=1&gicode=A" + ticker + "&cID=&MenuYn=Y&ReportGB=&NewMenuID=108&stkGb=701"
        html = ScrapFnguideCore().fetch(url, 'IMP', 'XPATH', '//div[@class="ul_co1_c pd_t1"]')
        # print(html)
        dfList = []
        if type(html) is list:
            for item in html:
                dfList = pd.read_html(item)
                # print(dfList[0].columns)
                # print(dfList[0])
        df = dfList[0]
        df.index = df[df.columns[0]]
        df.drop(df.columns[0], axis=1, inplace=True)
        return dfList[0]

    def getQuarterConsensus(self, ticker: str):
        url = "https://comp.fnguide.com/SVO2/ASP/SVD_Consensus.asp?pGB=1&gicode=A" + ticker + "&cID=&MenuYn=Y&ReportGB=&NewMenuID=108&stkGb=701"
        SeleniumDriverManager().getUrl(url)
        # 분기버튼 클릭
        SeleniumDriverManager().click('//div[@id="div1AQGb"]/a[2]')
        time.sleep(0.4)
        html = ScrapFnguideCore().fetchOnCurrentUrl('IMP', 'XPATH', '//div[@class="ul_co1_c pd_t1"]')
        dfList = []
        if type(html) is list:
            for item in html:
                dfList = pd.read_html(item)
                # print(dfList[0].columns)
                # print(dfList[0])

        df = dfList[0]
        df.index = df[df.columns[0]]
        df.drop(df.columns[0], axis=1, inplace=True)
        return df


def refineDF(df, siteOpt, dataType):
    if siteOpt == 'NAVER' and dataType == 'PERF':
        # df.rename(columns='_'.join, inplace=True)
        df.columns = df.columns.map(NAVER_COLUMN_SEPARATOR.join)
        # df.index = df[('주요재무정보', '주요재무정보', '주요재무정보')]
        # df = df.drop(('주요재무정보', '주요재무정보', '주요재무정보'), axis=1)

        df.rename(columns={'주요재무정보'+NAVER_COLUMN_SEPARATOR+'주요재무정보'+NAVER_COLUMN_SEPARATOR+'주요재무정보': '주요재무정보'}, inplace=True)
        df.index = df['주요재무정보']
        df = df.drop('주요재무정보', axis=1)

    return df


class ScrapNaver:

    def getThemaMain(self):
        url = "https://finance.naver.com/sise/theme.nhn"
        html = ScrapNaverCore().fetch(url, 'IMP', 'XPATH', '//div[@id="contentarea_left"]')
        # print(html)
        if type(html) is list:
            for item in html:
                dfList = pd.read_html(item)
                # print(dfList[0].columns)
                # print(dfList[0])

    def getPerformance(self, ticker: str):
        """
        실적 가져오기
        :return:
        """
        url = "https://finance.naver.com/item/main.nhn?code=" + ticker
        html = ScrapNaverCore().fetch(url, 'IMP', 'XPATH',
                                      '//div[@class="section cop_analysis"]//div[@class="sub_section"]')
        # print(html)
        dfList = []
        if type(html) is list:
            for item in html:
                dfList = pd.read_html(item)
                # print(dfList)
                # print(len(df))
                # print(type(df))
                # print(dfList[0].columns)
                # print(dfList[0])

        # return dfList[0]
        df = refineDF(dfList[0], 'NAVER', 'PERF')

        return df


if __name__ == "__main__":
    # SeleniumDriverManager().close()
    # SeleniumDriverManager().reConnect()
    # df = ScrapFnguide().getSnapShot('005930')
    df = ScrapNaver().getPerformance('005930')
    print(df)
    print(SeleniumDriverManager().getStatus())
    df2 = ScrapFnguide().getYearlyConsensus('005930')
    print(df2)
    print(SeleniumDriverManager().getStatus())
    df3 = ScrapFnguide().getQuarterConsensus("005930")
    print(df3)
    print(SeleniumDriverManager().getStatus())
    SeleniumDriverManager().close()
    print(SeleniumDriverManager().getStatus())

    # # 테마별 세부정보 url get
    # html = ScrapNaverCore().fetch('005930', "https://finance.naver.com/item/main.nhn?code=005930"
    #                               , 'IMP', 'XPATH', '//div[@id="contentarea_left"]//td[@class="col_type1"]')
    # print(html)
    # if type(html) is list:
    #     for item in html:
    #         df = pd.read_html(item)
    #         print(df)
    #         print(len(df))
    #         print(type(df))
    #         print(df[0].columns)
