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
        self.accountNum = None
        self.useMoneyPercent = 0.5  # 예수금 가용률
        self.stockTiedMoney = 0  # 주식매입금
        self.useMaxMoney = 0  # 비율설정후 주문가능한 금액
        self.accountStockDict = {}  # 계좌평가잔고내역 멀티데이터

        ##################

        self.getOcxInstance()
        self.eventSlots()
        self.signalLoginCommConnect()
        self.getAccountInfo()
        self.trRequest("예수금상세현황요청")
        self.trRequest("계좌평가잔고내역요청")

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
        accountList = self.dynamicCall("GetLoginInfo(String)", "ACCNO")
        self.serverGubun = self.dynamicCall("GetLoginInfo(String)", "GetServerGubun")

        self.accountNum = accountList.split(';')[0]
        print("나의 보유계좌번호 : ", self.accountNum)
        print("접속서버 : ", self.serverGubun, ", info : ", loginServerInfo(self.serverGubun))

    def trRequest(self, trType):
        if trType == "예수금상세현황요청":
            self.detailAccountInfo()
        elif trType == "계좌평가잔고내역요청":
            self.detailAccountStockInfo()

        print("tr Request event loop start.")
        self.trEventLoop = QEventLoop()
        self.trEventLoop.exec_()

    def detailAccountInfo(self):
        print("request account asset info")

        # 변수를 후에 설정정보로 빼도 좋을듯.
        self.dynamicCall("SetInputValue(String,String)", "계좌번호", self.accountNum)
        self.dynamicCall("SetInputValue(String,String)", "비밀번호", "")
        self.dynamicCall("SetInputValue(String,String)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(String,String)", "조회구분", "2")

        # CommRqData("RQName", "opw00001", "0", "화면번호");
        # 화면번호는 (주문,조회 등의)요청마다 그룹핑을 해주는 용도. 한 화면번호에 최대 100개. 화면번호 종류는 200개까지 설정가능.
        self.dynamicCall("CommRqData(String,String,int,String)", "예수금상세현황요청", "OPW00001", "0", screenNum("MYINFO"))

    def detailAccountStockInfo(self, sPrevNext="0"):
        '''
        :param sPrevNext: 첫페이지는 o, 다음페이지가 있다면 2 , 한페이지 20개종목
        :return:
        '''
        print("request account detail stock info..")

        # 변수를 후에 설정정보로 빼도 좋을듯.
        self.dynamicCall("SetInputValue(String,String)", "계좌번호", self.accountNum)
        self.dynamicCall("SetInputValue(String,String)", "비밀번호", "")
        self.dynamicCall("SetInputValue(String,String)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(String,String)", "조회구분", "2")

        self.dynamicCall("CommRqData(String,String,int,String)", "계좌평가잔고내역요청", "opw00018", sPrevNext,
                         screenNum("MYINFO"))

    def trDataSlot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext, nDataLength):
        '''
        TR요청을 받는 슬롯임.
        :param sScrNo: 스크린번호
        :param sRQName: 내가 요청했을때 지은 이름
        :param sTrCode: 요청ID, TR코드
        :param sRecordName: 사용 안함
        :param sPrevNext: 다음 페이지가 없으면 "0" or "" , 다음페이지가 있으면 "2", 한페이지 20개종목
        :param nDataLength:
        :return:
        '''
        print("TR 요청 : ", sRQName)
        if sRQName == "예수금상세현황요청":
            self.deposit = self.dynamicCall("GetCommData(String,String,int,String)", sTrCode, sRQName, 0, "예수금")
            self.orderPossible = self.dynamicCall("GetCommData(String,String,int,String)", sTrCode, sRQName, 0,
                                                  "주문가능금액")
            self.withdrawPossible = self.dynamicCall("GetCommData(String,String,int,String)", sTrCode, sRQName, 0,
                                                     "출금가능금액")

            # deposit -> int(deposit) : 000000500000000 -> 500000000
            print("예수금 : ", int(self.deposit))
            print("주문가능금액 : ", int(self.orderPossible))
            print("출금가능금액 : ", int(self.withdrawPossible))


        elif sRQName == "계좌평가잔고내역요청":

            totalBuyMoney = self.dynamicCall("GetCommData(String,String,int,String)", sTrCode, sRQName, 0, "총매입금액")
            totalBenefit = self.dynamicCall("GetCommData(String,String,int,String)", sTrCode, sRQName, 0, "총수익률(%)")

            self.totalBuyMoney = int(totalBuyMoney)
            self.totalBenefit = float(totalBenefit)
            print("총매입금액 : ", self.totalBuyMoney)
            print("총수익률(%) : ", self.totalBenefit)

            # 오류가 난다면 String -> QString으로 타입 바꿔보기.
            # cnt를 증가시키면서 첫번째 종목, 두번째 종목 ... 의 멀티데이터(한페이지 최대 20개)를 갖고온다.
            rows = self.dynamicCall("GetRepeatCnt(QString,QString)", sTrCode, sRQName)
            for i in range(rows):
                print(i, "번째 종목정보를 가져옵니다.")
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

                self.accountStockDict[code]["종목명"] = codeNm
                self.accountStockDict[code]["보유수량"] = stockQuantity
                self.accountStockDict[code]["매입가"] = buyPrice
                self.accountStockDict[code]["수익률(%)"] = earnRate
                self.accountStockDict[code]["현재가"] = currentPrice
                self.accountStockDict[code]["매입금액"] = totalHoldPrice
                self.accountStockDict[code]["평가금액"] = totalMarkeyPrice
                self.accountStockDict[code]["매매가능수량"] = possibleQuantity

            print("현재 로딩한 보유종목정보 : ", self.accountStockDict)
            print("현재 로딩한 보유종목수 : ", len(self.accountStockDict))

            # sPrevNext가 2이면 다음페이지가 있다는 것이므로, 다음 20개종목이 들어있는 페이지 조회
            if sPrevNext == "2":
                self.detailAccountStockInfo(sPrevNext="2")
            else:
                print("다음 페이지가 없습니다.")
                pass

        print("tr Request event loop end.")
        self.trEventLoop.exit()

    def setUseMoney(self):
        self.useMaxMoney = int(self.deposit) * self.useMoneyPercent

        if self.useMaxMoney <= self.totalBuyMoney:
            self.useMaxMoney = 0
            print("매입금이 이미 설정한 비율의 주문가능한 금액을 넘어섰습니다. 주식가용비율 = ", self.useMoneyPercent * 100, "%")
        else:
            self.useMaxMoney = self.useMaxMoney - self.totalBuyMoney
            print("설정한 비율로 계산한 주문가능한 금액 = ", self.useMaxMoney)
