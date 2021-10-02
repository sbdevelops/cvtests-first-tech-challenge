import imutils
from util import *

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

cv2.createTrackbar("Top Cutoff", window_name, 640, feed.stats.height - 1, nothing)
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

    # Convert to HLS color space
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Threshold image to get lower red->orange hues
    thresh_low = cv2.inRange(
        src=hsv,
        lowerb=(0, lower_sat_cutoff, 30),
        upperb=(lower_hue_cutoff, upper_sat_cutoff, 255)
    )

    # Threshold image to get upper pink->red hues
    thresh_high = cv2.inRange(
        src=hsv,
        lowerb=(upper_hue_cutoff, lower_sat_cutoff, 30),
        upperb=(180, upper_sat_cutoff, 255)
    )

    # Combine the threshold results
    thresh = cv2.bitwise_or(thresh_low, thresh_high)

    # Erode the image
    eroded = cv2.erode(thresh, None, iterations=erode_iterations)

    # Determine what our output image will be
    output_choices = (image, hsv, thresh, eroded)
    output = output_choices[output_index].copy()
    output_stats = ImageStats(output)

    # Get image contours
    contours_tuple = cv2.findContours(eroded.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours_tuple)
    num_contours = len(contours)

    # Iterate over contours. First create a list of contour information
    contour_info = []
    for contour_index in range(num_contours):
        # Get our current contour in for loop
        contour = contours[contour_index]

        # Get a list of all x and y positions
        x_positions = [pt[0, 0] for pt in contour]
        y_positions = [pt[0, 1] for pt in contour]

        # Get our minimum and maximum point
        min_point = (min(x_positions), min(y_positions))
        max_point = (max(x_positions), max(y_positions))

        # Compute width, height, and area
        width = max_point[0] - min_point[0]
        height = max_point[1] - min_point[1]
        area = width * height

        # Compute the aspect ratio of the contour
        aspect_ratio = width / height

        # Compute the number of sides on the contour
        arc_length = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, contour_approx * 0.01 * arc_length, True)
        num_sides = len(approx)

        # Cutoff if needed
        if area < area_cutoff or not aspect_cutoff_low*0.1 < aspect_ratio < aspect_cutoff_high*0.1 or num_sides > num_sides_cutoff:
            continue

        # Print some information
        print("Contour %d with %d sides and aspect ratio %.2f and area %d" %
              (contour_index, num_sides, aspect_ratio, area))
        contour_info.append(
            (contour_index, num_sides, aspect_ratio, min_point, max_point)
        )

        # If permitted, draw around the contours
        if draw_contours:
            # Draw text showing the aspect ratio
            cv2.putText(output, "%d@%.2f@%d@c%d" % (num_sides, aspect_ratio, area, contour_index),
                        min_point, cv2.FONT_HERSHEY_SIMPLEX, 0.5, inverse_color_at_point(output, min_point), 1)

            # Draw a rectangle using min and max points
            cv2.rectangle(output, min_point, max_point, inverse_color_at_point(output, max_point), 4)

            # Draw a vertical line marking middle of contour
            contour_mid_x = int((min_point[0] + max_point[0]) / 2)
            cv2.line(output, (contour_mid_x, 0), (contour_mid_x, output_stats.height - 1),
                     inverse_color_at_point(output, min_point), 2)

    # If there are more than three contours left, we must eliminate extras
    if len(contour_info) > 3:
        # Get the mean of the minimum y positions of remaining contours
        mean = sum([contour[3][1] for contour in contour_info]) / len(contour_info)
        print("Mean top pos is %.2f" % mean)

        # Sort contours by distance from mean to eliminate furthest contours
        contour_info.sort(key=lambda elem: elem[3][0], reverse=False)
        contour_info = contour_info[:3]

    # We will perform additional computations if we see three power shots
    if len(contour_info) == 3:
        # Print something just to separate previous printouts
        print("After sort - there are three contours!")

        # Re-sort the contours
        contour_info.sort(key=lambda elem: elem[3][0])

        # For each contour, print out the index and contour number, just for reference
        for contour_index in range(len(contour_info)):
            current_info = contour_info[contour_index]
            print("%d: Contour %d with left=%d" % (contour_index, current_info[0], current_info[3][0]))

        # Get the distance between two of the contours. Via tuple pos 3 aka min_point
        pixel_dist_between_contours = abs(contour_info[0][3][0] - contour_info[1][3][0])

        # Use distance between contours to determine pixels per inch
        pixels_per_inch = pixel_dist_between_contours / 7.5
        print("Pixels per inch = %.2f" % pixels_per_inch)

        # Put a circle on the contour that we are targeting
        target_contour_info = contour_info[target_power_shot_index]
        print("Target power shot index is %d" % target_power_shot_index)
        target_contour_mid_point = (int((target_contour_info[3][0] + target_contour_info[4][0]) / 2),
                                    int((target_contour_info[3][1] + target_contour_info[4][1]) / 2))

        targets_dist_in = (target_x_position - target_contour_mid_point[0]) * (1 / pixels_per_inch)

        print("%s  Distance:%.2fin." %
                        ("Move RIGHT -->" if targets_dist_in < 0 else "<-- Move LEFT", -targets_dist_in))

        if draw_contours:
            # Draw a circle on top of our chosen contour
            cv2.circle(output,
                       target_contour_mid_point,
                       10,
                       inverse_color_at_point(output, target_contour_mid_point),
                       4)

            # Draw our ideal target line
            cv2.line(output, (target_x_position, 0), (target_x_position, output_stats.height-1),
                     (0, 220, 0) if output_stats.channels > 1 else 255, 4)

            # Draw the line from chosen contour to ideal target
            cv2.line(output, (target_contour_mid_point[0], target_contour_mid_point[1]),
                     (target_x_position, target_contour_mid_point[1]),
                     (0, 255, 0) if output_stats.channels > 1 else 255, 4)

            # Put text indicating distance to target and direction
            cv2.putText(output,
                        "%s  Distance:%.2fin." %
                        ("Move RIGHT -->" if targets_dist_in < 0 else "<-- Move LEFT", -targets_dist_in),
                        (15,30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        inverse_color_at_point(output, (15,30)),
                        2)

            if abs(targets_dist_in) < 1:
                cv2.putText(output, "SHOOT NOW!", (15, 70),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            inverse_color_at_point(output, (15,70)),
                            2)

    # Show the image and wait for specified duration
    cv2.imshow(window_name, output)
    cv2.waitKey(refresh_rate)
    print("\n")
