import argparse
import cv2
from collections.abc import Iterable

window_name = 'Image'
window_name_gray = "Image (Gray)"
num_rectangles = 4

image = cv2.imread('virtualrings.png')
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
    color = new_image[point_order_of_xy[0]][point_order_of_xy[1]]
    inverse_color = ~color
    # Convert this inverse color to a tuple and then print it
    inverse_color_as_tuple = \
        [int(x) for x in inverse_color] if isinstance(inverse_color, Iterable) else int(inverse_color)
    print(inverse_color_as_tuple)
    return inverse_color_as_tuple


def contrain_point_in_image(pt):
    return constrain(pt[0], 0, shape[0]), constrain(pt[1], 0, shape[1])


class Rectangle:
    def __init__(self, top_left_x, top_left_y, rect_width, rect_height):
        self.top_left_xy = contrain_point_in_image((top_left_x, top_left_y))
        self.bottom_right_xy = contrain_point_in_image((top_left_x + rect_width, top_left_y + rect_height))

        self.left_x = self.top_left_xy[0]
        self.right_x = self.bottom_right_xy[0]
        self.top_y = self.top_left_xy[1]
        self.bottom_y = self.bottom_right_xy[1]


print(shape)
# cv2.imshow(window_name, image)
# cv2.imshow(window_name_gray, gray)
# cv2.waitKey(0)

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

# Create our window
cv2.namedWindow(window_name, cv2.WINDOW_KEEPRATIO)

# Create trackbars to determine color space and channels
cv2.createTrackbar('Space', window_name, 0, len(keys), nothing)
cv2.createTrackbar('Channel', window_name, 0, 1, nothing)
# Create trackbars for the center point
cv2.createTrackbar('Center X', window_name, 0, img_width, nothing)
cv2.createTrackbar('Center Y', window_name, 0, img_height, nothing)
# Create trackbar for the width, and then the ratio to determine height
cv2.createTrackbar('Width', window_name, 0, img_width, nothing)
cv2.createTrackbar('Height', window_name, 0, img_height, nothing)
# Create trackbar for the spacing
cv2.createTrackbar('Spacing', window_name, 0, int(img_height / 4), nothing)
# Create trackbar to determine averaging params
cv2.createTrackbar('Search Space', window_name, 5, 20, nothing)


while True:
    #
    # Get correct color space and channels
    #
    #

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
    # Split the image to one channel if index != 0, otherwise keep image the same
    channel_index = cv2.getTrackbarPos('Channel', window_name)
    if channel_index != 0:
        num_channels_in_modified_image = 1
        for index in range(0, num_channels_for_trackbar):
            if index != channel_index - 1:
                new_image[:, :, index] = 0
    else:
        num_channels_in_modified_image = shape[2]
    # new_image = new_image[:, :, channel_index-1]

    # Create an alternate image that we can annotate on when needed
    annotated = new_image.copy()

    #
    # Do the math
    #
    #

    # Start off by getting the numbers that we set via the sliders
    (centerX, centerY, width, height, spacing, search) = \
        get_trackbar_vars_as_tuple('Center X', 'Center Y', 'Width', 'Height', 'Spacing', 'Search Space')

    # Put at circle at the center point
    inverse_color_at_center = inverse_color_at_point((centerX, centerY))
    cv2.circle(image, (centerX, centerY), 5, inverse_color_at_center, 2)

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
        # make some reworded variables for the for loop bounds
        row_min = rectangle.top_y
        row_max = rectangle.bottom_y
        col_min = rectangle.left_x
        col_max = rectangle.right_x

        # If there is a channel in the image, and the search rectangle has an area greater than 0
        if num_channels_in_modified_image > 0 and (row_max - row_min) * (col_max - col_min) != 0:

            # Do the numerical analysis

            num_points_searched = 0
            points_sum = 0
            points = list()
            for row_inc in range(row_min, row_min + height, search+1):
                for col_inc in range(col_min, col_min + height, search+1):
                    point_val = new_image[row_inc][col_inc]
                    points.append(new_image[row_inc][col_inc])
                    points_sum += point_val
            average = points_sum / num_points_searched

            stddev_sum = 0
            for point in points:
                stddev_sum = pow((point - average), 2)
            stddev = pow(stddev_sum / (num_points_searched - 1), 0.5)

            # Place bounding boxes on the annotated image
            rect_color = inverse_color_at_point(rectangle.top_left_xy)
            cv2.rectangle(
                annotated, rectangle.top_left_xy, rectangle.bottom_right_xy,
                inverse_color_at_point(rectangle.top_left_xy), 5)

            rect_text_start_point = (5, img_height - 20 - (10 * n))
            text_color = inverse_color_at_point(rect_text_start_point)
            # Put the text on our image
            cv2.putText(annotated, "Rect %d: avg%.2f stdev%.2f pts%d" % (n, average, stddev, num_points_searched),
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
    cv2.waitKey(50)
