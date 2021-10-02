import imutils
from util import *
import serial

serial_active = False
ser = None

# Assign window name and instantiate image feed
window_name = "Image"
# feed = PreLoadedImage("images/ps_R2.jpg")
feed = VideoFeed(window_name, 1)
# feed = VideoPlayback(window_name, "images/psV_1.mov")

# Create window and setup image feed
cv2.namedWindow(window_name, cv2.WINDOW_KEEPRATIO)
cv2.resizeWindow(window_name, 1500, 1000)
feed.setup()
feed.get_frame()

cv2.createTrackbar("Top Cutoff", window_name, 0, feed.stats.height - 1, nothing)
cv2.createTrackbar("Bottom Cutoff", window_name, 870, feed.stats.height - 1, nothing)
cv2.createTrackbar("Lower Hue Cutoff", window_name, 6, 30, nothing)
cv2.createTrackbar("Upper Hue Cutoff", window_name, 170, 180, nothing)
cv2.createTrackbar("Lower Sat Cutoff", window_name, 100, 255, nothing)
cv2.createTrackbar("Upper Sat Cutoff", window_name, 220, 255, nothing)
cv2.createTrackbar("Area Cutoff", window_name, 450, 2000, nothing)
cv2.createTrackbar("Num Sides Cutoff", window_name, 6, 15, nothing)
cv2.createTrackbar("Aspect Cutoff Low (x0.1)", window_name, 1, 15, nothing)
cv2.createTrackbar("Aspect Cutoff High (x0.1)", window_name, 7, 15, nothing)
cv2.createTrackbar("Erode Iterations", window_name, 1, 15, nothing)
cv2.createTrackbar("Draw Contours", window_name, 1, 1, nothing)
cv2.createTrackbar("Contour Approx (x0.01)", window_name, 4, 10, nothing)
cv2.createTrackbar("TARGET PS Index", window_name, 0, 2, nothing)
cv2.createTrackbar("TARGET X Position", window_name, 460, feed.stats.width - 1, nothing)
cv2.createTrackbar("Output Index", window_name, 0, 3, nothing)
cv2.createTrackbar("Refresh Rate", window_name, 100, 2000, nothing)

while True:

    if not serial_active:
        try:
            ser = serial.Serial('/dev/cu.usbmodem14101', 9600, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE)
            serial_active = True
            print("Successfully created serial device")
        except serial.SerialException as e:
            print("Could not generate serial device. Will try again")

    # Get trackbar vars at beginning
    (top_cutoff, bottom_cutoff,
     lower_hue_cutoff, upper_hue_cutoff, lower_sat_cutoff, upper_sat_cutoff,
     area_cutoff, num_sides_cutoff,
     aspect_cutoff_low, aspect_cutoff_high,
     erode_iterations, draw_contours, contour_approx,
     target_power_shot_index, target_x_position,
     output_index, refresh_rate) = \
        get_trackbar_vars_as_tuple(window_name,
                                   "Top Cutoff", "Bottom Cutoff",
                                   "Lower Hue Cutoff", "Upper Hue Cutoff", "Lower Sat Cutoff", "Upper Sat Cutoff",
                                   "Area Cutoff", "Num Sides Cutoff",
                                   "Aspect Cutoff Low (x0.1)", "Aspect Cutoff High (x0.1)",
                                   "Erode Iterations", "Draw Contours", "Contour Approx (x0.01)",
                                   "TARGET PS Index", "TARGET X Position",
                                   "Output Index", "Refresh Rate")

    # Get the image from the camera feed. Also cut off top and bottom regions as desired.
    image = feed.get_frame()[top_cutoff:bottom_cutoff, :]

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    hsv_threshed = cv2.inRange(
        src=hsv,
        lowerb=(10, 210, 0),
        upperb=(25, 255, 255)
    )
    # hsv_threshed_3channels = cv2.cvtColor(hsv_threshed, cv2.COLOR_GRAY2BGR)
    # show_and_pointer(hsv_threshed, "Image: HSV: Threshed")

    # img_masked_to_thresh = cv2.bitwise_and(img, hsv_threshed_3channels)
    # show_and_pointer(img_masked_to_thresh, "Image: HSV: Threshed: #toRGB: Masked")

    img_masked_to_thresh_eroded = cv2.erode(hsv_threshed, None, iterations=5)
    height, width, channels = image.shape
    contours = cv2.findContours(img_masked_to_thresh_eroded.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)
    output = image.copy()
    if len(contours) > 0:
        i = 0

        c = contours[i]
        print('CONTOUR %d' % i)
        print(c)
        x_positions = [pt[0, 0] for pt in c]
        y_positions = [pt[0, 1] for pt in c]
        print(x_positions)
        min_pt = (min(x_positions), min(y_positions))
        print(f'MIN: x{min_pt[0]} y{min_pt[1]}')
        cv2.circle(output, min_pt, 5, inverse_color_at_point(output, min_pt), 2)

        max_pt = (max(x_positions), max(y_positions))
        print(f'MIN: x{max_pt[0]} y{max_pt[1]}')
        cv2.circle(output, max_pt, 5, inverse_color_at_point(output, max_pt), 2)

        height = max_pt[1] - min_pt[1]
        width = max_pt[0] - min_pt[0]
        ratio = width / height
        mid_x = min_pt[0] + width / 2
        print(f"Width: {width}; height: {height}; ratio: {ratio}")

        found_statement = f"Found a stack with {'four' if ratio < 3 else 'one'}"
        print(found_statement)
        cv2.putText(output, found_statement, (5, 60), cv2.FONT_HERSHEY_SIMPLEX, 1,
                    inverse_color_at_point(output, (5, 60)), 2)
        cv2.rectangle(output, min_pt, max_pt, inverse_color_at_point(output, min_pt), 10)

        cv2.drawContours(output, [c], -1, (240, 0, 159), 3)

        if serial_active:
            ser.write(bytearray([0, 14 if ratio < 3 else 11, 20 + 180 * (mid_x / float(width)),3]))
    else:
        if serial_active:
            ser.write(bytearray([0,1,2,3]))

    # Show the image and wait for specified duration
    cv2.imshow(window_name, output)
    cv2.waitKey(refresh_rate)
    print("\n")
