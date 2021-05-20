# will use all method in QAxWidget
from json import *

from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from PyQt5.QtTest import *
from datetime import datetime, timedelta
from kiwoom.analyze import *
import time
import FinanceDataReader as fdr
from config.stockConfig import *
from pykrx import stock
import traceback


# inherited QAxWidget Class
class Kiwoom(QAxWidget):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls)
        return cls._instance

    # setting variable , init super class
    def __init__(self):
        # initializing for approaching to QAxWidget init method variable
        # so, usually self variable is in the init method.
        # but to get inherited Class's Method, just get to "super().methodName()"
        super().__init__()
        print("it is kiwoom Class")

        #### class Object
        self.analyze = Analyze()

        #### EventLoop
        self.loginEventLoop = None
        self.trEventLoop = QEventLoop()
        # self.trDetailAccountEventLoop = None
        # self.trDetailAccountStockEventLoop = None
        ##################

        #### variable
        self.accountNum = None  # 계좌번호
        self.serverType = None  # 서버구분
        self.useMaxMoney = 0  # 비율설정후 주문가능한 금액
        self.stockTiedMoney = 0  # 주식매입금
        self.accountStockDict = {}  # 계좌평가잔고내역 멀티데이터
        self.nonContractDict = {}  # 미체결 멀티데이터
        self.stockDayChartDict = {}  # 주식일봉조회데이터
        self.stockNaverOrKrxDailyChartDict = {}  # 주식일봉조회데이터(NAVER or KRX)
        self.stockDayChartMaxCnt = -1  # 주식최대조회일수 설정 (kiwoom api에서 조회할때, trDataSlot에서 받아오는 일수를 가변적으로 변경하기 위함)
        self.stockDayChartCnt = 0  # 현재 단일종목 주식조회일수
        self.stockDayTransInfo = {}  # 일자별  거래대금, 거래량 조회 (NAVER옵션에서 사용)
        self.fieldDayChartDict = {}  # 업종일봉조회데이터
        self.deposit = 0  # 예수금
        self.orderPossible = 0  # 주문가능금액
        self.withdrawPossible = 0  # 출금가능금액
        self.totalBuyMoney = 0  # 총매입금
        self.totalBenefit = 0  # 총수익률
        self.codeList = []  # 종목코드리스트
        self.krxSectorInfo = None  # 종목섹터정보
        ##################

        self.getOcxInstance()
        self.eventSlots()
        self.signalLoginCommConnect()
        self.getAccountInfo()

        # 코스닥, 코스피 종목코드리스트 받아오기.
        self.getCodeListByMarket("0")
        self.getCodeListByMarket("10")
        # self.codeList = self.codeList[200:300]
        # self.codeList = ["001550"]
        # self.codeList.extend(["580016","580017","294570","005930"])

        # self.trRequest("예수금상세현황요청")
        # self.trRequest("계좌평가잔고내역요청")
        # self.trRequest("미체결요청")
        days = ["월", "화", "수", "목", "금", "토", "일"]  # 토,일이면 분석할 필요없으므로 조건 추가하기.
        self.today = datetime.today()

        # 느림. 하지만 financeDataReader로 지수차트를 받아오는데 안정성 문제가 있어. 지수는 이것으로 받아오기.
        fieldDayVarDict = {"업종코드": fieldCode("KOSPI"), "기준일자": self.today.strftime('%Y%m%d')}
        self.trRequest("업종일봉조회요청", fieldDayVarDict)

        # NAVER와 KRX에서 받아온 chartDF index는 TimeStamp형, KIWOOM에서 받아온 chartDF index는 Str형.
        apiType = apiCode("KRX")
        if apiType == apiCode("NAVER"):
            kospiDownList = self.analyze.analyzeField(self.fieldDayChartDict, option=apiCode("NAVER"))
            self.naverOrKrxStockDailyChart(kospiDownList, option=apiCode("NAVER"))
        elif apiType == apiCode("KIWOOM"):
            kospiDownList = self.analyze.analyzeField(self.fieldDayChartDict, option=apiCode("KIWOOM"))
            self.kiwoomStockDailyChart(kospiDownList)
        elif apiType == apiCode("KRX"):
            kospiDownList = self.analyze.analyzeField(self.fieldDayChartDict, option=apiCode("KRX"))
            # self.krxStockDailyChart(kospiDownList, option=apiCode("KRX"))
            self.analyze.selectStrongStockSimple(kospiDownList)

        self.recSectorInfo()
        self.analyze.sortStrongStock(self.krxSectorInfo)
        self.analyze.setPerformance('FNGUIDE')
        self.analyze.setPerformance('NAVER')
        perfDict = self.analyze.comparePerformance()
        self.writeFile(kospiDownList, perfDict)

    def writeFile(self, kospiDownList, perfDict):
        DataFrame(perfDict).transpose().to_csv(sysConfig.RESOURCES_DIR + '\\analyze.transpose.csv', sep=',')
        if len(kospiDownList) == 1:
            DataFrame(perfDict).to_csv(sysConfig.RESOURCES_DIR + '\\analyze.'
                                       + kospiDownList[len(kospiDownList) - 1].strftime('%Y%m%d') + '.csv', sep=',')
            DataFrame(perfDict).transpose().to_csv(sysConfig.RESOURCES_DIR + '\\analyze.transpose.'
                                                   + kospiDownList[len(kospiDownList) - 1].strftime('%Y%m%d') + '.csv',
                                                   sep=',')
        elif len(kospiDownList) > 1:
            DataFrame(perfDict).to_csv(sysConfig.RESOURCES_DIR + '\\analyze.'
                                       + kospiDownList[len(kospiDownList) - 1].strftime('%Y%m%d')
                                       + '_' + kospiDownList[0].strftime('%Y%m%d') + '.csv', sep=',')
            DataFrame(perfDict).transpose().to_csv(sysConfig.RESOURCES_DIR + '\\analyze.transpose.'
                                                   + kospiDownList[len(kospiDownList) - 1].strftime('%Y%m%d')
                                                   + '_' + kospiDownList[0].strftime('%Y%m%d') + '.csv', sep=',')

    def kiwoomStockDailyChart(self, kospiDownList):
        """
        코스피지수가 하락한 날짜의 상승종목을 조회함.
        :param kospiDownList:
        :return:
        """
        # tr조회요청 사이에 또 시간간격을 두어야 함. 너무 많이 하면 연결끊김.
        start = time.time()
        cnt = 0
        marketCap = self.recMarketCap()
        for code in self.codeList:
            # 공백이면 if not code = True
            if not code:
                continue
            stockDayVarDict = {"종목코드": code, "기준일자": self.today, "수정주가구분": "1"
                , "최대조회일수": STOCK_SCAN_PERIOD
                               }
            self.trRequest("주식일봉차트조회요청", stockDayVarDict)

            # 등락률 계산.
            df = DataFrame(self.stockDayChartDict[code]).transpose()
            df = self.analyze.calUpDownPer(df)
            if code in marketCap.index:
                codeMarketCap = marketCap.loc[code, '시가총액']
            else:
                codeMarketCap = 0
                print(code, " 에 대한 시가총액 정보가 없습니다.")

            # 지수대비강 종목을 추리기.
            self.analyze.selectStrongStock(code, df, kospiDownList, codeMarketCap)

            cnt += 1
            print("kiwoomStockDailyChart : code [", code, "] load complete. cnt = ", cnt)
            if cnt % 100 == 0:
                print("kiwoomStockDailyChart : Load Count = ", cnt)

        print("kiwoomStockDailyChart : Load Stock Chart data from kiwoom. time = ", time.time() - start)

    def naverOrKrxStockDailyChart(self, kospiDownList, option):
        """
        https://fchart.stock.naver.com/sise.nhn?timeframe=day&count=6000&requestType=0&symbol= 에서 요청한
        주식종목정보 리스트

        :param kospiDownList: 코스피 하락한 날짜 리스트 ( NAVER : date형 )
        :return:
        """
        start = time.time()
        cnt = 0

        if option == 1:
            # stockDayRansInfo 쓸거면 selectStrongStock에 인자 추가로 넣어줘야함.
            # 또는 NaverChartDF에 거래대금열 생성해서 해당하는 날짜에 값 넣기.
            for date in kospiDownList:
                dfTrans = stock.get_market_ohlcv_by_ticker(date.strftime('%Y%m%d'))[['거래대금']]
                if date in self.stockDayTransInfo:
                    pass
                else:
                    self.stockDayTransInfo[date] = dfTrans

        marketCap = self.recMarketCap()

        for code in self.codeList:
            try:
                # 공백이면 if not code = True
                if not code:
                    continue
                df = None
                if option == 1:
                    df = fdr.DataReader(code, (self.today - timedelta(days=STOCK_SCAN_PERIOD)).strftime('%Y-%m-%d'))
                elif option == 3:
                    df = stock.get_market_ohlcv_by_date(
                        (self.today - timedelta(days=STOCK_SCAN_PERIOD)).strftime('%Y%m%d'),
                        self.today.strftime('%Y%m%d'), code, adjusted=False)
                # 지수대비강 종목을 여기서 바로 추리기.

                if code in marketCap.index:
                    codeMarketCap = marketCap.loc[code, '시가총액']
                else:
                    codeMarketCap = 0
                    print(code, " 에 대한 시가총액 정보가 없습니다.")

                # dailyChart정보 모두 적재
                if code in self.stockNaverOrKrxDailyChartDict:
                    pass
                else:
                    self.stockNaverOrKrxDailyChartDict.update({code: {}})
                self.stockNaverOrKrxDailyChartDict[code] = df

                self.analyze.selectStrongStock(code, df, kospiDownList, codeMarketCap, option)

                cnt += 1
                if cnt % 10 == 0:
                    print("naverOrKrxStockDailyChart : Load Count = ", cnt)
                    time.sleep(10)

            except Exception as e:
                traceback.print_exc()
                print("naverOrKrxStockDailyChart : 받아온 정보를 읽어들일 수 없습니다")

        print("naverStockDailyChart : Naver DailyChart dict length = ", len(self.stockNaverDailyChartDict))

        print("naverStockDailyChart : Load Stock Chart data from naver End. time = ", time.time() - start)

    def krxStockDailyChart(self, kospiDownList, option):

        pass

    def recSectorInfo(self):
        krx = fdr.StockListing('KRX')
        filterKrx = krx[['Symbol', 'Market', 'Name', 'Sector', 'Industry']]

        # sector, industry 둘다 nan 인 경우 drop
        sectorList = filterKrx['Sector'].tolist()
        industryList = filterKrx['Industry'].tolist()
        removeIndexList = []
        for i in range(len(sectorList)):
            if type(sectorList[i]) is not str:
                removeIndexList.append(i)
        filterKrx = filterKrx.drop(removeIndexList)

        filterKrx.index = filterKrx['Symbol']
        self.krxSectorInfo = filterKrx.drop('Symbol', axis=1)

    def recMarketCap(self):
        today = datetime.today()
        df = stock.get_market_cap_by_ticker(today.strftime('%Y%m%d'))[['시가총액','상장주식수']]
        return df

    # can control openapi
    def getOcxInstance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    # make Slot to receive data for event
    def eventSlots(self):
        self.OnEventConnect.connect(self.loginSlot)
        self.OnReceiveTrData.connect(self.trDataSlot)

    # 로그인이 완료되면 errCode를 뿌려주도록 되어있으므로 그 후에 eventLoop를 종료시킨다.
    def loginSlot(self, errCode):
        print("login ErrorCode is = ", errors(errCode))

        self.loginEventLoop.exit()

    def signalLoginCommConnect(self):
        # pyqt5 : sending data to other application method
        # trying login
        self.dynamicCall("CommConnect()")

        # 로그인이 끝날때까지 eventLoop활성화
        self.loginEventLoop = QEventLoop()
        self.loginEventLoop.exec_()

    def getAccountInfo(self):
        accountList = self.dynamicCall("GetLoginInfo(QString)", "ACCNO")
        self.serverType = self.dynamicCall("GetLoginInfo(QString)", "GetServerGubun")
        print("서버구분 : ", self.serverType)
        self.accountNum = accountList.split(';')[0]
        print("나의 보유계좌번호 : ", self.accountNum)
        print("접속서버 : ", self.serverType, ", info : ", loginServerInfo(self.serverType))

    def getCodeListByMarket(self, marketCode):
        """
        종목코드가져오기.
        :param marketCode: 0:코스피, 10:코스닥
        :return:
        """
        codeList = self.dynamicCall("GetCodeListByMarket(QString)", marketCode)
        codeList = codeList.split(";")
        if int(marketCode) == 0:
            print("코스피 종목코드 개수: ", len(codeList))
        elif int(marketCode) == 10:
            print("코스닥 종목코드 개수 : ", len(codeList))

        self.codeList.extend(codeList)

    def trRequest(self, trType, varDict=None):
        if trType == "예수금상세현황요청":
            self.detailAccountInfo()
        elif trType == "계좌평가잔고내역요청":
            self.detailAccountStockInfo()
        elif trType == "미체결요청":
            self.nonContractedInfo()
        elif trType == "주식일봉차트조회요청":
            self.stockDayChart(varDict)
        elif trType == "업종일봉조회요청":
            self.fieldDayChart(varDict)

        print("tr Request event loop start.")
        self.trEventLoop.exec_()

    def detailAccountInfo(self):
        """
        예수금상세현황요청
        :return:
        """
        print("request account asset info.")

        # 변수를 후에 설정정보로 빼도 좋을듯.
        self.dynamicCall("SetInputValue(QString,QString)", "계좌번호", self.accountNum)
        self.dynamicCall("SetInputValue(QString,QString)", "비밀번호", "")
        self.dynamicCall("SetInputValue(QString,QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString,QString)", "조회구분", "2")

        # CommRqData("RQName", "opw00001", "0", "화면번호");
        # 화면번호는 (주문,조회 등의)요청마다 그룹핑을 해주는 용도. 한 화면번호에 최대 100개. 화면번호 종류는 200개까지 설정가능.
        self.dynamicCall("CommRqData(QString,QString,int,QString)", "예수금상세현황요청", "opw00001", "0", screenNum("MY_INFO"))

    def detailAccountStockInfo(self, sPrevNext="0"):
        """
        계좌평가잔고내역요청
        :param sPrevNext: 첫페이지는 o, 다음페이지가 있다면 2 , 한페이지 20개종목
        :return:
        """
        print("request account detail stock info.")

        # 변수를 후에 설정정보로 빼도 좋을듯.
        self.dynamicCall("SetInputValue(QString,QString)", "계좌번호", self.accountNum)
        self.dynamicCall("SetInputValue(QString,QString)", "비밀번호", "")
        self.dynamicCall("SetInputValue(QString,QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString,QString)", "조회구분", "2")

        self.dynamicCall("CommRqData(QString,QString,int,QString)", "계좌평가잔고내역요청", "opw00018", sPrevNext,
                         screenNum("MY_INFO"))

    def nonContractedInfo(self, sPrevNext="0"):
        """
        미체결요청
        :param sPrevNext:
        :return:
        """
        print("request non-contracted stock info.")

        self.dynamicCall("SetInputValue(QString,QString)", "계좌번호", self.accountNum)
        self.dynamicCall("SetInputValue(QString,QString)", "전체종목구분", "0")  # 안쓰면 전체로 되나?
        self.dynamicCall("SetInputValue(QString,QString)", "매매구분", "0")
        self.dynamicCall("SetInputValue(QString,QString)", "체결구분", "1")

        self.dynamicCall("CommRqData(QString,QString,int,QString)", "미체결요청", "opt10075", sPrevNext,
                         screenNum("MY_INFO"))

    # 차트조회요청 api와 계정정보조회요청 api를 구분하도록 리팩토링?
    def stockDayChart(self, varDict, sPrevNext="0"):
        """
        주식일봉차트조회요청
        :param subjCode: 종목코드
        :param date: 기준일자 , YYYYMMDD (20160101 연도4자리, 월 2자리, 일 2자리 형식)
        :param priceType: 수정주가구분 , 0 or 1, 수신데이터 1:유상증자, 2:무상증자, 4:배당락, 8:액면분할, 16:액면병합, 32:기업합병, 64:감자, 256:권리락
        :return:
        """
        # self.dynamicCall("DisconnectRealData(QString)", screenNum("CHART"))
        print("request stock daily chart.")
        QTest.qWait(2000)
        self.dynamicCall("SetInputValue(QString,QString)", "종목코드", varDict["종목코드"])
        if "기준일자" in varDict:
            self.dynamicCall("SetInputValue(QString,QString)", "기준일자", varDict["기준일자"])
        self.dynamicCall("SetInputValue(QString,QString)", "수정주가구분", varDict["수정주가구분"])

        self.dynamicCall("CommRqData(QString,QString,int,QString)", "주식일봉차트조회요청", "opt10081", sPrevNext,
                         screenNum("CHART"))

        if "최대조회일수" in varDict:
            self.stockDayChartMaxCnt = varDict["최대조회일수"]

    def fieldDayChart(self, varDict, sPrevNext="0"):
        """
        업종일봉조회요청
        :param varDict:
        :param sPrevNext:
        :return:
        """
        print("request field daily chart.")
        QTest.qWait(1000)

        self.dynamicCall("SetInputValue(QString,QString)", "업종코드", varDict["업종코드"])
        if "기준일자" in varDict:
            self.dynamicCall("SetInputValue(QString,QString)", "기준일자", varDict["기준일자"])

        self.dynamicCall("CommRqData(QString,QString,int,QString)", "업종일봉조회요청", "opt20006", sPrevNext,
                         screenNum("CHART"))

    def trDataSlot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext, nDataLength):
        """
        TR요청을 받는 슬롯
        :param sScrNo: 스크린번호
        :param sRQName: 내가 요청했을때 지은 이름
        :param sTrCode: 요청ID, TR코드
        :param sRecordName: 사용 안함
        :param sPrevNext: 다음 페이지가 없으면 "0" or "" , 다음페이지가 있으면 "2", 한페이지 20개종목
        :param nDataLength:
        :return:
        """
        print("TR 요청 : ", sRQName)
        if sRQName == "예수금상세현황요청":
            self.recDetailAccInfo(sRQName, sTrCode)

        elif sRQName == "계좌평가잔고내역요청":
            self.recDetailAccStockInfo(sPrevNext, sRQName, sTrCode)

        elif sRQName == "미체결요청":
            self.recNonContractedInfo(sRQName, sTrCode)

        elif sRQName == "주식일봉차트조회요청":
            sPrevNext = self.recStockDayChart(sPrevNext, sRQName, sTrCode)

        elif sRQName == "업종일봉조회요청":
            self.recFieldDayChart(sPrevNext, sRQName, sTrCode)

        print("sPrevNext = ", sPrevNext)
        if sPrevNext == "2":
            print("tr Request event loop maintain.")
        else:
            self.trEventLoop.exit()
            print("tr Request event loop end.")

    def recFieldDayChart(self, sPrevNext, sRQName, sTrCode):
        code = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, 0, "업종코드")
        rows = self.dynamicCall("GetRepeatCnt(QString,QString)", sTrCode, sRQName)
        dayBeforePrice = None
        for i in range(rows):
            # print("업종일봉조회요청 : 최근 ", i + 1, "번째 일자 일봉차트를 가져옵니다.")
            currentPrice = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, i, "현재가")
            flowQuantity = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, i, "거래량")
            flowMoney = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, i, "거래대금")
            date = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, i, "일자")
            startPrice = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, i, "시가")
            highPrice = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, i, "고가")
            lowPrice = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, i, "저가")

            code = code.strip()
            currentPrice = int(currentPrice.strip())
            flowQuantity = int(flowQuantity.strip())
            flowMoney = int(flowMoney.strip())
            date = date.strip()
            startPrice = int(startPrice.strip())
            highPrice = int(highPrice.strip())
            lowPrice = int(lowPrice.strip())

            if code in self.fieldDayChartDict:
                pass
            else:
                self.fieldDayChartDict.update({code: {}})

            if date in self.fieldDayChartDict[code]:
                pass
            else:
                self.fieldDayChartDict[code].update({date: {}})

            dayDict = self.fieldDayChartDict[code][date]
            dayDict["현재가"] = currentPrice
            dayDict["거래량"] = flowQuantity
            dayDict["거래대금"] = flowMoney
            dayDict["시가"] = startPrice
            dayDict["고가"] = highPrice
            dayDict["저가"] = lowPrice

        print("업종코드 = ", code, " 업종일봉조회데이터일수 = ", len(self.fieldDayChartDict[code]))

        # sPrevNext가 2이면 다음페이지가 있다는 것이므로, 다음 20개종목이 들어있는 페이지 조회
        if sPrevNext == "2":
            varDict = {"업종코드": code}
            self.fieldDayChart(varDict, sPrevNext="2")
        else:
            print("다음 페이지가 없습니다.")
            pass

    def recStockDayChart(self, sPrevNext, sRQName, sTrCode):

        cntCompleted = False
        code = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, 0, "종목코드")
        rows = self.dynamicCall("GetRepeatCnt(QString,QString)", sTrCode, sRQName)
        for i in range(rows):

            # print("주식일봉차트조회요청 : 최근 ", i + 1, "번째 일자 일봉차트를 가져옵니다.")
            currentPrice = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, i, "현재가")
            flowQuantity = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, i, "거래량")
            flowMoney = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, i, "거래대금")
            date = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, i, "일자")
            startPrice = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, i, "시가")
            highPrice = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, i, "고가")
            lowPrice = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, i, "저가")

            code = code.strip()
            currentPrice = int(currentPrice.strip())
            flowQuantity = int(flowQuantity.strip())
            flowMoney = int(flowMoney.strip())
            date = date.strip()
            startPrice = int(startPrice.strip())
            highPrice = int(highPrice.strip())
            lowPrice = int(lowPrice.strip())

            if code in self.stockDayChartDict:
                pass
            else:
                self.stockDayChartDict.update({code: {}})

            if date in self.stockDayChartDict[code]:
                pass
            else:
                self.stockDayChartDict[code].update({date: {}})

            dayDict = self.stockDayChartDict[code][date]
            dayDict["현재가"] = currentPrice
            dayDict["거래량"] = flowQuantity
            dayDict["거래대금"] = flowMoney
            dayDict["시가"] = startPrice
            dayDict["고가"] = highPrice
            dayDict["저가"] = lowPrice

            # 조회일수 체크
            self.stockDayChartCnt += 1
            if self.stockDayChartMaxCnt == -1:
                continue
            elif self.stockDayChartCnt >= self.stockDayChartMaxCnt:
                cntCompleted = True
                break

        print("종목코드 = ", code)
        print("주식일봉조회데이터일수 = ", len(self.stockDayChartDict[code]))

        # sPrevNext가 2이면 다음페이지가 있다는 것이므로, 다음 20개종목이 들어있는 페이지 조회
        if sPrevNext == "2" and not cntCompleted:
            varDict = {"종목코드": code, "수정주가구분": "1"}
            self.stockDayChart(varDict, sPrevNext="2")
        elif cntCompleted:
            print("최대조회일수만큼 데이터를 가져왔습니다.")
            self.stockDayChartCnt = 0
            sPrevNext = "0"
        else:
            print("다음 페이지가 없습니다.")
            self.stockDayChartCnt = 0
        return sPrevNext

    def recNonContractedInfo(self, sRQName, sTrCode):
        rows = self.dynamicCall("GetRepeatCnt(QString,QString)", sTrCode, sRQName)
        for i in range(rows):
            print("미체결요청 : ", i + 1, "번째 종목정보를 가져옵니다.")
            code = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, i, "종목번호")
            codeNm = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, i, "종목명")
            orderNo = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, i, "주문번호")
            # 주문상태 : 접수 -> 확인 -> 체결
            orderStatus = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, i, "주문상태")
            orderQuantity = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, i, "주문수량")
            orderPrice = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, i, "주문가격")
            # 주문구분 : 매수, 매도, 정정, 취소
            orderClassify = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, i, "주문구분")
            nonQuantity = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, i, "미체결수량")
            okQuantity = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, i, "체결량")

            code = code.strip()
            codeNm = codeNm.strip()
            orderNo = int(orderNo.strip())
            orderStatus = orderStatus.strip()
            orderQuantity = int(orderQuantity.strip())
            orderPrice = int(orderPrice.strip())
            orderClassify = orderClassify.strip().lstrip('+').lstrip('-')
            nonQuantity = int(nonQuantity.strip())
            okQuantity = int(okQuantity.strip())

            if orderNo in self.nonContractDict:
                pass
            else:
                self.nonContractDict.update({orderNo: {}})

            nonDict = self.nonContractDict[orderNo]
            nonDict["종목코드"] = code
            nonDict["종목명"] = codeNm
            nonDict["주문상태"] = orderStatus
            nonDict["주문수량"] = orderQuantity
            nonDict["주문가격"] = orderPrice
            nonDict["주문구분"] = orderClassify
            nonDict["미체결수량"] = nonQuantity
            nonDict["체결량"] = okQuantity

        print("미체결 종목 : ", self.nonContractDict)

    def recDetailAccStockInfo(self, sPrevNext, sRQName, sTrCode):
        """
        계좌평가잔고내역요청 결과값 받기
        :param sPrevNext:
        :param sRQName:
        :param sTrCode:
        :return:
        """
        totalBuyMoney = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, 0, "총매입금액")
        totalBenefit = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, 0, "총수익률(%)")
        self.totalBuyMoney = int(totalBuyMoney)
        self.totalBenefit = float(totalBenefit)
        print("총매입금액 : ", self.totalBuyMoney)
        print("총수익률(%) : ", self.totalBenefit)
        # 오류가 난다면 String -> QString으로 타입 바꿔보기.
        # cnt를 증가시키면서 첫번째 종목, 두번째 종목 ... 의 멀티데이터(한페이지 최대 20개)를 갖고온다.
        rows = self.dynamicCall("GetRepeatCnt(QString,QString)", sTrCode, sRQName)
        for i in range(rows):
            print("계좌평가잔고내역요청 : ", i, "번째 종목정보를 가져옵니다.")
            code = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, i, "종목번호")
            codeNm = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, i, "종목명")
            stockQuantity = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, i,
                                             "보유수량")
            buyPrice = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, i, "매입가")
            earnRate = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, i, "수익률(%)")
            currentPrice = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, i, "현재가")
            totalHoldPrice = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, i,
                                              "매입금액")
            totalMarkeyPrice = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, i,
                                                "평가금액")
            possibleQuantity = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, i,
                                                "매매가능수량")

            code = code.strip()[1:]  # Axxxx -> xxxx 숫자 파싱.
            codeNm = codeNm.strip()
            stockQuantity = int(stockQuantity.strip())
            buyPrice = int(buyPrice.strip())
            earnRate = float(earnRate.strip())
            currentPrice = int(currentPrice.strip())
            totalHoldPrice = int(totalHoldPrice.strip())
            totalMarkeyPrice = int(totalMarkeyPrice.strip())
            possibleQuantity = int(possibleQuantity.strip())

            if code in self.accountStockDict:
                pass
            else:
                self.accountStockDict.update({code: {}})

            accStockDict = self.accountStockDict[code]
            accStockDict["종목명"] = codeNm
            accStockDict["보유수량"] = stockQuantity
            accStockDict["매입가"] = buyPrice
            accStockDict["수익률(%)"] = earnRate
            accStockDict["현재가"] = currentPrice
            accStockDict["매입금액"] = totalHoldPrice
            accStockDict["평가금액"] = totalMarkeyPrice
            accStockDict["매매가능수량"] = possibleQuantity

        print("현재 로딩한 보유종목정보 : ", self.accountStockDict)
        print("현재 로딩한 보유종목수 : ", len(self.accountStockDict))
        # sPrevNext가 2이면 다음페이지가 있다는 것이므로, 다음 20개종목이 들어있는 페이지 조회
        if sPrevNext == "2":
            self.detailAccountStockInfo(sPrevNext="2")
        else:
            print("다음 페이지가 없습니다.")
            pass

    def recDetailAccInfo(self, sRQName, sTrCode):
        """
        예수금상세현황요청 결과값 받기
        :param sRQName:
        :param sTrCode:
        :return:
        """
        deposit = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, 0, "예수금")
        orderPossible = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, 0,
                                         "주문가능금액")
        withdrawPossible = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, 0,
                                            "출금가능금액")
        self.deposit = int(deposit)
        self.orderPossible = int(orderPossible)
        self.withdrawPossible = int(withdrawPossible)
        # deposit -> int(deposit) : 000000500000000 -> 500000000
        print("예수금 : ", self.deposit)
        print("주문가능금액 : ", self.orderPossible)
        print("출금가능금액 : ", self.withdrawPossible)

    def setUseMoney(self):
        self.useMaxMoney = int(self.deposit) * USE_MONEY_PERCENT

        if self.useMaxMoney <= self.totalBuyMoney:
            self.useMaxMoney = 0
            print("매입금이 이미 설정한 비율의 주문가능한 금액을 넘어섰습니다. 주식가용비율 = ", USE_MONEY_PERCENT * 100, "%")
        else:
            self.useMaxMoney = self.useMaxMoney - self.totalBuyMoney
            print("설정한 비율로 계산한 주문가능한 금액 = ", self.useMaxMoney)
