import cv2
import imutils

img = cv2.imread('images/tetris_blocks.png')
cv2.imshow("Image", img)

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
cv2.imshow('Image: Gray', gray)

edged = cv2.Canny(gray, 30, 150)
cv2.imshow("Image: Edged", edged)

thresh = cv2.threshold(gray, 225, 255, cv2.THRESH_BINARY_INV)[1]
cv2.imshow("Image: Thresh", thresh)

mask = thresh.copy()
mask = cv2.erode(mask, None, iterations=5)
cv2.imshow("Image: Eroded", mask)

dmask = img.copy()
dmask = cv2.dilate(dmask, None, iterations=5)
cv2.imshow("Image: Dilated", dmask)

contours = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
contours = imutils.grab_contours(contours)
output = img.copy()
for i in range(len(contours)):
    c = contours[i]
    print('CONTOUR %d' % i)
    print(c)
    cv2.drawContours(output, [c], -1, (240,0, 159), 3)
    cv2.imshow("Contours", output)
    print("\n\nagagaga")
    for aga in c:
        print(aga)
        for aba in aga:
            print("aba %s" % str(aba))

hsvimg = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)[:,:,1]

hsvthresh = cv2.threshold(hsvimg, 200, 255, cv2.THRESH_BINARY)[1]
# hsvthreshed2bgr = cv2.cvtColor(hsvthresh, cv2.COLOR_HSV2BGR)
cv2.imshow("HSV Image: Thresh", hsvthresh)

cv2.waitKey(0)


