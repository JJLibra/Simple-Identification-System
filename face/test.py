import cv2
import numpy as np


def blur_demo(image):
    """
    均值模糊 : 去随机噪声有很好的去噪效果
    （1, 15）是垂直方向模糊，（15， 1）是水平方向模糊
    """
    dst = cv2.blur(image, (1, 15))
    cv2.imshow("avg_blur_demo", dst)


def median_blur_demo(image):  # 中值模糊  对椒盐噪声有很好的去燥效果
    dst = cv2.medianBlur(image, 5)
    cv2.imshow("median_blur_demo", dst)


def custom_blur_demo(image):
    """
    用户自定义模糊
    下面除以25是防止数值溢出
    """
    kernel = np.ones([5, 5], np.float32) / 25
    dst = cv2.filter2D(image, -1, kernel)
    cv2.imshow("custom_blur_demo", dst)


src = cv2.imread("./img/test1.png")
img = cv2.resize(src, None, fx=0.8, fy=0.8, interpolation=cv2.INTER_CUBIC)
cv2.imshow('input_image', img)

blur_demo(img)
median_blur_demo(img)
custom_blur_demo(img)

cv2.waitKey(0)
cv2.destroyAllWindows()
