# will use all method in QAxWidget
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from config.classificationCode import *


# inherited QAxWidget Class
class Kiwoom(QAxWidget):

    # setting variable , init super class
    def __init__(self):
        # initializing for approaching to QAxWidget init method variable
        # so, usually self variable is in the init method.
        # but to get inherited Class's Method, just get to "super().methodName()"
        super().__init__()
        print("it is kiwoom Class")

        #### EventLoop
        self.loginEventLoop = None
        self.trEventLoop = None
        # self.trDetailAccountEventLoop = None
        # self.trDetailAccountStockEventLoop = None
        ##################

        #### variable
        self.accountNum = None  # 계좌번호
        self.serverType = None  # 서버구분
        self.useMoneyPercent = 0.5  # 예수금 가용률
        self.useMaxMoney = 0  # 비율설정후 주문가능한 금액
        self.stockTiedMoney = 0  # 주식매입금
        self.accountStockDict = {}  # 계좌평가잔고내역 멀티데이터
        self.nonContractDict = {}  # 미체결 멀티데이터
        self.stockDayChartDict = {}  # 주식일봉조회데이터
        self.fieldDayChartDict = {}  # 업종일봉조회데이터
        self.deposit = 0  # 예수금
        self.orderPossible = 0  # 주문가능금액
        self.withdrawPossible = 0  # 출금가능금액
        self.totalBuyMoney = 0  # 총매입금
        self.totalBenefit = 0  # 총수익률
        ##################

        self.getOcxInstance()
        self.eventSlots()
        self.signalLoginCommConnect()
        self.getAccountInfo()
        self.getCodeListByMarket("0")
        self.getCodeListByMarket("10")
        self.trRequest("예수금상세현황요청")
        self.trRequest("계좌평가잔고내역요청")
        self.trRequest("미체결요청")
        fieldDayVarDict = {"업종코드": "001", "기준일자": "20210423"}
        self.trRequest("업종일봉조회요청", fieldDayVarDict)
        stockDayVarDict = {"종목코드": "000390", "기준일자": "20210423", "수정주가구분": "0"}
        self.trRequest("주식일봉차트조회요청", stockDayVarDict)

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
        self.trEventLoop = QEventLoop()
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
        self.dynamicCall("DisconnectRealData(QString)", screenNum("CHART"))
        print("request stock daily chart.")

        self.dynamicCall("SetInputValue(QString,QString)", "종목코드", varDict["종목코드"])
        self.dynamicCall("SetInputValue(QString,QString)", "기준일자", varDict["기준일자"])
        self.dynamicCall("SetInputValue(QString,QString)", "수정주가구분", varDict["수정주가구분"])

        self.dynamicCall("CommRqData(QString,QString,int,QString)", "주식일봉차트조회요청", "opt10081", sPrevNext,
                         screenNum("CHART"))

    def fieldDayChart(self, varDict, sPrevNext="0"):
        """
        업종일봉조회요청
        :param varDict:
        :param sPrevNext:
        :return:
        """
        print("request field daily chart.")

        self.dynamicCall("SetInputValue(QString,QString)", "업종코드", varDict["업종코드"])
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
            self.recStockDayChart(sRQName, sTrCode)

        elif sRQName == "업종일봉조회요청":
            self.recFieldDayChart(sRQName, sTrCode)

        print("tr Request event loop end.")
        self.trEventLoop.exit()

    def recFieldDayChart(self, sRQName, sTrCode):
        code = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, 0, "업종코드")
        rows = self.dynamicCall("GetRepeatCnt(QString,QString)", sTrCode, sRQName)
        for i in range(rows):
            print("업종일봉조회요청 : 최근 ", i + 1, "번째 일자 일봉차트를 가져옵니다.")
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

    def recStockDayChart(self, sRQName, sTrCode):
        code = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, 0, "종목코드")
        rows = self.dynamicCall("GetRepeatCnt(QString,QString)", sTrCode, sRQName)
        for i in range(rows):
            print("주식일봉차트조회요청 : 최근 ", i + 1, "번째 일자 일봉차트를 가져옵니다.")
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

        print("종목코드 = ", code)
        print("주식일봉조회데이터일수 = ", len(self.stockDayChartDict[code]))

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
        self.useMaxMoney = int(self.deposit) * self.useMoneyPercent

        if self.useMaxMoney <= self.totalBuyMoney:
            self.useMaxMoney = 0
            print("매입금이 이미 설정한 비율의 주문가능한 금액을 넘어섰습니다. 주식가용비율 = ", self.useMoneyPercent * 100, "%")
        else:
            self.useMaxMoney = self.useMaxMoney - self.totalBuyMoney
            print("설정한 비율로 계산한 주문가능한 금액 = ", self.useMaxMoney)
