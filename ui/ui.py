# make Ui at this Class

import sys
from kiwoom.kiwoom import Kiwoom
# it is library for make UI
from PyQt5.QtWidgets import *

class UiClass:
    def __init__(self):
        print("it is UI Class")

        # sys.argv = ['파이썬파일경로','추가할옵션','추가할옵션']
        self.app = QApplication(sys.argv)
        self.kiwoom = Kiwoom()


        # eventloop executing. must be exit manually.
        self.app.exec_()
        print("kiwoom api end.")