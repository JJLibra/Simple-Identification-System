# -*- coding: utf-8 -*-
import os
import sys
from time import time

import cv2
import face_recognition
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QInputDialog

from ui.start_main_ui import StartMainUi

from logic.user_main import UserMainWindow, FaceCompareWindow, ImgTxtWindow


class StartMainWindow(QMainWindow, StartMainUi):
    signal_user = pyqtSignal()
    signal_admin = pyqtSignal()

    def __init__(self, parent=None):
        super(StartMainWindow, self).__init__(parent)
        self.setupUi(self)

        self.close_button.clicked.connect(self.close)
        self.minimize_button.clicked.connect(self.showMinimized)

        self.user_button.clicked.connect(self.show_login_dialog)
        self.admin_button.clicked.connect(self.send_signal_admin)
        self.cancel_button.clicked.connect(self.close)
        self.show()

        self.counter = 0
        self.name = "Unknown"
        self.isAdmin_flag = False
        self.registrant = None
        self.cancel_flag = False

    def send_signal_user(self):
        self.signal_user.emit()
        self.close()

    # 显示登陆界面
    def show_login_dialog(self):
        path = "img/face_recognition"  # 模型数据图片目录
        total_image_name = []
        total_face_encoding = []
        for fn in os.listdir(path):  # fn 表示的是文件名q
            print(path + "/" + fn)
            total_face_encoding.append(
                face_recognition.face_encodings(
                    face_recognition.load_image_file(path + "/" + fn))[0])
            fn = fn[:(len(fn) - 4)]  # 截取图片名（这里应该把images文件中的图片名命名为为人物名）
            total_image_name.append(fn)  # 图片名字列表
        QMessageBox.information(self, "提示", self.tr("开始验证，请看摄像头"))
        cap = cv2.VideoCapture(0)
        while not self.isAdmin_flag:
            ret, frame = cap.read()
            # 发现在视频帧所有的脸和face_enqcodings
            face_locations = face_recognition.face_locations(frame)
            face_encodings = face_recognition.face_encodings(frame, face_locations)
            # 在这个视频帧中循环遍历每个人脸
            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                # 看看面部是否与已知人脸相匹配
                for i, v in enumerate(total_face_encoding):
                    match = face_recognition.compare_faces([v], face_encoding, tolerance=0.5)
                    if match[0]:
                        self.isAdmin_flag = True
                        self.name = total_image_name[i]
                        break
                if self.isAdmin_flag:
                    cap.release()
                    break
            if self.isAdmin_flag:
                QMessageBox.information(self, "欢迎", self.tr("你好！" + self.name))
                self.send_signal_user()
            elif self.counter == 5:
                QMessageBox.information(self, "提示", self.tr("请先注册！"))
                break
            else:
                QMessageBox.information(self, "提示", self.tr("暂未识别到，请对准摄像头！"))
                self.counter += 1
                # 延时器

    # 注册信号
    def send_signal_admin(self):
        QMessageBox.information(self, "提示", self.tr("开始注册，请注视摄像头。"))
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        show = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # cv2.imshow("Image", show)
        gray = cv2.cvtColor(show, cv2.COLOR_BGR2GRAY)  # 转换灰色
        # OpenCV人脸识别分类器
        classifier = cv2.CascadeClassifier("data\\haarcascade_frontalface_default.xml")
        # 调用识别人脸
        faceRects = classifier.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=3, minSize=(32, 32))
        if len(faceRects):  # 大于0则检测到人脸
            # 获取姓名
            self.cancel_flag = True
            self.record_name_dialog()
            if self.cancel_flag:
                cv2.imwrite("img/face_recognition/" + self.registrant + ".jpg", show)
                QMessageBox.information(self, "提示", self.tr("用户添加成功！"))
        else:
            QMessageBox.information(self, "提示", self.tr("未识别到人脸！"))

    def record_name_dialog(self):
        dialog = QInputDialog(self)
        dialog.setWindowTitle('用户名')
        dialog.setLabelText('请输入用户名：')
        # 定义一个布尔变量，表示用户名是否已存在
        user_exists = True
        # 使用while循环，直到用户输入一个不存在的用户名
        while user_exists:
            # 调用exec_方法显示对话框，并获取用户输入的值和点击的按钮
            value, ok = dialog.getText(dialog, '用户名', '请输入用户名：')
            params = str(value)
            path = "img/face_recognition"
            # 假设用户名不存在
            user_exists = False
            for fn in os.listdir(path):
                if fn == params + '.jpg':
                    # 如果发现用户名已存在，则弹出提示消息，并将user_exists设为True
                    QMessageBox.information(self, "提示", self.tr("用户已存在，请重新输入！"))
                    user_exists = True
                    break  # 跳出for循环
            # 判断用户是否点击了确定按钮
            if ok and not user_exists:
                print('success')
                try:
                    self.registrant = params
                except:
                    QMessageBox.information(self, "提示", self.tr("请正确输入用户名！"))
            elif not ok:
                # 如果用户点击了取消按钮，则跳出while循环
                self.cancel_flag = False
                break


if __name__ == "__main__":
    ui_start_time = time()
    app = QApplication(sys.argv)

    # 主界面
    main_win = StartMainWindow()
    user_main = UserMainWindow()
    # admin_main = AdminMainWindow()
    # 用户次界面
    # modify = ModifyWindow()
    # register = RegisterWindow()
    faceCompare = FaceCompareWindow()
    imgTxt = ImgTxtWindow()
    # 管理员次界面
    # login = LoginWindow()
    # delete = DeleteWindow()
    # unlock = UnloadWindow()
    # setting = AdminSettingWindow()

    # 主界面信号槽
    main_win.signal_user.connect(user_main.show)
    # main_win.signal_admin.connect(admin_main.show)
    # 用户界面信号槽
    # user_main.signal_register.connect(register.show)
    user_main.signal_compare.connect(faceCompare.show)
    user_main.signal_txt.connect(imgTxt.show)
    # user_main.signal_modify.connect(modify.show)
    # 管理员界面信号槽
    # admin_main.signal_login.connect(login.show)
    # admin_main.signal_unlock.connect(unlock.show)
    # admin_main.signal_setting.connect(setting.show)
    # admin_main.signal_delete.connect(delete.show)

    print('界面 初始化时间:', time() - ui_start_time)

    sys.exit(app.exec_())
