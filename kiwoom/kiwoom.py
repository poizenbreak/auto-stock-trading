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
        self.trDetailAccountEventLoop = None
        self.trDetailAccountStockEventLoop = None
        ##################

        #### variable
        self.accountNum = None
        ##################

        self.getOcxInstance()
        self.eventSlots()
        self.signalLoginCommConnect()
        self.getAccountInfo()
        self.detailAccountInfo()
        self.detailAccountStockInfo()

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

    def detailAccountInfo(self):
        print("request account asset info")

        # 변수를 후에 설정정보로 빼도 좋을듯.
        self.dynamicCall("SetInputValue(String,String)", "계좌번호", self.accountNum)
        self.dynamicCall("SetInputValue(String,String)", "비밀번호", "")
        self.dynamicCall("SetInputValue(String,String)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(String,String)", "조회구분", "2")

        # CommRqData("RQName", "opw00001", "0", "화면번호");
        # 화면번호는 (주문,조회 등의)요청마다 그룹핑을 해주는 용도. 한 화면번호에 최대 100개. 화면번호 종류는 200개까지 설정가능.
        self.dynamicCall("CommRqData(String,String,int,String)", "예수금상세현황요청", "OPW00001", "0", "2000")

        print("tr(detail account info) Request event loop start.")
        self.trDetailAccountEventLoop = QEventLoop()
        self.trDetailAccountEventLoop.exec_()

    def detailAccountStockInfo(self, sPrevNext="0"):
        print("request account detail stock info..")

        # 변수를 후에 설정정보로 빼도 좋을듯.
        self.dynamicCall("SetInputValue(String,String)", "계좌번호", self.accountNum)
        self.dynamicCall("SetInputValue(String,String)", "비밀번호", "")
        self.dynamicCall("SetInputValue(String,String)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(String,String)", "조회구분", "2")

        self.dynamicCall("CommRqData(String,String,int,String)", "계좌평가잔고내역요청", "opw00018", sPrevNext, "2000")

        print("tr(detail Account Stock Info) Request event loop start.")
        self.trDetailAccountStockEventLoop = QEventLoop()
        self.trDetailAccountStockEventLoop.exec_()


    def trDataSlot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext, nDataLength):
        '''
        TR요청을 받는 슬롯임.
        :param sScrNo: 스크린번호
        :param sRQName: 내가 요청했을때 지은 이름
        :param sTrCode: 요청ID, TR코드
        :param sRecordName: 사용 안함
        :param sPrevNext: 다음 페이지가 있는지
        :param nDataLength:
        :return:
        '''
        print("TR 요청 : ",sRQName)
        if sRQName == "예수금상세현황요청":
            deposit = self.dynamicCall("GetCommData(String,String,int,String)", sTrCode, sRQName, 0, "예수금")
            orderPossible = self.dynamicCall("GetCommData(String,String,int,String)", sTrCode, sRQName, 0,
                                             "주문가능금액")
            withdrawPossible = self.dynamicCall("GetCommData(String,String,int,String)", sTrCode, sRQName, 0,
                                                "출금가능금액")

            # deposit -> int(deposit) : 000000500000000 -> 500000000
            print("예수금 : ", int(deposit))
            print("주문가능금액 : ",int(orderPossible))
            print("출금가능금액 : ",int(withdrawPossible))

            print("tr Request event loop end.")
            self.trDetailAccountEventLoop.exit()

        elif sRQName == "계좌평가잔고내역요청":
            totalBuyMoney = self.dynamicCall("GetCommData(String,String,int,String)", sTrCode, sRQName, 0, "총매입금액")
            totalBenefit = self.dynamicCall("GetCommData(String,String,int,String)", sTrCode, sRQName, 0, "총수익률(%)")

            print("총매입금액 : ", int(totalBuyMoney))
            print("총수익률 : ", float(totalBenefit))

            print("tr Request event loop end.")
            self.trDetailAccountStockEventLoop.exit()






