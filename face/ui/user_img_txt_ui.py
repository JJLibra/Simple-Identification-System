# -*- coding: utf-8 -*-
import sys
import qtawesome
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QIcon


class ImageTxtUi(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(756, 529)

        # 关闭
        self.close_button = QtWidgets.QPushButton(Form)
        self.close_button.setGeometry(QtCore.QRect(20, 20, 31, 21))
        self.close_button.setObjectName("closeButton")

        # 其他
        self.other_button = QtWidgets.QPushButton(Form)
        self.other_button.setGeometry(QtCore.QRect(60, 20, 31, 21))
        self.other_button.setObjectName("other_button")

        # 最小化
        self.minimize_button = QtWidgets.QPushButton(Form)
        self.minimize_button.setGeometry(QtCore.QRect(100, 20, 31, 21))
        self.minimize_button.setObjectName("minimizeButton")

        self.img_a_button = QtWidgets.QPushButton(Form)
        self.img_a_button.setGeometry(QtCore.QRect(90, 70, 131, 31))
        self.img_a_button.setObjectName("img_a_button")

        self.img_a_path = QtWidgets.QTextBrowser(Form)
        self.img_a_path.setGeometry(QtCore.QRect(240, 70, 421, 31))
        self.img_a_path.setObjectName("img_a_path")

        self.img_a_show = QtWidgets.QLabel(Form)
        self.img_a_show.setGeometry(QtCore.QRect(120, 125, 510, 300))
        self.img_a_show.setObjectName("img_a_show")

        self.compare_button = QtWidgets.QPushButton(Form)
        self.compare_button.setGeometry(QtCore.QRect(250, 450, 221, 31))
        self.compare_button.setObjectName("compare_button_button")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.img_a_show.setText('')
        self.img_a_show.setStyleSheet('QLabel{font-size:20px;}')
        # self.img_a_show.setAlignment(Qt.AlignCenter)
        self.img_a_button.setText(_translate("Form", "添加图片"))
        self.compare_button.setText(_translate("Form", "开始识别"))

        # ------------------------------------ #
        # 控制按钮样式
        self.minimize_button.setFixedSize(30, 30)  # 设置关闭按钮的大小
        self.other_button.setFixedSize(30, 30)  # 设置按钮大小
        self.close_button.setFixedSize(30, 30)  # 设置最小化按钮大小

        # 设置按钮部件的QSS样式
        # 默认为淡色，鼠标悬浮时为深色
        self.close_button.setStyleSheet(
            '''QPushButton{background:#F76677;border-radius:15px;}QPushButton:hover{background:red;}''')
        self.other_button.setStyleSheet(
            '''QPushButton{background:#F7D674;border-radius:15px;}QPushButton:hover{background:yellow;}''')
        self.minimize_button.setStyleSheet(
            '''QPushButton{background:rgba(106, 168, 255);border-radius:15px;}QPushButton:hover{background:blue;}''')
        buttons = [self.img_a_button, self.compare_button]
        for button in buttons:
            button.setStyleSheet(
                '''QPushButton{
                    border:none;
                    color:white;
                    height:35px;
                    padding-left:5px;
                    background:#646669;
                    border-radius:10px;
                    padding-right:10px;
                    font-size:15px;}

                    QPushButton:hover{
                    color:white;
                    background:#828282;}''')

        # ------------------------------------ #
        # 整体样式
        Form.setWindowOpacity(0.85)
        Form.setWindowTitle("文字识别")
        Form.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        pe = QPalette()
        Form.setAutoFillBackground(True)
        pe.setColor(QPalette.Window, Qt.lightGray)
        Form.setPalette(pe)

        # ------------------------------------ #
        # 图标样式
        Form.setWindowIcon(QIcon('./img/luckycat.ico'))

        self.img_a_path.setStyleSheet('''
                        QTextBrowser{
                        background:white;
                        border:2px solid gray;
                        font-size:13px;
                        font-weight:700;
                        font-family: "Helvetica Neue";
                        border-radius:12px;
                        height:25px;
                        }''')


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    widgets = QtWidgets.QMainWindow()
    ui = ImageTxtUi()
    ui.setupUi(widgets)
    widgets.show()
    sys.exit(app.exec_())

