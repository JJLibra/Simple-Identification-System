import os
import sys
import random
from datetime import datetime  # 可以用于获取当前的时间
from time import time  # 用于计算一个模块运行的时间
import configparser  # 解析配置文件
import numpy as np  # 数组 相关

# 人脸识别,活体检测 相关
import pytesseract
import cv2
import dlib
import face_recognition
import imutils
from imutils import face_utils
from scipy.spatial import distance as dist
import mediapipe as mp
from PIL import Image, ImageDraw, ImageFont  # 显示汉字

# PyQt5界面设计 相关
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import *
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QDialog, QInputDialog
from PyQt5 import QtWidgets

# 界面ui 相关
from ui.user_face_compare_ui import FaceCompareUi
from ui.user_img_txt_ui import ImageTxtUi
from ui.user_main_ui import UserMainUi

# 文件目录
curPath = os.path.abspath(os.path.dirname(__file__))
# 项目根路径
rootPath = curPath[:curPath.rindex('logic')]
# 配置文件夹路径
CONF_FOLDER_PATH = rootPath + 'conf\\'
# 图片文件夹路径
PHOTO_FOLDER_PATH = rootPath + 'photo\\'
# 数据文件夹路径
DATA_FOLDER_PATH = rootPath + 'data\\'

# 读取配置文件 获取参数
conf = configparser.ConfigParser()
conf.read(CONF_FOLDER_PATH + 'setting.conf', encoding='gbk')
CAPTURE_SOURCE = conf.get('image_config', 'capture_source')
if CAPTURE_SOURCE == '0':
    CAPTURE_SOURCE = int(CAPTURE_SOURCE)
TOLERANCE = float(conf.get('image_config', 'tolerance'))
SET_SIZE = float(conf.get('image_config', 'set_size'))

# 登录标志
USER_LOGIN_MSG_FLAG = False
USER_LOGIN_FLAG = False
USER_LOGIN_COUNT = 0
USER_LOGIN_NAME = ""
# 临时变量
SHOT_TEMP_NAME = ""
ENCODING_TEMP = ""


