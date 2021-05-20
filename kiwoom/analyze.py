import pandas as pd
from numpy.lib import math

from config import sysConfig
from config.classificationCode import *
from pandas import Series, DataFrame
from config.stockConfig import *
from datetime import datetime
from krx import customWrap
import numpy as np
import copy
from scrap.core import ScrapNaver, ScrapFnguide
import traceback
import time


class Analyze:
    def __init__(self):

        self.baseUpdownPer = 2  # 기준 등락률
        self.baseTransMoney = 10000000000  # 기준 거래대금 , 단위 : 백만
        self.baseMarketCap = 300000000000  # 기준 시가총액액        self.stochasticParam = [[5, 3, 3], [10, 5, 5]]  # N, M, T
        self.stockStrongDict = {}  # 지수대비강 종목 (거래대금이 xx억이상, 등락률 x퍼이상)

        self.stockStrongSortDict = {}  # 등락률까지 고려하여 지수대비강 종목 재계산
        self.sectorStrongSortDict = {}  # 지수대비강 sector 계산
        self.performanceDict = {}  # 실적
        # self.industryStrongSortDict = {} # 지수대비강 Industry 계산

    def analyzeField(self, dict, option):
        """
        코스피 하락한 날짜 계산.
        :param dict:
        :param option: NAVER = kospiDownList가 xxxx-xx-xx 형식으로 나옴.
        :return: kospiDownList = 코스피가 하락한 날짜리스트
        """
        kospiChart = dict[fieldCode("KOSPI")]

        # transpose 반전
        kospiDF = DataFrame(kospiChart).transpose()

        kospiDF = self.calUpDownPer(kospiDF)
        # print(kospiDF)

        # kospiDF = self.calStochastic(kospiDF)
        # # 인덱스 값들 조회.
        # checkDate = [5,6,7,8,9,10]
        # print("info = ",kospiDF.iloc[checkDate, len(kospiDF.columns)-5:len(kospiDF.columns)])

        # print(kospiDF.iloc[[0],:])
        kospiRecentDF = kospiDF.iloc[:FIELD_SCAN_PERIOD]
        downList = kospiRecentDF.index[kospiRecentDF['등락률'] < float(0)].tolist()

        if option == 1 or option == 3:
            naverDownList = []
            for downDateStr in downList:
                downDate = datetime.strptime(downDateStr, '%Y%m%d')
                # downDateNewStr = downDate.strftime('%Y-%m-%d')
                naverDownList.append(downDate)

            # naver 일자 형식 : [datetime,datetime,...,datetime]
            print(naverDownList)
            return naverDownList

        elif option == 2:
            # kiwoom 일자 형식 : [str, str, ... , str]
            print(downList)
            return downList

    def selectStrongStock(self, code, stockDict, kospiDownList, codeMarketCap, option):
        """
        지수대비강 종목 추리기. 모든 종목의 일봉차트를 다 받아와서 종목안의 특정날짜를 체크하는 법. 비효율적
        :param option:
        :param code:
        :param codeMarketCap: 시가총액
        :param stockDict:
        :param kospiDownList:
        :return:
        """
        strongBool = False

        colTransMoney = None
        colChange = None

        if option == 1:
            # colOpen = stockDict.columns[0]
            # colHigh = stockDict.columns[1]
            # colLow = stockDict.columns[2]
            # colClose = stockDict.columns[3]
            # colTransVol = stockDict.columns[4]
            colChange = stockDict.columns[5]
            #
        elif option == 2:
            # colClose = stockDict.columns[0]
            # colTransVolume = stockDict.columns[1]
            colTransMoney = stockDict.columns[2]  # 단위 : 백만
            # colOpen = stockDict.columns[3]
            # colHigh = stockDict.columns[4]
            # colLow = stockDict.columns[5]
            colChange = stockDict.columns[6]
        elif option == 3:
            # colOpen = stockDict.columns[0]
            # colHigh = stockDict.columns[1]
            # colLow = stockDict.columns[2]
            # colClose = stockDict.columns[3]
            # colTransVol = stockDict.columns[4]
            colTransMoney = stockDict.columns[5]
            colChange = stockDict.columns[6]

        for downDateStr in kospiDownList:
            # try:
            # print("code=",code, ", date=",downDateStr)
            if downDateStr not in stockDict.index.tolist():
                print("date not exist in stockDict. code =", code)
                continue
            change = stockDict.loc[downDateStr, colChange]
            transMoney = stockDict.loc[downDateStr, colTransMoney]
            # print("selectStrongStock : change = ",change, ", type = ", type(change))
            if '-' not in str(change) and change >= float(
                    self.baseUpdownPer) and transMoney >= self.baseTransMoney and codeMarketCap >= self.baseMarketCap:
                # print("- is not exist in change value")
                if downDateStr in self.stockStrongDict:
                    pass
                else:
                    self.stockStrongDict.update({downDateStr: {}})
                self.stockStrongDict[downDateStr][code] = change
        # except Exception as e:
        #     print("error stock code = ", code)
        #     print("selectStrongStock : error occured. Exception = ",e)

        # for date in self.stockStrongCntDict.keys():
        #     print("selectStrongStock : date=",date,", code size = ",len(self.stockStrongCntDict[date]))

        return strongBool

    def selectStrongStockSimple(self, kospiDownList):
        """
        :return:
        """
        for downDate in kospiDownList:
            df = customWrap.getMarketOhlcvByTicker(downDate, market="ALL")
            colTransMoney = df.columns[5]
            colChange = df.columns[6]
            colMarketCap = df.columns[7]

            # sector, industry 둘다 nan 인 경우 drop
            transMoneyList = df[colTransMoney].tolist()
            changeList = df[colChange].tolist()
            marketCapList = df[colMarketCap].tolist()
            removeIndexList = []
            for i in range(len(transMoneyList)):
                if np.isnan(transMoneyList[i]):
                    print("종목 ", df.index[i], "에 거래대금 정보가 없습니다.")
                    removeIndexList.append(i)
                elif np.isnan(changeList[i]):
                    print("종목 ", df.index[i], "에 등락률 정보가 없습니다.")
                    removeIndexList.append(i)
                elif type(marketCapList[i]) is not str:
                    print("종목 ", df.index[i], "에 시가총액 정보가 없습니다.")
                    removeIndexList.append(i)
            df = df.drop(removeIndexList)

            strongList = df.index[(df[colTransMoney] >= self.baseTransMoney) & (df[colChange] >= float(
                self.baseUpdownPer)) & (pd.to_numeric(df[colMarketCap]) >= 300000000000)].tolist()
            for code in strongList:
                if downDate in self.stockStrongDict:
                    pass
                else:
                    self.stockStrongDict.update({downDate: {}})
                self.stockStrongDict[downDate][code] = df.loc[code, colChange]

    def sortStrongStock(self, sectorInfo):
        """
        1. 가장 강한 업종 체크
        종목의 섹터 카운트하기(종목 중복 허용) sector 체크.

        2. 가장 강한 종목 체크
        날짜 돌면서 상승률 다 더하기.
        :param sectorInfo:
        :return:
        """
        print("analyzeStock : Analyze Stock Data.")
        print(self.stockStrongDict)
        for date in self.stockStrongDict.keys():
            dateDict = self.stockStrongDict[date]
            for code in dateDict.keys():
                # 종목체크
                if code not in self.stockStrongSortDict:
                    self.stockStrongSortDict[code] = dateDict[code]
                else:
                    self.stockStrongSortDict[code] += dateDict[code]

                # 업종체크
                if code in sectorInfo.index:
                    codeSector = sectorInfo.loc[code, 'Sector']
                    # codeIndustry = sectorInfo.loc[code,'Industry']
                    if type(codeSector) is str:
                        if codeSector not in self.sectorStrongSortDict:
                            self.sectorStrongSortDict[codeSector] = []
                            self.sectorStrongSortDict[codeSector].append(code)
                        else:
                            self.sectorStrongSortDict[codeSector].append(code)
                else:
                    print(code, " 가 업종정보에 등록되어 있지 않습니다.")

        self.stockStrongSortDict
        print(self.stockStrongSortDict)
        strongSeries = Series(self.stockStrongSortDict)
        strongSeries = strongSeries.sort_values(ascending=False)
        self.stockStrongSortDict = strongSeries.to_dict()
        print(self.stockStrongSortDict)

        self.sectorStrongSortDict = self.sortDictByListSize(self.sectorStrongSortDict)

        print(strongSeries.index.tolist())
        print(self.sectorStrongSortDict)

        # for sector in self.sectorStrongSortDict:
        #     print('sector별 size :', sector, ' = ', len(self.sectorStrongSortDict[sector]))

    def calCurQuarter(self):
        return str(datetime.today().year) + 'Y' + '_' + str(math.ceil(datetime.today().month / 3.0)) + 'Q'

    def calCurYear(self):
        return str(datetime.today().year) + 'Y'

    def calQuarter(self, date: datetime):
        return str(date.year) + 'Y' + '_' + str(math.ceil(date.month / 3.0)) + 'Q'

    def calYear(self, date: datetime):
        return str(date.year) + 'Y'

    def calBeforeYear(self, yearStr: str, beforeCnt: int):
        return str(int(yearStr.replace('Y', '')) - beforeCnt) + 'Y'

    def calRightBeforeQuarter(self, quarterStr):
        year = quarterStr.split('_')[0]
        quar = quarterStr.split('_')[1]
        if quar != '1Q':
            rbQuar = str(int(quar.replace('Q', '')) - 1) + 'Q'
            rbYear = year
            return rbYear + '_' + rbQuar
        else:
            rbQuar = '4Q'
            rbYear = str(int(year.replace('Y', '')) - 1) + 'Y'
            return rbYear + '_' + rbQuar

    def calLastSameQuarter(self, quarterStr):
        year = quarterStr.split('_')[0]
        quar = quarterStr.split('_')[1]
        lastYear = str(int(year.replace('Y', '')) - 1) + 'Y'
        return lastYear + '_' + quar

    def calbeforeQuarter(self, quarterStr: str, beforeCnt: int):
        year = quarterStr.split('_')[0]
        quar = quarterStr.split('_')[1]
        beforeY = int(beforeCnt / 4)
        beforeQ = beforeCnt % 4

        firstResultY = int(year.replace('Y', '')) - beforeY
        if beforeQ >= int(quar.replace('Q', '')):
            return str(firstResultY - 1) + 'Y' + '_' + str(int(quar.replace('Q', '')) + (4 - beforeQ)) + 'Q'
        else:
            return str(firstResultY) + 'Y' + '_' + str(int(quar.replace('Q', '')) - beforeQ) + 'Q'

    def calAfterQuarter(self, quarterStr: str, afterCnt: int):
        year = quarterStr.split('_')[0]
        quar = quarterStr.split('_')[1]
        afterY = int(afterCnt / 4)
        afterQ = afterCnt % 4

        firstResultY = int(year.replace('Y', '')) + afterY
        if (afterQ + int(quar.replace('Q', ''))) > 4:
            return str(firstResultY + 1) + 'Y' + '_' + str(int(quar.replace('Q', '')) - (4 - afterQ)) + 'Q'
        else:
            return str(firstResultY) + 'Y' + '_' + str(int(quar.replace('Q', '')) + afterQ) + 'Q'

    def setPerformance(self, option):
        """
        이전분기와 현재분기를 기준으로 연간실적비교, 분기실적비교하기.
        :param option:
        :return:
        """
        curQuar = self.calCurQuarter()
        rightBeforeQuar = self.calbeforeQuarter(curQuar, 1)
        lastSameQuar = self.calbeforeQuarter(curQuar, 4)
        rightAfterQuar = self.calAfterQuarter(curQuar, 1)
        curYear = self.calCurYear()
        rightBeforeYear = self.calBeforeYear(curYear, 1)
        # 지수대비강 종목들 리스트를 가져옴.
        strongSeries = Series(self.stockStrongSortDict)
        codeList = strongSeries.index.tolist()
        if option == 'FNGUIDE':
            failCodeList = []
            for code in codeList:
                try:
                    dfYearCon = ScrapFnguide().getYearlyConsensus(code)
                    dfQuarCon = ScrapFnguide().getQuarterConsensus(code)
                except Exception as e:
                    traceback.print_exc()
                    print('get consensus failed. code = ', code)
                    failCodeList.append(codeList)
                    continue

                # 분기컨센서스 컬럼명 재구성
                for column in dfQuarCon.columns:
                    date = datetime.strptime(column.strip().replace('(P)', '').replace('(E)', ''), '%Y/%m')
                    newDate = self.calQuarter(date)
                    dfQuarCon.rename(columns={column: newDate}, inplace=True)
                # 연간컨센서스 컬럼명 재구성
                for column in dfYearCon.columns:
                    date = datetime.strptime(column.strip().replace('(P)', '').replace('(E)', ''), '%Y/%m')
                    newDate = self.calYear(date)
                    dfYearCon.rename(columns={column: newDate}, inplace=True)

                try:
                    self.setFnguidePerformance(code, dfYearCon, curYear)
                    self.setFnguidePerformance(code, dfYearCon, rightBeforeYear)
                    self.setFnguidePerformance(code, dfQuarCon, curQuar)
                    self.setFnguidePerformance(code, dfQuarCon, rightBeforeQuar)
                    self.setFnguidePerformance(code, dfQuarCon, rightAfterQuar)

                except Exception as e:
                    traceback.print_exc()
                    print('setPerformance : error occured : code = ', code, ', columns = ', dfQuarCon.columns.tolist())
                    failCodeList.append(code)

            if len(failCodeList) > 0:
                print('fail code list exist. try again.')
                # 실적가져오기 실패된 종목에 대해서 위와 똑같이 한번더 작업하기.

        if option == 'NAVER':
            failCodeList = []
            for code in codeList:
                try:
                    dfPerf = ScrapNaver().getPerformance(code)
                except Exception as e:
                    traceback.print_exc()
                    print('get consensus failed. code = ', code)
                    # failCodeList.append(codeList)
                    continue

                # 분기명 재구성
                for column in dfPerf.columns:
                    try:
                        perfType = column.split(NAVER_COLUMN_SEPARATOR)[0].strip()
                        dateStr = column.split(NAVER_COLUMN_SEPARATOR)[1]
                        if perfType == '최근 연간 실적':
                            date = datetime.strptime(dateStr.strip().replace('(P)', '').replace('(E)', ''), '%Y.%m')
                            newDate = self.calYear(date)
                            dfPerf.rename(columns={column: newDate}, inplace=True)
                        elif perfType == '최근 분기 실적':
                            date = datetime.strptime(dateStr.strip().replace('(P)', '').replace('(E)', ''), '%Y.%m')
                            newDate = self.calQuarter(date)
                            dfPerf.rename(columns={column: newDate}, inplace=True)
                    except Exception as e:
                        print('setPerformance : error occured : code = ', code, ', column = ', column)

                try:
                    # self.setNaverPerformance(code, dfPerf, rightBeforeQuar)
                    self.setNaverPerformance(code, dfPerf, lastSameQuar)
                    # self.setNaverPerformance(code, dfPerf, curYear)
                    # self.setNaverPerformance(code, dfPerf, rightBeforeYear)
                except Exception as e:
                    traceback.print_exc()
                    print('setPerformance : error occured : code = ', code, ', columns = ', dfPerf.columns.tolist())
                    # failCodeList.append(code)

            if len(failCodeList) > 0:
                print('fail code list exist. try again.')
                pass
                # 실적가져오기 실패된 종목에 대해서 위와 똑같이 한번더 작업하기.

        return self.performanceDict

    def comparePerformance(self):
        curQuar = self.calCurQuarter()
        rightBeforeQuar = self.calbeforeQuarter(curQuar, 1)
        rightAfterQuar = self.calAfterQuarter(curQuar, 1)
        lastSameQuar = self.calbeforeQuarter(curQuar, 4)
        curYear = self.calCurYear()
        rightBeforeYear = self.calBeforeYear(curYear, 1)

        deleteCodeList = []
        # 없는 컬럼은 nan으로 비교하기 위해 perfDF 생성.
        perfDF = DataFrame(self.performanceDict).transpose()
        for code in self.performanceDict.keys():
            if np.isnan(perfDF.loc[code, (curQuar, 'EPS')]):
                deleteCodeList.append(code)
                continue
            elif perfDF.loc[code, (curQuar, 'EPS')] < 0:
                deleteCodeList.append(code)
                continue

            if np.isnan(perfDF.loc[code, (rightBeforeQuar, 'EPS')]):
                pass
            elif perfDF.loc[code, (rightBeforeQuar, 'EPS')] < 0:
                self.performanceDict[code][('VS_RIGHT_BEFORE', 'EPS')] = 9999
            else:
                self.performanceDict[code][('VS_RIGHT_BEFORE', 'EPS')] = (self.performanceDict[code][(curQuar, 'EPS')] -
                                                            self.performanceDict[code][(rightBeforeQuar, 'EPS')]) / \
                                                           self.performanceDict[code][(rightBeforeQuar, 'EPS')] * 100

            if np.isnan(perfDF.loc[code, (rightAfterQuar, 'EPS')]):
                pass
            elif perfDF.loc[code, (rightAfterQuar, 'EPS')] < 0:
                self.performanceDict[code][('EXP_RIGHT_AFTER', 'EPS')] = 9999
            else:
                self.performanceDict[code][('EXP_RIGHT_AFTER', 'EPS')] = (self.performanceDict[code][(rightAfterQuar, 'EPS')] -
                                                            self.performanceDict[code][(curQuar, 'EPS')]) / \
                                                           self.performanceDict[code][(curQuar, 'EPS')] * 100

            if np.isnan(perfDF.loc[code, (lastSameQuar, 'EPS')]):
                pass
            elif perfDF.loc[code, (lastSameQuar, 'EPS')] < 0:
                self.performanceDict[code][('VS_LAST_SAME', 'EPS')] = 9999
            else:
                self.performanceDict[code][('VS_LAST_SAME', 'EPS')] = (self.performanceDict[code][(curQuar, 'EPS')] -
                                                            self.performanceDict[code][(lastSameQuar, 'EPS')]) / \
                                                           self.performanceDict[code][(lastSameQuar, 'EPS')] * 100

            if np.isnan(perfDF.loc[code, (rightBeforeYear, 'EPS')]):
                pass
            elif perfDF.loc[code, (rightBeforeYear, 'EPS')] < 0:
                self.performanceDict[code][('VS_LAST_YEAR', 'EPS')] = 9999
            else:
                self.performanceDict[code][('VS_LAST_YEAR', 'EPS')] = (self.performanceDict[code][(curYear, 'EPS')] -
                                                            self.performanceDict[code][(rightBeforeYear, 'EPS')]) / \
                                                           self.performanceDict[code][(rightBeforeYear, 'EPS')] * 100

        for code in deleteCodeList:
            del self.performanceDict[code]

        self.performanceDict = DataFrame(self.performanceDict).transpose().\
            sort_values(by=[('VS_LAST_SAME','EPS')], ascending=False)\
            [[('VS_RIGHT_BEFORE', 'EPS'),('EXP_RIGHT_AFTER', 'EPS'),('VS_LAST_SAME', 'EPS'),('VS_LAST_YEAR', 'EPS')
              ,(curYear,'EPS'),(rightBeforeYear,'EPS'),(curYear,'PER'),(rightBeforeYear,'PER')
              ,(curYear,'BPS'),(rightBeforeYear,'BPS'),(curYear,'PBR'),(rightBeforeYear,'PBR')
              ,(rightAfterQuar,'EPS'),(curQuar,'EPS'),(rightBeforeQuar,'EPS'),(lastSameQuar,'EPS')
              ,(rightAfterQuar,'PER'),(curQuar,'PER'),(rightBeforeQuar,'PER'),(lastSameQuar,'PER')
              ,(rightAfterQuar,'BPS'),(curQuar,'BPS'),(rightBeforeQuar,'BPS'),(lastSameQuar,'BPS')
              ,(rightAfterQuar,'PBR'),(curQuar,'PBR'),(rightBeforeQuar,'PBR'),(lastSameQuar,'PBR')]].transpose().to_dict()
        return self.performanceDict

    def setNaverPerformance(self, code, df, QuarStr):
        if code in self.performanceDict:
            pass
        else:
            self.performanceDict[code] = {}
        codePerfDic = self.performanceDict[code]

        if 'EPS(원)' in df.index and QuarStr in df.columns:
            codePerfDic[(QuarStr, 'EPS')] = float(df.loc['EPS(원)', QuarStr])
        else:
            codePerfDic[(QuarStr, 'EPS')] = np.nan
        if 'BPS(원)' in df.index and QuarStr in df.columns:
            codePerfDic[(QuarStr, 'BPS')] = float(df.loc['BPS(원)', QuarStr])
        else:
            codePerfDic[(QuarStr, 'BPS')] = np.nan
        if 'PBR(배)' in df.index and QuarStr in df.columns:
            codePerfDic[(QuarStr, 'PBR')] = float(df.loc['PBR(배)', QuarStr])
        else:
            codePerfDic[(QuarStr, 'PBR')] = np.nan
        if 'PER(배)' in df.index and QuarStr in df.columns:
            codePerfDic[(QuarStr, 'PER')] = float(df.loc['PER(배)', QuarStr])
        else:
            codePerfDic[(QuarStr, 'PER')] = np.nan

    def setFnguidePerformance(self, code, df, QuarStr):
        if code in self.performanceDict:
            pass
        else:
            self.performanceDict[code] = {}
        codePerfDic = self.performanceDict[code]

        if 'EPS(원)' in df.index and QuarStr in df.columns and df.loc['EPS(원)', QuarStr] != '-':
            codePerfDic[(QuarStr, 'EPS')] = float(df.loc['EPS(원)', QuarStr])
        else:
            codePerfDic[(QuarStr, 'EPS')] = np.nan
        if 'BPS(원)' in df.index and QuarStr in df.columns and df.loc['BPS(원)', QuarStr] != '-':
            codePerfDic[(QuarStr, 'BPS')] = float(df.loc['BPS(원)', QuarStr])
        else:
            codePerfDic[(QuarStr, 'BPS')] = np.nan
        if 'PBR' in df.index and QuarStr in df.columns and df.loc['PBR', QuarStr] != '-':
            codePerfDic[(QuarStr, 'PBR')] = float(df.loc['PBR', QuarStr])
        else:
            codePerfDic[(QuarStr, 'PBR')] = np.nan
        if 'PER' in df.index and QuarStr in df.columns and df.loc['PER', QuarStr] != '-':
            codePerfDic[(QuarStr, 'PER')] = float(df.loc['PER', QuarStr])
        else:
            codePerfDic[(QuarStr, 'PER')] = np.nan

    def sortDictByListSize(self, originDict):
        """
        dict내 value가 list형일때 list개수가 많은 순으로 정렬하는 알고리즘
        :param originDict:
        :return:
        """
        newDict = {}
        keyList = list(originDict.keys())
        itemList = list(originDict.items())
        # print(itemList[0])    # key-value pair list
        # print(itemList[0][0]) # key
        # print(itemList[0][1]) # value

        for i in range(len(itemList)):
            originItem = copy.deepcopy(itemList[i])
            maxValue = 0
            maxValueIdx = 0
            for j in range(i, len(itemList)):
                if j == i:
                    maxValue = len(itemList[j][1])
                    maxValueIdx = j
                    continue
                if maxValue > len(itemList[j][1]):
                    pass
                else:
                    maxValue = len(itemList[j][1])
                    maxValueIdx = j

            changeItem = copy.deepcopy(itemList[maxValueIdx])

            itemList[i] = changeItem
            itemList[maxValueIdx] = originItem

            # print('curIdx = ', i, ', maxIdx = ', maxValueIdx)
            # print('change Result = ', itemList)

        # convert 'list of key-value pair' to 'Dict'
        for item in itemList:
            newDict[item[0]] = item[1]

        return newDict

    def calUpDownPer(self, chartDF):
        """
        등락률 계산
        :param chartDF: column(현재가)
        :return:
        """
        # 날짜 ASC 정렬
        chartRowReverse = chartDF[::-1]
        chartCurReversePrice = chartRowReverse['현재가']

        chartUpDownPer = [float(0) for i in range(len(chartRowReverse))]

        dayBeforePrice = float(0)
        for i in range(len(chartDF)):
            # 등락률 계산 (날짜 ASC로 계산)
            if i < 1:
                dayBeforePrice = float(chartCurReversePrice[i])
                # print(dayBeforePrice)
                continue

            chartUpDownPer[i] = round((float(chartCurReversePrice[i]) - dayBeforePrice) / dayBeforePrice * 100, 2)
            dayBeforePrice = float(chartCurReversePrice[i])

        # kospiRowReverse['등락률'] = kospiUpdownPer # 에러남

        ##### 등락률 컬럼 추가
        # 1. 첫번째 방법
        # kospiRowReverse.insert(len(kospiRowReverse.columns), "등락률", kospiUpdownPer, allow_duplicates=True)
        # 2. 두번째 방법
        chartRowReverse = chartRowReverse.assign(등락률=chartUpDownPer)

        chartDF = chartRowReverse[::-1]

        return chartDF

    def calStochastic(self, chartDF):
        """
        스토캐스틱 지표 계산 \n
        FastK = (현재가 - n기간중 최저가)/(n기간중 최고가 - n기간중 최저가)*100 \n
        SlowK = FastK m일 이동평균 \n
        SlowD = SlowK t일 이동평균 \n
        :param chartDF: column(고가, 저가, 현재가)
        :return:
        """
        # 날짜 DESC
        chartHighPrice = chartDF['고가'].tolist()
        chartLowPrice = chartDF['저가'].tolist()
        chartCurPrice = chartDF['현재가'].tolist()

        ########### stochastic 지표 변수
        chartFastKDic = {}
        chartSlowKDic = {}
        chartSlowDDic = {}
        for param in self.stochasticParam:
            fastKColumn = str(param[0])
            slowKColumn = str(param[0]) + "_" + str(param[1])
            slowDColumn = str(param[0]) + "_" + str(param[1]) + "_" + str(param[2])
            if fastKColumn in chartFastKDic:
                pass
            else:
                chartFastKDic[fastKColumn] = [float(0) for i in range(len(chartDF))]

            if slowKColumn in chartSlowKDic:
                pass
            else:
                chartSlowKDic[slowKColumn] = [float(0) for i in range(len(chartDF))]

            if slowDColumn in chartSlowDDic:
                pass
            else:
                chartSlowDDic[slowDColumn] = [float(0) for i in range(len(chartDF))]
        ##################################

        # stochastic 지표 계산 (날짜 DESC로 계산)
        for param in self.stochasticParam:
            # 여기서는 fast K만 계산.
            # 다 계산하고 나서 이후에 slow K slow D 계산하기.
            fastKParam = param[0]
            for j in range(len(chartDF) - fastKParam + 1):
                periodHigh = max(chartHighPrice[j:j + fastKParam])
                periodLow = min(chartLowPrice[j:j + fastKParam])

                fastKVal = round(float((chartCurPrice[j] - periodLow) / (periodHigh - periodLow) * 100), 2)
                chartFastKDic[str(fastKParam)][j] = fastKVal

        # print("kospifastKDic=\n",DataFrame(kospiFastKDic))

        for param in self.stochasticParam:
            fastKParam = param[0]
            slowKParam = param[1]
            slowKVal = float(0)
            for j in range(len(chartDF) - fastKParam - slowKParam + 1):
                periodSum = 0
                for k in range(slowKParam):
                    periodSum += chartFastKDic[str(fastKParam)][j + k]
                slowKVal = round(float(periodSum / slowKParam), 2)
                chartSlowKDic[str(fastKParam) + "_" + str(slowKParam)][j] = slowKVal

        # print("kospiSlowKDic=\n", DataFrame(kospiSlowKDic))

        for param in self.stochasticParam:
            fastKParam = param[0]
            slowKParam = param[1]
            slowDParam = param[2]
            slowDVal = float(0)
            for j in range(len(chartDF) - fastKParam - slowKParam - slowDParam + 1):
                periodSum = 0
                for k in range(slowDParam):
                    periodSum += chartSlowKDic[str(fastKParam) + "_" + str(slowKParam)][j + k]
                slowDVal = round(float(periodSum / slowDParam), 2)
                chartSlowDDic[str(fastKParam) + "_" + str(slowKParam) + "_" + str(slowDParam)][j] = slowDVal

        # print("kospiSlowDDic=\n", DataFrame(kospiSlowDDic))

        # kospiRowReverse['등락률'] = kospiUpdownPer # 에러남

        for i in range(len(self.stochasticParam)):
            slowKColumn = list(chartSlowKDic.keys())[i]
            chartDF.insert(len(chartDF.columns), "SlowK(" + slowKColumn + ")", chartSlowKDic[slowKColumn],
                           allow_duplicates=True)
            slowDColumn = list(chartSlowDDic.keys())[i]
            chartDF.insert(len(chartDF.columns), "SlowD(" + slowDColumn + ")", chartSlowDDic[slowDColumn],
                           allow_duplicates=True)

        # 인덱스 값들 조회.
        # checkDate = [585,586,587,588,589,590]
        # print("info = ",kospiDF.iloc[checkDate])
        return chartDF


if __name__ == "__main__":
    curQuar = Analyze().calCurQuarter()
    print(curQuar)
