import argparse
import cv2
from collections.abc import Iterable

#
# DEFAULT VARIABLES
#
#

# For the image
# preloaded_image_name = 'virtualrings.png'
preloaded_image_name = 1
window_name = 'Image'
window_name_gray = "Image (Gray)"
num_rectangles = 4

# For the bounding boxes
SPACE_DEFAULT = 0
CHANNEL_DEFAULT = 0
CENTER_X_DEFAULT = 721
CENTER_Y_DEFAULT = 878
WIDTH_DEFAULT = 526
HEIGHT_DEFAULT = 126
SPACING_DEFAULT = 0
SEARCH_SPACE_DEFAULT = 5
REFRESH_RATE_DEFAULT = 50

# Names only, not to be changed
image = None
gray = None
img_height = 0
img_width = 0
shape = None
camera = None


#
# USEFUL FUNCTIONS
#
#
def redo_image_stats():
    global image
    global gray
    global img_width
    global img_height
    global shape
    if image is not None:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        shape = image.shape
        img_height = shape[0]
        img_width = shape[1]


def constrain(num, minimum, maximum):
    return min(max(minimum, num), maximum)


def nothing(none):
    pass


def get_trackbar_vars(*v):
    return {n: cv2.getTrackbarPos(n, window_name) for n in v}


def get_trackbar_vars_as_tuple(*v):
    return tuple([cv2.getTrackbarPos(n, window_name) for n in v])


def inverse_color_at_point(point_order_of_xy: tuple):
    # Determine the color we should use for the text, by getting the inverse color at the text's start point
    color = new_image[point_order_of_xy[1]][point_order_of_xy[0]]
    inverse_color = ~color
    # Convert this inverse color to a tuple and then print it
    inverse_color_as_tuple = \
        [int(x) for x in inverse_color] if isinstance(inverse_color, Iterable) else int(inverse_color)
    print(inverse_color_as_tuple)
    return inverse_color_as_tuple


def contrain_point_in_image(pt):
    return constrain(pt[0], 0, shape[1]-1), constrain(pt[1], 0, shape[0]-1)


class Rectangle:
    def __init__(self, top_left_x, top_left_y, rect_width, rect_height):
        self.top_left_xy = contrain_point_in_image((top_left_x, top_left_y))
        self.bottom_right_xy = contrain_point_in_image((top_left_x + rect_width, top_left_y + rect_height))

        self.left_x = self.top_left_xy[0]
        self.right_x = self.bottom_right_xy[0]
        self.top_y = self.top_left_xy[1]
        self.bottom_y = self.bottom_right_xy[1]


# Get the valid BGR to ____ color space conversions
valid_color_spaces = {k: v for k, v in vars(cv2).items() if 'COLOR_BGR2' in k}
# keys = list(valid_color_spaces.keys())
keys = (
    ('BGR2GRAY', cv2.COLOR_BGR2GRAY),
    ('BGR2RGB', cv2.COLOR_BGR2RGB),
    ('BGR2LAB', cv2.COLOR_BGR2LAB),
    ('BGR2HLS', cv2.COLOR_BGR2HLS),
    ('BGR2HSV', cv2.COLOR_BGR2HSV)
)
print(keys)

#
# READ THE IMAGE AND DETERMINE PROPERTIES
#
#
if type(preloaded_image_name) is str:
    using_camera_feed = False
    image = cv2.imread(preloaded_image_name)
    redo_image_stats()
else:
    using_camera_feed = True
    camera = cv2.VideoCapture(preloaded_image_name)
    ret, image = camera.read()
    redo_image_stats()

print(shape)
# cv2.imshow(window_name, image)
# cv2.imshow(window_name_gray, gray)
# cv2.waitKey(0)

# Create our window
cv2.namedWindow(window_name, cv2.WINDOW_KEEPRATIO)

# Create trackbars to determine color space and channels
cv2.createTrackbar('Space', window_name, SPACE_DEFAULT, len(keys), nothing)
cv2.createTrackbar('Channel', window_name, CHANNEL_DEFAULT, 1, nothing)
# Create trackbars for the center point
cv2.createTrackbar('Center X', window_name, CENTER_X_DEFAULT, img_width, nothing)
cv2.createTrackbar('Center Y', window_name, CENTER_Y_DEFAULT, img_height, nothing)
# Create trackbar for the width, and then the ratio to determine height
cv2.createTrackbar('Width', window_name, WIDTH_DEFAULT, img_width, nothing)
cv2.createTrackbar('Height', window_name, HEIGHT_DEFAULT, img_height, nothing)
# Create trackbar for the spacing
cv2.createTrackbar('Spacing', window_name, SPACING_DEFAULT, int(img_height / 4), nothing)
# Create trackbar to determine search params
cv2.createTrackbar('Search Space', window_name, SEARCH_SPACE_DEFAULT, 20, nothing)
cv2.createTrackbar('Refresh Rate', window_name, REFRESH_RATE_DEFAULT, 2000, nothing)