# 主界面
class UserMainWindow(QMainWindow, UserMainUi):
    # JUNIOR
    # signal_register = pyqtSignal()  # 用户注册 界面信号
    # signal_modify = pyqtSignal()  # 用户修改 界面信号
    # SENIOR
    signal_compare = pyqtSignal()  # 图片识别 界面信号
    signal_txt = pyqtSignal()  # 文字识别 界面信号
    signal_partition = pyqtSignal()  # 精细分割 界面信号

    def __init__(self, parent=None):
        super(UserMainWindow, self).__init__(parent)
        self.setupUi(self)

        self.show_image = None
        self.set_name = None
        self.set_names = None
        self.need_record_name = ([])

        self.camera_start_time = None
        self.detect_start_time = None

        self.cap = cv2.VideoCapture()  # 相机
        self.source = CAPTURE_SOURCE  # 相机标号
        self.WIN_WIDTH = 800  # 相机展示画面宽度
        self.WIN_HEIGHT = 500  # 相机展示画面高度
        self.isFaceRecognition_flag = False  # 是否打开人脸识别标志
        self.isFaceDetection_flag = False  # 是否打开活体检测标志
        self.isFineSegmentation_flag = False  # 是否打开背景模糊标志
        self.isAttitudeDetection_flag = False  # 是否打开姿态检测标志
        self.isObjectExtraction_flag = False  # 是否打开对象提取标志
        self.cancel_flag = True  # 取消标志
        self.H = 0
        self.S = 0
        self.V = 0

        self.all_list = []

        self.detector = None  # 人脸检测器
        self.predictor = None  # 特征点检测器
        # 闪烁阈值
        self.EAR_THRESH = None
        self.MOUTH_THRESH = None
        # 总闪烁次数
        self.eye_flash_counter = None
        self.mouth_open_counter = None
        self.turn_left_counter = None
        self.turn_right_counter = None
        # 连续帧数阈值
        self.EAR_CONSTANT_FRAMES = None
        self.MOUTH_CONSTANT_FRAMES = None
        self.LEFT_CONSTANT_FRAMES = None
        self.RIGHT_CONSTANT_FRAMES = None
        # 连续帧计数器
        self.eye_flash_continuous_frame = 0
        self.mouth_open_continuous_frame = 0
        self.turn_left_continuous_frame = 0
        self.turn_right_continuous_frame = 0
        # 字体颜色
        self.text_color = (255, 0, 0)
        # 百度API
        # self.api = BaiduApiUtil

        # 窗口控制
        self.close_button.clicked.connect(self.close_window)  # 关闭窗口
        self.minimize_button.clicked.connect(self.showMinimized)  # 最小化窗口
        # JUNIOR
        self.camera_button.clicked.connect(self.open_camera)  # 打开摄像头
        # self.register_button.clicked.connect(self.user_register)  # 打开注册界面
        # self.login_button.clicked.connect(self.user_login)  # 打开登录界面
        # self.logout_button.clicked.connect(self.user_logout)  # 用户登出
        # self.query_user_button.clicked.connect(self.send_signal_modify)  # 打开查询界面
        # SENIOR
        self.recognition_button.clicked.connect(self.recognize_face_judge)  # 人脸识别
        self.biopsy_testing_button.clicked.connect(self.detect_face_judge)  # 活体检测
        self.face_compare_button.clicked.connect(self.send_signal_compare)  # 图片识别
        self.img_txt_button.clicked.connect(self.send_signal_txt)  # 文字识别
        self.fine_segmentation_button.clicked.connect(self.fine_segmentation_judge)  # 精细分割
        self.attitude_detection_button.clicked.connect(self.criticalPoint_detection_judge)  # 姿态检测
        self.object_extraction_button.clicked.connect(self.object_extraction_judge)  # 对象提取

    # 发射信号 打开注册用户界面
    # def send_signal_register(self):
    #     self.signal_register.emit()
    #
    # # 发射信号 打开修改信息界面
    # def send_signal_modify(self):
    #     self.signal_modify.emit()

    # 发射信号 打开人脸对比界面
    def send_signal_compare(self):
        self.signal_compare.emit()

    def send_signal_txt(self):
        self.signal_txt.emit()

    # ----------------- 打开摄像头 ------------------ #
    # 打开摄像头判断器
    def open_camera(self):
        if not self.cap.isOpened():
            self.camera_start_time = time()
            self.cap.open(self.source)
            print("相机 初始化时间:", time() - self.camera_start_time)
            try:
                self.show_camera()
            except:
                QMessageBox.about(self, '警告', '相机不能正常被打开')
        else:  # 关闭摄像头，释放cap
            self.cap.release()
            self.camera_button.setText(u'打开相机')
            self.camera_label.setPixmap(QPixmap(""))
            self.camera_label.setText('智能识别系统')

    # 展示摄像头画面
    def show_camera(self):
        self.camera_button.setText(u'关闭相机')
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            QApplication.processEvents()
            show = cv2.resize(frame, (self.WIN_WIDTH, self.WIN_HEIGHT))
            show = cv2.cvtColor(show, cv2.COLOR_BGR2RGB)
            self.show_image = QImage(show.data, show.shape[1], show.shape[0], QImage.Format_RGB888)
            self.camera_label.setPixmap(QPixmap.fromImage(self.show_image))
        self.camera_label.setPixmap(QPixmap(""))

    # ----------------- 用户注册 ------------------ #
    # 用户注册
    # def user_register(self):
    #     isCapOpened_flag = self.cap.isOpened()
    #     if not isCapOpened_flag:
    #         QMessageBox.information(self, "提示", self.tr("请先打开摄像头!"))
    #     else:
    #         ret, frame = self.cap.read()
    #         frame_location = face_recognition.face_locations(frame)
    #         if len(frame_location) == 0:
    #             QMessageBox.information(self, "提示", self.tr("没有检测到人脸，请重新拍摄!"))
    #         else:
    #             QMessageBox.information(self, "提示", self.tr("拍照成功!"))
    #
    #             global PHOTO_FOLDER_PATH
    #             global SHOT_TEMP_NAME
    #             SHOT_TEMP_NAME = datetime.now().strftime("%Y%m%d%H%M%S")
    #             self.show_image.save(PHOTO_FOLDER_PATH + SHOT_TEMP_NAME + ".jpg")
    #             # self.send_signal_register()
    #
    # # ----------------- 用户登录 ------------------ #
    # # 用户登录
    # def user_login(self):
    #     if not self.cap.isOpened():
    #         QMessageBox.information(self, "提示", self.tr("请先打开摄像头"))
    #     else:
    #         global USER_LOGIN_FLAG
    #         if not USER_LOGIN_FLAG:
    #             QApplication.processEvents()
    #             login = LoginWindow(self)
    #             login.exec_()
    #             global USER_LOGIN_MSG_FLAG
    #             global USER_LOGIN_NAME
    #             if USER_LOGIN_MSG_FLAG:
    #                 # 登录信息成功，进行活体检测
    #                 QMessageBox.about(self, '提示', '登录成功，进行活体检测')
    #                 if self.detect_face():
    #                     # 活体检测成功，进行人脸识别
    #                     global ENCODING_TEMP
    #                     face_encoding = FaceEncodingUtil.decoding_FaceStr(ENCODING_TEMP)
    #                     if self.recognize_instant_face(face_encoding):
    #                         QMessageBox.about(self, '提示', '登陆成功')
    #                         self.save_record(USER_LOGIN_NAME, '使用摄像头进行登录')
    #                         USER_LOGIN_FLAG = True
    #                     else:
    #                         QMessageBox.about(self, '提示', '人脸识别失败，请重新登录')
    #                         if USER_LOGIN_NAME != "":
    #                             UserSqlUtil.add_name_warn(USER_LOGIN_NAME)
    #                         USER_LOGIN_MSG_FLAG = False
    #                 else:
    #                     QMessageBox.about(self, '提示', '活体检测失败，请重新登录')
    #                     if USER_LOGIN_NAME != "":
    #                         UserSqlUtil.add_name_warn(USER_LOGIN_NAME)
    #                     USER_LOGIN_MSG_FLAG = False
    #             login.destroy()
    #         else:
    #             QMessageBox.about(self, '提示', '用户已经登录')
    #
    # # 用户登出
    # def user_logout(self):
    #     global USER_LOGIN_FLAG
    #     global USER_LOGIN_NAME
    #     if not USER_LOGIN_FLAG:
    #         QMessageBox.about(self, '提示', '请先登录')
    #     else:
    #         USER_LOGIN_FLAG = False
    #         QMessageBox.about(self, '提示', '退出成功')
    #         self.save_record(USER_LOGIN_NAME, '退出登录')

    # ----------------- 人脸识别 ------------------ #
    # 人脸识别判断器
    def recognize_face_judge(self):
        if not self.cap.isOpened():
            QMessageBox.information(self, "提示", self.tr(u"请先打开摄像头"))
        else:
            # 点击人脸识别时，人脸识别是关闭的
            if not self.isFaceRecognition_flag:
                self.isFaceRecognition_flag = True
                self.recognition_button.setText(u'关闭人脸识别')
                self.recognize_continuous_face()
            # 点击人脸识别时，人脸识别已经开启
            elif self.isFaceRecognition_flag:
                self.isFaceRecognition_flag = False
                self.recognition_button.setText(u'人脸识别')
                # self.clear_information()
                self.show_camera()

    # 瞬时人脸识别
    # def recognize_instant_face(self, recognize_encoding):
    #     # 隔帧处理，减少计算量
    #     process_this_frame = True
    #     # 超过10帧判断识别失败，因为隔帧处理，一共判断5帧
    #     total_frame = 0
    #     # 已知的人脸编码集合
    #     recognize_encodings = [recognize_encoding]
    #     # 当摄像头打开时开始检测，当 检测成功 或 超过10帧 时推出循环
    #     while self.cap.isOpened():
    #         # 获取当前摄像头画面帧 frame
    #         ret, frame = self.cap.read()
    #         # 帧数加一
    #         total_frame += 1
    #         # 减少界面卡顿
    #         QApplication.processEvents()
    #         # 对帧进行裁剪处理，减少计算量
    #         small_frame = cv2.resize(frame, (0, 0), fx=SET_SIZE, fy=SET_SIZE)
    #
    #         # 判断当前帧是否需要计算（隔帧处理）
    #         if process_this_frame:
    #             QApplication.processEvents()
    #             # 核心代码
    #             unknown_locations = face_recognition.face_locations(small_frame)
    #             unknown_encodings = face_recognition.face_encodings(small_frame, unknown_locations)
    #             for unknown_encoding in unknown_encodings:
    #                 match = face_recognition.compare_faces(recognize_encodings, unknown_encoding, tolerance=TOLERANCE)
    #                 if True in match:
    #                     return True
    #         # 隔帧处理
    #         process_this_frame = not process_this_frame
    #
    #         # 超时退出
    #         if total_frame >= 10.0:
    #             return False
    #
    #         # 对传回来的画面进行处理
    #         show_video = cv2.resize(frame, (self.WIN_WIDTH, self.WIN_HEIGHT))
    #         show_video = cv2.cvtColor(show_video, cv2.COLOR_BGR2RGB)
    #         self.show_image = QImage(show_video.data, show_video.shape[1], show_video.shape[0], QImage.Format_RGB888)
    #         self.camera_label.setPixmap(QPixmap.fromImage(self.show_image))

    # 人脸识别
    def recognize_continuous_face(self):
        # # 通过数据库读取已知的用户姓名以及人脸编码
        # self.read_person_msg()
        # known_names = []  # 存放已知用户的名字
        # known_encodings = []  # 存放已知用户的人脸特征信息
        # for i in range(len(self.all_list)):
        #     known_names.append(self.all_list[i][0])
        #     known_encodings.append(FaceEncodingUtil.decoding_FaceStr(self.all_list[i][5]))
        #
        # # 从摄像头实时读取未知用户编码
        # unknown_locations = []  # 存放未知用户的人脸位置
        # unknown_names = [] # 存放经过识别的用户名字
        # process_this_frame = True
        # while self.cap.isOpened():
        #     ret, frame = self.cap.read()
        #     QApplication.processEvents()
        #     small_frame = cv2.resize(frame, (0, 0), fx=SET_SIZE, fy=SET_SIZE)
        #
        #     if process_this_frame:
        #         QApplication.processEvents()
        #         unknown_locations = face_recognition.face_locations(small_frame)
        #         unknown_encodings = face_recognition.face_encodings(small_frame, unknown_locations)
        #         unknown_names = []
        #         for unknown_encoding in unknown_encodings:
        #             name = "Unknown" # 默认未知
        #             matches = face_recognition.compare_faces(known_encodings, unknown_encoding, tolerance=TOLERANCE)
        #             if True in matches:
        #                 first_match_index = matches.index(True)
        #                 name = known_names[first_match_index]
        #             unknown_names.append(name)
        #
        #     process_this_frame = not process_this_frame
        #
        #     # 保存捕捉到的人脸姓名信息
        #     self.set_name = set(unknown_names)
        #     self.set_names = tuple(self.set_name)
        #
        #     # 绘制图像
        #     for (top, right, bottom, left), name in zip(unknown_locations, unknown_names):
        #         top *= int(1 / SET_SIZE)
        #         right *= int(1 / SET_SIZE)
        #         bottom *= int(1 / SET_SIZE)
        #         left *= int(1 / SET_SIZE)
        #         # 画矩形框
        #         cv2.rectangle(frame, (left, top), (right, bottom), (60, 20, 220), 2)
        #
        #         # 由于opencv无法显示汉字，用PIL进行转换
        #         cv2_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        #         pil_img = Image.fromarray(cv2_img)
        #         draw = ImageDraw.Draw(pil_img)
        #         # 参数1：字体文件路径，参数2：字体大小
        #         font = ImageFont.truetype(DATA_FOLDER_PATH + "MicrosoftYaHeiFont.ttf", 24, encoding="utf-8")
        #         # 参数1：打印坐标，参数2：文本，参数3：字体颜色，参数4：字体
        #         draw.text((left + 10, bottom), name, (220, 20, 60), font=font)
        #         frame = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        #
        #     self.show_results()
        #     show_video = cv2.resize(frame, (self.WIN_WIDTH, self.WIN_HEIGHT))
        #     show_video = cv2.cvtColor(show_video, cv2.COLOR_BGR2RGB)
        #     self.show_image = QImage(show_video.data, show_video.shape[1], show_video.shape[0], QImage.Format_RGB888)
        #     self.camera_label.setPixmap(QPixmap.fromImage(self.show_image))

        # 展示人脸识别结果
        while self.cap.isOpened():
            # 获取当前摄像头画面帧 frame
            ret, frame = self.cap.read()
            QApplication.processEvents()

            self.discern(frame)

    # 图片识别方法封装
    def discern(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        cap = cv2.CascadeClassifier(
            "./data/haarcascade_frontalface_default.xml"
        )
        faceRects = cap.detectMultiScale(
            gray, scaleFactor=1.2, minNeighbors=3, minSize=(50, 50))
        if len(faceRects):
            for faceRect in faceRects:
                x, y, w, h = faceRect
                cv2.rectangle(img, (x, y), (x + h, y + w), (0, 255, 0), 2)  # 框出人脸
        # cv2.imshow("Image", img)
        show_video = cv2.resize(img, (self.WIN_WIDTH, self.WIN_HEIGHT))
        show_video = cv2.cvtColor(show_video, cv2.COLOR_BGR2RGB)
        self.show_image = QImage(show_video.data, show_video.shape[1], show_video.shape[0], QImage.Format_RGB888)
        self.camera_label.setPixmap(QPixmap.fromImage(self.show_image))

    # def show_results(self):
    #     if self.isFaceRecognition_flag:
    #         msg_label = {0: self.msg_label_a,
    #                      1: self.msg_label_b,
    #                      2: self.msg_label_c}
    #
    #         # 最多放置3个人的信息
    #         if len(self.set_names) > 3:
    #             show_person = 3
    #         else:
    #             show_person = len(self.set_names)
    #
    #         if show_person != 0:
    #             for show_index in range(show_person):
    #                 name = self.set_names[show_index]
    #                 try:
    #                     per_label = msg_label[show_index]
    #                     index = self.search_person_index(self.all_list, name)
    #                     if index != -1:
    #                         infor_str = ' 姓名: ' + name + '                ' + \
    #                                     ' 年龄: ' + self.all_list[index][2] + '                 ' + \
    #                                     ' 性别: ' + self.all_list[index][3] + '                 ' + \
    #                                     ' 更多: ' + self.all_list[index][4]
    #                         per_label.setText(infor_str)
    #                         per_label.setStyleSheet("color:white;font-size:20px;font-family:Microsoft YaHei;")
    #                         per_label.setWordWrap(True)
    #                 except:
    #                     QMessageBox.about(self, '警告', '请检查' + name + '的信息')
    #
    #         if show_person != 3:
    #             for empty in range(3)[show_person:]:
    #                 per_label = msg_label[empty]
    #                 per_label.setText("")

    # 读取用户信息
    # def read_person_msg(self):
    #     all_msg = UserSqlUtil.search_all_msg()
    #     for tup in all_msg:
    #         per_list = []
    #         for i in tup:
    #             per_list.append(i)
    #         self.all_list.append(per_list)

    # 查找指定用户下标
    # @staticmethod
    # def search_person_index(persons_infor, name):
    #     for i in range(len(persons_infor)):
    #         if persons_infor[i][0] == name:
    #             return i
    #     return -1
    #
    # # 清除人脸识别结果信息
    # def clear_information(self):
    #     self.msg_label_a.setText("")
    #     self.msg_label_b.setText("")
    #     self.msg_label_c.setText("")

    # ----------------- 活体检测 ------------------ #
    # 活体检测判断器
    def detect_face_judge(self):
        if not self.cap.isOpened():
            QMessageBox.information(self, "提示", self.tr("请先打开摄像头"))
        else:
            if not self.isFaceDetection_flag:
                self.isFaceDetection_flag = True
                self.biopsy_testing_button.setText("关闭活体检测")
                self.detect_face()
                self.biopsy_testing_button.setText("活体检测")
                self.isFaceDetection_flag = False
            elif self.isFaceDetection_flag:
                self.isFaceDetection_flag = False
                self.remind_label.setText("")
                self.biopsy_testing_button.setText("活体检测")
                self.show_camera()

    # 整体活体检测
    def detect_face(self):
        if self.api.network_connect_judge():
            if not self.detect_face_network():
                return False
        if not self.detect_face_local():
            return False
        return True

    # 联网活体检测
    def detect_face_network(self):
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            frame_location = face_recognition.face_locations(frame)
            if len(frame_location) == 0:
                QApplication.processEvents()
                self.remind_label.setText("未检测到人脸")
            else:
                global PHOTO_FOLDER_PATH
                shot_path = PHOTO_FOLDER_PATH + datetime.now().strftime("%Y%m%d%H%M%S") + ".jpg"
                self.show_image.save(shot_path)
                QApplication.processEvents()
                self.remind_label.setText("正在初始化\n请稍后")
                # 百度API进行活体检测
                QApplication.processEvents()
                if not self.api.face_api_invoke(shot_path):
                    os.remove(shot_path)
                    QMessageBox.about(self, '警告', '未通过活体检测')
                    self.remind_label.setText("")
                    return False
                else:
                    os.remove(shot_path)
                    return True
            show_video = cv2.cvtColor(cv2.resize(frame, (self.WIN_WIDTH, self.WIN_HEIGHT)), cv2.COLOR_BGR2RGB)
            self.show_image = QImage(show_video.data, show_video.shape[1], show_video.shape[0], QImage.Format_RGB888)
            self.camera_label.setPixmap(QPixmap.fromImage(self.show_image))

    # 计算眼长宽比例 EAR值
    @staticmethod
    def count_EAR(eye):
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        C = dist.euclidean(eye[0], eye[3])
        EAR = (A + B) / (2.0 * C)
        return EAR

    # 计算嘴长宽比例 MAR值
    @staticmethod
    def count_MAR(mouth):
        A = dist.euclidean(mouth[1], mouth[11])
        B = dist.euclidean(mouth[2], mouth[10])
        C = dist.euclidean(mouth[3], mouth[9])
        D = dist.euclidean(mouth[4], mouth[8])
        E = dist.euclidean(mouth[5], mouth[7])
        F = dist.euclidean(mouth[0], mouth[6])  # 水平欧几里德距离
        ratio = (A + B + C + D + E) / (5.0 * F)
        return ratio

    # 计算左右脸转动比例 FR值
    @staticmethod
    def count_FR(face):
        rightA = dist.euclidean(face[0], face[27])
        rightB = dist.euclidean(face[2], face[30])
        rightC = dist.euclidean(face[4], face[48])
        leftA = dist.euclidean(face[16], face[27])
        leftB = dist.euclidean(face[14], face[30])
        leftC = dist.euclidean(face[12], face[54])
        ratioA = rightA / leftA
        ratioB = rightB / leftB
        ratioC = rightC / leftC
        ratio = (ratioA + ratioB + ratioC) / 3
        return ratio

    # 本地活体检测
    def detect_face_local(self):
        self.detect_start_time = time()

        QApplication.processEvents()
        self.remind_label.setText("正在初始化\n请稍后")
        # 特征点检测器首次加载比较慢，通过判断减少后面加载的速度
        if self.detector is None:
            self.detector = dlib.get_frontal_face_detector()
        if self.predictor is None:
            self.predictor = dlib.shape_predictor('../data/shape_predictor_68_face_landmarks.dat')

        # 闪烁阈值
        self.EAR_THRESH = 0.25
        self.MOUTH_THRESH = 0.7

        # 总闪烁次数
        self.eye_flash_counter = 0
        self.mouth_open_counter = 0
        self.turn_left_counter = 0
        self.turn_right_counter = 0

        # 连续帧数阈值
        self.EAR_CONSTANT_FRAMES = 2
        self.MOUTH_CONSTANT_FRAMES = 2
        self.LEFT_CONSTANT_FRAMES = 4
        self.RIGHT_CONSTANT_FRAMES = 4

        # 连续帧计数器
        self.eye_flash_continuous_frame = 0
        self.mouth_open_continuous_frame = 0
        self.turn_left_continuous_frame = 0
        self.turn_right_continuous_frame = 0

        print("活体检测 初始化时间:", time() - self.detect_start_time)

        # 当前总帧数
        total_frame_counter = 0

        # 设置随机值
        now_flag = 0
        random_type = [0, 1, 2, 3]
        random.shuffle(random_type)

        random_eye_flash_number = random.randint(4, 6)
        random_mouth_open_number = random.randint(2, 4)
        QMessageBox.about(self, '提示', '请按照指示执行相关动作')
        self.remind_label.setText("")

        # 抓取面部特征点的索引
        (lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
        (rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
        (mStart, mEnd) = face_utils.FACIAL_LANDMARKS_IDXS["mouth"]

        while self.cap.isOpened():
            ret, frame = self.cap.read()
            total_frame_counter += 1
            frame = imutils.resize(frame)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            rects = self.detector(gray, 0)

            if len(rects) == 1:
                QApplication.processEvents()
                shape = self.predictor(gray, rects[0])
                shape = face_utils.shape_to_np(shape)

                # 提取面部坐标
                left_eye = shape[lStart:lEnd]
                right_eye = shape[rStart:rEnd]
                mouth = shape[mStart:mEnd]

                # 计算长宽比
                left_EAR = self.count_EAR(left_eye)
                right_EAR = self.count_EAR(right_eye)
                mouth_MAR = self.count_MAR(mouth)
                leftRight_FR = self.count_FR(shape)
                average_EAR = (left_EAR + right_EAR) / 2.0

                # 计算左眼、右眼、嘴巴的凸包
                left_eye_hull = cv2.convexHull(left_eye)
                right_eye_hull = cv2.convexHull(right_eye)
                mouth_hull = cv2.convexHull(mouth)

                # 可视化
                cv2.drawContours(frame, [left_eye_hull], -1, (0, 255, 0), 1)
                cv2.drawContours(frame, [right_eye_hull], -1, (0, 255, 0), 1)
                cv2.drawContours(frame, [mouth_hull], -1, (0, 255, 0), 1)

                if now_flag >= 4:
                    self.remind_label.setText("")
                    QMessageBox.about(self, '提示', '已通过活体检测')
                    self.turn_right_counter = 0
                    self.mouth_open_counter = 0
                    self.eye_flash_counter = 0
                    return True

                if random_type[now_flag] == 0:
                    if self.turn_left_counter > 0:
                        now_flag += 1
                    else:
                        self.remind_label.setText("请向左摇头")
                        self.check_left_turn(leftRight_FR)
                        self.turn_right_counter = 0
                        self.mouth_open_counter = 0
                        self.eye_flash_counter = 0

                elif random_type[now_flag] == 1:
                    if self.turn_right_counter > 0:
                        now_flag += 1
                    else:
                        self.remind_label.setText("请向右摇头")
                        self.check_right_turn(leftRight_FR)
                        self.turn_left_counter = 0
                        self.mouth_open_counter = 0
                        self.eye_flash_counter = 0

                elif random_type[now_flag] == 2:
                    if self.mouth_open_counter >= random_mouth_open_number:
                        now_flag += 1

                    else:
                        self.remind_label.setText("已张嘴{}次\n还需张嘴{}次".format(self.mouth_open_counter, (
                                random_mouth_open_number - self.mouth_open_counter)))
                        self.check_mouth_open(mouth_MAR)
                        self.turn_right_counter = 0
                        self.turn_left_counter = 0
                        self.eye_flash_counter = 0

                elif random_type[now_flag] == 3:
                    if self.eye_flash_counter >= random_eye_flash_number:
                        now_flag += 1
                    else:
                        self.remind_label.setText("已眨眼{}次\n还需眨眼{}次".format(self.eye_flash_counter, (
                                random_eye_flash_number - self.eye_flash_counter)))
                        self.check_eye_flash(average_EAR)
                        self.turn_right_counter = 0
                        self.turn_left_counter = 0
                        self.mouth_open_counter = 0

            elif len(rects) == 0:
                QApplication.processEvents()
                self.remind_label.setText("没有检测到人脸!")

            elif len(rects) > 1:
                QApplication.processEvents()
                self.remind_label.setText("检测到超过一张人脸!")

            show_video = cv2.cvtColor(cv2.resize(frame, (self.WIN_WIDTH, self.WIN_HEIGHT)), cv2.COLOR_BGR2RGB)
            self.show_image = QImage(show_video.data, show_video.shape[1], show_video.shape[0], QImage.Format_RGB888)
            self.camera_label.setPixmap(QPixmap.fromImage(self.show_image))

            if total_frame_counter >= 1000.0:
                QMessageBox.about(self, '警告', '已超时，未通过活体检测')
                self.remind_label.setText("")
                return False

    def check_eye_flash(self, average_EAR):
        if average_EAR < self.EAR_THRESH:
            self.eye_flash_continuous_frame += 1
        else:
            if self.eye_flash_continuous_frame >= self.EAR_CONSTANT_FRAMES:
                self.eye_flash_counter += 1
            self.eye_flash_continuous_frame = 0

    def check_mouth_open(self, mouth_MAR):
        if mouth_MAR > self.MOUTH_THRESH:
            self.mouth_open_continuous_frame += 1
        else:
            if self.mouth_open_continuous_frame >= self.MOUTH_CONSTANT_FRAMES:
                self.mouth_open_counter += 1
            self.mouth_open_continuous_frame = 0

    def check_right_turn(self, leftRight_FR):
        if leftRight_FR <= 0.5:
            self.turn_right_continuous_frame += 1
        else:
            if self.turn_right_continuous_frame >= self.RIGHT_CONSTANT_FRAMES:
                self.turn_right_counter += 1
            self.turn_right_continuous_frame = 0

    def check_left_turn(self, leftRight_FR):
        if leftRight_FR >= 2.0:
            self.turn_left_continuous_frame += 1
        else:
            if self.turn_left_continuous_frame >= self.LEFT_CONSTANT_FRAMES:
                self.turn_left_counter += 1
            self.turn_left_continuous_frame = 0

    # ----------------- 背景模糊 ------------------ #
    # 背景模糊判别器
    def fine_segmentation_judge(self):
        if not self.cap.isOpened():
            QMessageBox.information(self, "提示", self.tr("请先打开摄像头"))
        else:
            if not self.isFineSegmentation_flag:
                self.isFineSegmentation_flag = True
                self.fine_segmentation_button.setText("关闭背景模糊")
                self.fine_segmentation()
                self.fine_segmentation_button.setText("背景模糊")
                self.isFineSegmentation_flag = False

            elif self.isFineSegmentation_flag:
                self.isFineSegmentation_flag = False
                self.fine_segmentation_button.setText("背景模糊")
                self.show_camera()

    # 背景模糊
    def fine_segmentation(self):
        mp_selfie_segmentation = mp.solutions.selfie_segmentation
        BG_COLOR = (192, 192, 192)
        with mp_selfie_segmentation.SelfieSegmentation(model_selection=1) as selfie_segmentation:
            while self.cap.isOpened():
                ret, frame = self.cap.read()
                QApplication.processEvents()
                # 将 BGR 图像转换为 RGB
                in_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # 若要提高性能，可以选择将图像标记为不可写以通过引用传递。
                in_frame.flags.writeable = False
                results = selfie_segmentation.process(in_frame)

                in_frame.flags.writeable = True
                in_frame = cv2.cvtColor(in_frame, cv2.COLOR_RGB2BGR)
                # 在背景图像上绘制分割
                condition = np.stack((results.segmentation_mask,) * 3, axis=-1) > 0.1
                # 背景设置为高斯模糊
                gauss_image = cv2.GaussianBlur(in_frame, (85, 85), 0)
                if gauss_image is None:
                    gauss_image = np.zeros(in_frame.shape, dtype=np.uint8)
                    gauss_image[:] = BG_COLOR

                out_frame = np.where(condition, in_frame, gauss_image)

                show_video = cv2.cvtColor(cv2.resize(out_frame, (self.WIN_WIDTH, self.WIN_HEIGHT)), cv2.COLOR_BGR2RGB)
                self.show_image = QImage(show_video.data, show_video.shape[1], show_video.shape[0],
                                         QImage.Format_RGB888)
                self.camera_label.setPixmap(QPixmap.fromImage(self.show_image))

    # ----------------- 姿态检测 ------------------ #
    # 姿态检测判别器
    def criticalPoint_detection_judge(self):
        if not self.cap.isOpened():
            QMessageBox.information(self, "提示", self.tr("请先打开摄像头"))
        else:
            if not self.isAttitudeDetection_flag:
                self.isAttitudeDetection_flag = True
                self.attitude_detection_button.setText("关闭姿态检测")
                self.attitude_detection()
                self.attitude_detection_button.setText("姿态检测")
                self.isAttitudeDetection_flag = False

            elif self.isAttitudeDetection_flag:
                self.isAttitudeDetection_flag = False
                self.attitude_detection_button.setText("姿态检测")
                self.show_camera()

    # 姿态检测
    def attitude_detection(self):
        mp_pose = mp.solutions.pose  # 姿态识别方法
        pose = mp_pose.Pose(static_image_mode=False, smooth_landmarks=True,
                            min_detection_confidence=0.5, min_tracking_confidence=0.5)
        mp_draw = mp.solutions.drawing_utils
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            QApplication.processEvents()
            imgRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(imgRGB)
            if results.pose_landmarks:  # 如果检测到体态
                mp_draw.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)  # 绘制姿态坐标点

            show_video = cv2.cvtColor(cv2.resize(frame, (self.WIN_WIDTH, self.WIN_HEIGHT)), cv2.COLOR_BGR2RGB)
            self.show_image = QImage(show_video.data, show_video.shape[1], show_video.shape[0],
                                     QImage.Format_RGB888)
            self.camera_label.setPixmap(QPixmap.fromImage(self.show_image))

    # ----------------- 对象提取 ------------------ #
    # 对象提取判别器
    def object_extraction_judge(self):
        if not self.cap.isOpened():
            QMessageBox.information(self, "提示", self.tr("请先打开摄像头"))
        else:
            if not self.isObjectExtraction_flag:
                self.isObjectExtraction_flag = True
                self.object_extraction_button.setText("关闭对象提取")
                self.object_detection()
                self.object_extraction_button.setText("对象提取")
                self.isObjectExtraction_flag = False

            elif self.isObjectExtraction_flag:
                self.isObjectExtraction_flag = False
                self.object_extraction_button.setText("对象提取")
                self.show_camera()

    # 获取参数窗口
    def show_dialog(self):
        # 创建一个QInputDialog对象
        dialog = QInputDialog(self)
        dialog.setWindowTitle('HSV')
        dialog.setLabelText('请输入HSV，用英文逗号分隔：')
        user_exists = True
        while user_exists:
            # 调用exec_方法显示对话框，并获取用户输入的值和点击的按钮
            value, ok = dialog.getText(dialog, 'HSV', '请输入HSV，用英文逗号分隔：')
            # 判断用户是否点击了确定按钮
            if ok:
                # print('success')
                try:
                    # 将用户输入的值按逗号分割
                    params = [int(x) for x in value.split(',')]
                    # 判断参数个数是否为3
                    if len(params) == 3:
                        # 将参数赋值给self.H,self.S,self.V
                        self.H, self.S, self.V = params
                        self.cancel_flag = True
                        user_exists = False
                        break
                    else:
                        QMessageBox.information(self, "提示", self.tr("参数不规范，请重新输入！"))
                except:
                    # 打印错误信息
                    QMessageBox.information(self, "提示", self.tr("参数不规范，请重新输入！"))
            else:
                self.cancel_flag = False
                break

    # 对象提取
    def object_detection(self):
        # 创建一个获取参数的窗口
        self.cancel_flag = True
        self.show_dialog()
        QApplication.processEvents()

        while self.cap.isOpened() and self.cancel_flag:
            ret, frame = self.cap.read()
            QApplication.processEvents()

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            # 在PS里用取色器的HSV
            psHSV = [self.H, self.S, self.V]
            diff = 40  # 上下浮动值
            lowerHSV = [(psHSV[0] - diff) / 2, (psHSV[1] - diff) * 255 / 100,
                        (psHSV[2] - diff) * 255 / 100]
            upperHSV = [(psHSV[0] + diff) / 2, (psHSV[1] + diff) * 255 / 100,
                        (psHSV[2] + diff) * 255 / 100]

            mask = cv2.inRange(hsv, np.array(lowerHSV), np.array(upperHSV))
            # 使用位“与运算”提取颜色部分
            res = cv2.bitwise_and(frame, frame, mask=mask)
            # 使用高斯模式优化图片
            res = cv2.GaussianBlur(res, (5, 5), 1)
            show_video = cv2.resize(res, (self.WIN_WIDTH, self.WIN_HEIGHT))
            show_video = cv2.cvtColor(show_video, cv2.COLOR_BGR2RGB)
            self.show_image = QImage(show_video.data, show_video.shape[1], show_video.shape[0], QImage.Format_RGB888)
            self.camera_label.setPixmap(QPixmap.fromImage(self.show_image))

    # 关闭主窗口
    def close_window(self):
        if self.cap.isOpened():
            self.cap.release()
            self.close()
        else:
            self.close()


class FaceCompareWindow(QMainWindow, FaceCompareUi):
    def __init__(self):
        super(FaceCompareWindow, self).__init__()
        self.setupUi(self)

        self.imgA_path = ""
        self.imgA = None

        self.img_a_button.clicked.connect(self.open_imgA)
        self.compare_button.clicked.connect(self.compare_face)
        self.close_button.clicked.connect(self.close_window)
        self.minimize_button.clicked.connect(self.showMinimized)

    def open_imgA(self):
        imgA_path, fileType = QtWidgets.QFileDialog.getOpenFileName(self, "选取文件", os.getcwd(),
                                                                    "All Files(*);;Text Files(*.txt)")
        if not imgA_path.endswith('jpg') | imgA_path.endswith('png'):
            QMessageBox.about(self, '提示', '请选择jpg或者png类型图片')
        else:
            QApplication.processEvents()
            # self.imgA = imgA
            self.imgA_path = imgA_path
            img = cv2.imread(imgA_path)  # 读取图片
            show = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # 显示原图
            showImage = QImage(show.data, show.shape[1], show.shape[0], show.shape[1] * 3, QImage.Format_RGB888)
            self.img_a_show.setPixmap(QPixmap.fromImage(showImage))
            self.img_a_path.setText(imgA_path)

    def compare_face(self):
        if self.imgA_path == "":
            QMessageBox.information(self, "提示", self.tr("请先导入图片"))
        else:
            try:
                print(self.imgA_path)
                img = cv2.imread(self.imgA_path)  # 读取图片
                # img = cv2.resize(imgA, (510, 300))  # 截取图片
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # 转换灰色
                # OpenCV人脸识别分类器
                classifier = cv2.CascadeClassifier(
                    "C:\\opencv\\opencv-master\\data\\haarcascades\\haarcascade_frontalface_default.xml"
                )
                color = (0, 255, 0)  # 定义绘制颜色
                # 调用识别人脸
                faceRects = classifier.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=3, minSize=(32, 32))
                if len(faceRects):  # 大于0则检测到人脸
                    for faceRect in faceRects:  # 单独框出每一张人脸
                        x, y, w, h = faceRect
                        # 框出人脸
                        cv2.rectangle(img, (x, y), (x + h, y + w), color, 2)
                    show = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # 显示图像
                    showImage = QImage(show.data, show.shape[1], show.shape[0], show.shape[1] * 3, QImage.Format_RGB888)
                    self.img_a_show.setPixmap(QPixmap.fromImage(showImage))
                else:
                    QMessageBox.information(self, "提示", self.tr("没有检测到人脸，请重新导入图片!"))
            except IndexError:
                QMessageBox.information(self, "提示", self.tr("图片导入失败，请重新导入图片!"))
                quit()

    def close_window(self):
        self.img_a_show.setText("图片")
        self.img_a_path.setText("")
        self.imgA_path = ""
        self.imgA = None
        self.close()


class ImgTxtWindow(QMainWindow, ImageTxtUi):
    def __init__(self):
        super(ImgTxtWindow, self).__init__()
        self.setupUi(self)

        self.imgA_path = ""
        self.imgA = None

        self.img_a_button.clicked.connect(self.open_imgA)
        self.compare_button.clicked.connect(self.compare_face)
        self.close_button.clicked.connect(self.close_window)
        self.minimize_button.clicked.connect(self.showMinimized)

    def open_imgA(self):
        imgA_path, fileType = QtWidgets.QFileDialog.getOpenFileName(self, "选取文件", os.getcwd(),
                                                                    "All Files(*);;Text Files(*.txt)")
        if not imgA_path.endswith('jpg') | imgA_path.endswith('png'):
            QMessageBox.about(self, '提示', '请选择jpg或者png类型图片')
        else:
            QApplication.processEvents()
            # self.imgA = imgA
            self.imgA_path = imgA_path
            self.img_a_path.setText(imgA_path)

    def compare_face(self):
        if self.imgA_path == "":
            QMessageBox.information(self, "提示", self.tr("请先导入图片"))
        else:
            try:
                print(self.imgA_path)
                text = pytesseract.image_to_string(Image.open(self.imgA_path), lang='chi_sim')
                # print(text)
                if text != "":
                    self.img_a_show.setText(text)
                else:
                    QMessageBox.information(self, "提示", self.tr("未识别到文本内容，请重新导入图片!"))
            except IndexError:
                QMessageBox.information(self, "提示", self.tr("图片导入失败，请重新导入图片!"))
                quit()

    def close_window(self):
        self.img_a_show.setText("图片")
        self.img_a_path.setText("")
        self.imgA_path = ""
        self.imgA = None
        self.close()


if __name__ == "__main__":
    ui_start_time = time()
    app = QApplication(sys.argv)

    # 主界面
    user_win = UserMainWindow()
    # 次界面
    faceCompare = FaceCompareWindow()
    imgTxt = ImgTxtWindow()

    # user_win.signal_register.connect(register.show)
    # user_win.signal_modify.connect(modify.show)
    user_win.signal_compare.connect(faceCompare.show)
    user_win.signal_txt.connect(imgTxt.show)

    user_win.show()

    print('用户界面 初始化时间:', time() - ui_start_time)

    sys.exit(app.exec_())
