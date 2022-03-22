from GUI import GUI
from HAL import HAL
import cv2
import numpy as np

# Global values
last_diff_x = 0
print_debug = False
print_debug_2 = True
show_image = True


# Get the line in black and white with rgb image (Red color filter)
def get_line(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_thresh = np.array([0, 195, 200])
    upper_thresh = np.array([179, 255, 230])
    mask = cv2.inRange(hsv, lower_thresh, upper_thresh)
    mask = cv2.bitwise_not(mask)

    return mask


# Print information for debug, like coords of the followed line
def debug(x_start, y_start, x_end, y_end):
    print("X START : " + str(x_start))
    print("Y START : " + str(y_start))
    print("Y END : " + str(y_end))
    print("X END : " + str(x_end))


# Calculate the coords of the line to follow
def get_start_and_end_line(mask, image):
    img_invert = np.copy(mask)
    img_invert[mask > 0] = 0
    img_invert[mask == 0] = 1

    # ROW
    sum_row = img_invert.sum(axis=1)
    sum_row[sum_row <= 5] = 0

    # If all values == 1000 (Nothing found) -> Vehicle as to turn around
    if np.all(sum_row == sum_row[0]):
        if print_debug:
            debug(0, 0, 0, 0)
        if show_image:
            GUI.showImage(image)
        return 0, 0, 0, 0, True

    y_end = np.where(sum_row != 0)[0][0]
    y_start = mask.shape[0] - 1
    x_start = mask.shape[1] // 2

    y_end_specific_row = img_invert[y_end, :]
    y_end_specific_row_max = np.where(y_end_specific_row == np.amax(y_end_specific_row))
    # Taking all values from y_end and see where 1 are situated, and take the middle of them
    x_end = y_end_specific_row_max[0][len(y_end_specific_row_max[0]) // 2]

    # Drawing line to follow and start, end points
    if show_image:
        line_thickness = 4
        dot_thickness = 4
        cv2.line(image, (x_start, y_start), (x_end, y_end), (140, 255, 0), thickness=line_thickness)
        cv2.circle(image, (x_start, y_start), radius=3, color=(255, 50, 0), thickness=dot_thickness)
        cv2.circle(image, (x_end, y_end), radius=3, color=(255, 50, 0), thickness=dot_thickness)
        GUI.showImage(image)

    if print_debug:
        debug(x_start, y_start, x_end, y_end)

    return x_start, y_start, x_end, y_end, False


while True:
    global last_diff_x

    Kp = .01
    Kd = .005

    image = HAL.getImage()
    mask = get_line(image)

    x_start, y_start, x_end, y_end, car_stuck = get_start_and_end_line(mask, image)

    # If car is stuck
    if car_stuck:
        last_diff_x = 0

        HAL.setV(0.2)
        HAL.setW(20)
    else:
        diff_x = x_start - x_end
        if diff_x < 0:
            sign = -1
        else:
            sign = 1

        diff_x = abs(diff_x)

        # PD Controller
        W = Kp * diff_x + Kd * (diff_x - last_diff_x)

        HAL.setW(W * sign)

        if print_debug_2:
            print("Kd : " + "%.5f" % (Kd * (diff_x - last_diff_x)))
            print("Kp : " + "%.5f" % (Kp * diff_x))

        last_diff_x = diff_x

        V = 10 - (W * 7)
        if V < 1:
            V = 1

        HAL.setV(V)