while True:
    #
    # Refresh image frame, get color space and channels
    #
    #
    if using_camera_feed and camera is not None:
        ret, image = camera.read()
    redo_image_stats()

    # Get the desired color space, by obtaining the index from our list
    desired_space_number = cv2.getTrackbarPos('Space', window_name)
    print(f'desired_space_number: {desired_space_number}')
    # If index != 0, then find the color space. If index == 0, then keep the BGR color space
    if desired_space_number != 0:
        desired_space = keys[desired_space_number - 1]
        print(desired_space)
        desired_space_name = desired_space[0]
        desired_space_code = desired_space[1]
        new_image = cv2.cvtColor(image, desired_space_code)
    else:
        desired_space_name = 'NO CHANGE'
        new_image = image.copy()

    # Get the possible channels and apply min/max to trackbar
    new_image_shape = new_image.shape
    num_channels_for_trackbar = new_image_shape[2] if len(new_image_shape) >= 3 else 0
    cv2.setTrackbarMax('Channel', window_name, num_channels_for_trackbar)

    # Get the currently selected channel index
    channel_index = min(num_channels_for_trackbar, cv2.getTrackbarPos('Channel', window_name))
    # Split the image to one channel if index != 0, otherwise keep image the same
    if channel_index != 0:
        # Create a variable for the new image with the single channel
        new_image_single_channel = new_image[:, :, channel_index - 1]

        # Go through each channel of the image and set it to 0 if it's not our selected channel
        for index in range(0, num_channels_for_trackbar):
            if index != channel_index - 1:
                new_image[:, :, index] = 0
    elif num_channels_for_trackbar == 0:
        new_image_single_channel = new_image
    else:
        new_image_single_channel = None
    # new_image = new_image[:, :, channel_index-1]

    # Create an alternate image that we can annotate on when needed
    annotated = new_image.copy()

    #
    # Do the math
    #
    #

    # Start off by getting the numbers that we set via the sliders
    (centerX, centerY, width, height, spacing, search, refresh_rate) = \
        get_trackbar_vars_as_tuple('Center X', 'Center Y', 'Width', 'Height', 'Spacing', 'Search Space', 'Refresh Rate')

    # Put at circle at the center point
    center_point = contrain_point_in_image((centerX, centerY))
    inverse_color_at_center = inverse_color_at_point(center_point)
    cv2.circle(annotated, center_point, 5, inverse_color_at_center, 2)

    # Find the distance from the center to the edge
    center_x_offset_from_edge = int(width / 2)
    center_y_offset_from_edge = int(height / 2)

    # Find the top left point
    top_left_yx = (centerX - center_x_offset_from_edge, centerY - center_y_offset_from_edge)

    # Find the top left point for each of the upper rectangles
    rectangles = [
        Rectangle(top_left_yx[0], top_left_yx[1] - (height + spacing) * n, width, height)
        for n in range(num_rectangles)]

    for n in range(len(rectangles)):
        rectangle = rectangles[n]

        # Place bounding boxes on the annotated image
        rect_color = inverse_color_at_point(rectangle.top_left_xy)
        cv2.rectangle(
            annotated, rectangle.top_left_xy, rectangle.bottom_right_xy,
            inverse_color_at_point(rectangle.top_left_xy), 5)

        # make some reworded variables for the for loop bounds
        row_min = rectangle.top_y
        row_max = rectangle.bottom_y
        col_min = rectangle.left_x
        col_max = rectangle.right_x

        # If there is a channel in the image, and the search rectangle has an area greater than 0
        if new_image_single_channel is not None and (row_max - row_min) * (col_max - col_min) != 0:

            # Do the numerical analysis

            # num_points_searched = 0
            points_sum = 0
            points = list()
            for row_inc in range(row_min, row_max, search + 1):
                for col_inc in range(col_min, col_max, search + 1):
                    point_val = new_image_single_channel[row_inc][col_inc]
                    points.append(new_image_single_channel[row_inc][col_inc])
                    points_sum += point_val
            average = points_sum / len(points)

            stddev_sum = 0
            for point in points:
                stddev_sum = pow((point - average), 2)
            stddev = pow(stddev_sum / (len(points) - 1), 0.5)

            rect_text_start_point = (5, img_height - (30 * (n + 1)))
            text_color = inverse_color_at_point(rect_text_start_point)
            # Put the text on our image
            cv2.putText(annotated, "Rect %d: avg%.2f stdev%.2f pts%d" % (n, average, stddev, len(points)),
                        rect_text_start_point, cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 2)

    #
    # Do text annotation
    #
    #

    # Determine the start point for our text
    text_start_point = (5, img_height - 10)
    text_color = inverse_color_at_point(text_start_point)
    # Put the text on our image
    cv2.putText(annotated, desired_space_name, text_start_point, cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 2)

    # Actually show the image, and wait for a while
    cv2.imshow(window_name, annotated)
    cv2.waitKey(refresh_rate)
