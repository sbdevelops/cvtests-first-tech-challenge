from collections.abc import Iterable
import cv2
import imutils
from util import *


def show_and_pointer(image, name):
    def on_image_changed(nothing):
        img_cpy = image.copy()
        pt_x = cv2.getTrackbarPos("X", name)
        pt_y = cv2.getTrackbarPos("Y", name)
        res = image[pt_y, pt_x]
        icat_res = inverse_color(res)
        cv2.circle(img_cpy, (pt_x, pt_y), 5, icat_res, 3)

        txt_res = image[5, 30]
        txt_icat_res = inverse_color(txt_res)
        cv2.putText(img_cpy, f"{res}", (5, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, txt_icat_res, 2)

        # print(f"changed to {res}")
        # print(f"inverse is {~res}")
        cv2.imshow(name, img_cpy)

    cv2.namedWindow(name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(name, 600, 500)
    cv2.createTrackbar("X", name, 0, image.shape[1], on_image_changed)
    cv2.createTrackbar("Y", name, 0, image.shape[0], on_image_changed)
    on_image_changed(None)


img = cv2.imread('images/ps_R1.jpg')
img = cv2.medianBlur(img, 5)
img = img[400:700, :]

show_and_pointer(img, "Image: Input")

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
show_and_pointer(hsv, "Image: HSV")

hsv_threshed_low = cv2.inRange(
    src=hsv,
    lowerb=(0, 130, 30),
    upperb=(3, 220, 255)
)

hsv_threshed_high = cv2.inRange(
    src=hsv,
    lowerb=(170, 130, 30),
    upperb=(180, 220, 255)
)

hsv_threshed = cv2.bitwise_or(hsv_threshed_low, hsv_threshed_high)

img_masked_to_thresh_eroded = cv2.erode(hsv_threshed, None, iterations=4)
show_and_pointer(img_masked_to_thresh_eroded, "Image: HSV: Threshed: Eroded")

# img_masked_to_thresh_eroded = cv2.dilate(hsv_threshed, None, iterations=5)
# show_and_pointer(img_masked_to_thresh_eroded, "Image: HSV: Threshed: Dilated")


contours = cv2.findContours(img_masked_to_thresh_eroded.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
contours = imutils.grab_contours(contours)
output = img.copy()
for i in range(len(contours)):

    c = contours[i]

    x_positions = [pt[0, 0] for pt in c]
    y_positions = [pt[0, 1] for pt in c]
    # print(x_positions)
    min_pt = (min(x_positions), min(y_positions))
    if not 75 < min_pt[1] < 140:
        continue

    print('CONTOUR %d' % i)
    # print(c)
    print(f'MIN: x{min_pt[0]} y{min_pt[1]}')
    cv2.circle(output, min_pt, 5, inverse_color_at_point(output, min_pt), 2)

    max_pt = (max(x_positions), max(y_positions))
    print(f'MIN: x{max_pt[0]} y{max_pt[1]}')
    cv2.circle(output, max_pt, 5, inverse_color_at_point(output, max_pt), 2)

    height = max_pt[1] - min_pt[1]
    width = max_pt[0] - min_pt[0]
    ratio = width / height
    print(f"Width: {width}; height: {height}; ratio: {ratio}")

    found_statement = f"Found a stack with {'four' if ratio < 3 else 'one'}"
    print(found_statement)
    cv2.putText(output, found_statement, (5, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, inverse_color_at_point(output, (5, 60)),
                2)
    # cv2.rectangle(output, min_pt, max_pt, inverse_color_at_point(output, min_pt), 10)

    leng = cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, 0.02 * leng, True)
    print("THE LENGTH OF THIS CONTOUR IS %d\n\n" % len(approx))
    cv2.line(output, (int((min_pt[0] + max_pt[0]) / 2), 0), (int((min_pt[0] + max_pt[0]) / 2), output.shape[0]), (0, 60, 255), 3)
    cv2.drawContours(output, [approx], -1, (150, 0, 10), 3)
show_and_pointer(output, "Output")

# img_masked_to_thresh_blurred = cv2.medianBlur(img_masked_to_thresh, 5)
# show_and_pointer(img_masked_to_thresh_blurred, "Image: HSV: Threshed: #toRGB: Masked: Blurred")
cv2.waitKey(0)
