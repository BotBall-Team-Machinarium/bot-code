#!/usr/bin/python3

import os, sys, cv2, numpy as np
sys.path.append("/usr/lib")
# import kipr as k

# CONSTANTS

# Brightness normalization thresholds
WHITE_THRESHOLD = 220
BLACK_THRESHOLD = 3000

# Line following constants
MOTOR_STRENGTH = 100

# Cam constants
CAM_INDEX = 0
# Minimum contour area to avoid noise
MIN_AREA = 1000
# Colors to seach for in hsv
COLORS = {
	"pink": {
		"lower_hue": 150,
		"upper_hue": 180,
		"lower_saturation": 50,
		"upper_saturation": 220,
		"lower_value": 150,
		"upper_value": 255
	},
	"green": {
		"lower_hue": 40,
		"upper_hue": 80,
		"lower_saturation": 70,
		"upper_saturation": 255,
		"lower_value": 150,
		"upper_value": 255
	},
	"blue": {
		"lower_hue": 80,
		"upper_hue": 110,
		"lower_saturation": 70,
		"upper_saturation": 255,
		"lower_value": 100,
		"upper_value": 255
	}
}

def normalize_brightness(brightness: int) -> float:
	"""
	Normalize the brightness value to a range between 0.0 and 1.0.

	Parameters:
	  brightness (int): The raw brightness value to be normalized.

	Returns:
	  float: The normalized brightness value, where 0.0 represents the 
			minimum brightness (below WHITE_THRESHOLD) and 1.0 represents 
			the maximum brightness (above BLACK_THRESHOLD). Values in 
			between are scaled linearly.
	"""
	if brightness < WHITE_THRESHOLD:
		return 0.0
	elif brightness > BLACK_THRESHOLD:
		return 1.0
	else:
		return (brightness - WHITE_THRESHOLD) / (BLACK_THRESHOLD - WHITE_THRESHOLD)

def line_sense(brightness_left: float, brightness_right: float) -> float:
	"""
	Compute a measure of the "centerity" of the line by comparing the brightnesses
	of the left and right sensors.

	Parameters:
	  brightness_left (float): The brightness detected by the left sensor.
	  brightness_right (float): The brightness detected by the right sensor.

	Returns:
	  float: The measure of centerity, where negative values indicate the line
			is more to the left and positive values indicate the line is more
			to the right. The absolute value of the returned value indicates
			the strength of the signal.

			Signal visualization (y is signal value, x is line position relative to bot center):
					__
			__	 /  \\__
			  \\__/
	"""
	if brightness_left > brightness_right:
		centerity = -(brightness_left + brightness_right)
	elif brightness_left < brightness_right:
		centerity = brightness_left + brightness_right
	else:
		centerity = 0

	return centerity

def line_follow():
	"""
	Controls the robot's motors based on the line detected by the two line sensors.

	The brightnesses of the two line sensors are normalized and then used to compute a measure
	of the "centerity" of the line. This measure is then used to control the robot's motors such
	that the robot will move towards the line.

	Parameters:
	  None

	Returns:
	  None
	"""
	val_l = k.analog(0)
	val_r = k.analog(1)

	norm_l = normalize_brightness(val_l)
	norm_r = normalize_brightness(val_r)

	centerity = line_sense(norm_l, norm_r)

	influence = max(min(centerity, 1), -1)
	l_control = round((1 + influence) * MOTOR_STRENGTH)
	r_control = round((1 - influence) * MOTOR_STRENGTH)

	print(norm_l, norm_r, centerity, influence, l_control, r_control)

	k.motor(2, l_control)
	k.motor(3, r_control)

def show_hsv(event, x, y, flags, param):
	"""Displays HSV values when clicking on the frame."""
	if event == cv2.EVENT_LBUTTONDOWN:
		hsv_value = hsv[y, x]  # Get HSV value at clicked point
		print(f"HSV at ({x}, {y}): {hsv_value}")

def display_contours(frame: np.ndarray, color_contours: dict[str, list[np.ndarray]], color_masks: dict[str, np.ndarray]):
	"""
	Displays contours of each color found in the given frame.
	
	Parameters:
	  frame (np.ndarray): The frame to display contours in.
	  color_contours (dict[str, list[numpy.ndarray]]): A dictionary mapping color names to lists of contours of that color.
	  color_masks (dict[str, numpy.ndarray]): A dictionary mapping color names to the masks of that color.
	
	Returns:
	  None
	"""
	output = frame.copy()

	cv2.namedWindow("Detected Colors")
	cv2.setMouseCallback("Detected Colors", show_hsv)

	for color_name, contours in color_contours.items():
		if contours:
			# Calculate middle HSV color
			mid_hue = (COLORS[color_name]["lower_hue"] + COLORS[color_name]["upper_hue"]) // 2
			mid_saturation = (COLORS[color_name]["lower_saturation"] + COLORS[color_name]["upper_saturation"]) // 2
			mid_value = (COLORS[color_name]["lower_value"] + COLORS[color_name]["upper_value"]) // 2

			# Convert mid HSV to BGR for display
			mid_bgr = cv2.cvtColor(np.uint8([[[mid_hue, mid_saturation, mid_value]]]), cv2.COLOR_HSV2BGR)[0][0]
			mid_bgr = tuple(int(c) for c in mid_bgr)

			# Draw contours
			cv2.drawContours(output, contours, -1, mid_bgr, 2)

	cv2.imshow("Detected Colors", output)
	cv2.waitKey(0)
	cv2.destroyAllWindows()

def detect_contours():
	"""
	Starts the webcam, reads a frame, and detects contours of predefined colors in the frame.

	Returns:
	  tuple: A tuple containing the frame, a dictionary mapping color names to masks, and a dictionary mapping color names to lists of contours.
	"""
	# Start webcam
	cap = cv2.VideoCapture(CAM_INDEX)
	if not cap.isOpened():
		print("Error: Could not access the camera.")
		return

	ret, frame = cap.read()
	if not ret:
		print("Error: Could not read frame.")

	# Release webcam
	cap.release()

	# Flip frame, as cam is upside down
	frame = cv2.flip(frame, -1)
	global hsv
	hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

	# Store found contours for each color
	color_masks = {}
	color_contours = {}

	# Find contours for each color
	for color_name, values in COLORS.items():
		lower_bound = np.array([values["lower_hue"], values["lower_saturation"], values["lower_value"]])
		upper_bound = np.array([values["upper_hue"], values["upper_saturation"], values["upper_value"]])

		mask = cv2.inRange(hsv, lower_bound, upper_bound)
		kernel = np.ones((5, 5), np.uint8)
		mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
		mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

		contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
		contours = [cnt for cnt in contours if cv2.contourArea(cnt) > MIN_AREA]

		color_masks[color_name] = mask
		color_contours[color_name] = contours

	return frame, color_masks, color_contours

def find_cups(frame: np.ndarray, masks: dict[str, cv2.typing.MatLike], contours: dict[str, list[cv2.typing.MatLike]]) -> list:	
	"""
	Determines the index of the correct cup and sorts the detected contours.

	Analyzes the detected contours in the provided frame to identify the correct cup's index
	and sorts the contours by their x-position. The function excludes drinks by ignoring the 
	rightmost contours and only considers cups. The correct cup is identified based on its 
	color relative to the detected drink color.

	Parameters:
		frame (np.ndarray): The image frame in which the cups and drinks are detected.
		masks (dict[str, cv2.typing.MatLike]): Dictionary mapping color names to their corresponding masks.
		contours (dict[str, list[cv2.typing.MatLike]]): Dictionary mapping color names to a list of contours.

	Returns:
		list: A tuple containing the index of the correct cup and a list of sorted contours 
		represented as (color, bounding box).
	"""

	if not contours:  # Check if contours list is empty
		print("No contours found.")
		return None
	
	each_contour = []
	for color, cnt in contours.items():
		if type(cnt) == list:
			for c in cnt:
				each_contour.append((c, color, cv2.boundingRect(c)))
		else:
			each_contour.append((cnt, color, cv2.boundingRect(cnt)))

	# Sort valid contours by x-position (rightmost last)
	sorted_contours = sorted(each_contour, key=lambda cnt: cnt[2][0])
	
	# Find position of the correct cup
	drink_color = sorted_contours[-1][1]
	correct_cup = 0
	last_color = None
	for cnt, color, box in sorted_contours:
		# Only take cups, not drinks (exclude rightmost contours)
		if box[0] < (frame.shape[1] // 6) * 5:
			if color == drink_color:
				break
			# Do not count cups with multiple contours multiple times
			if color != last_color:
				correct_cup += 1
			last_color = color

	return correct_cup, [(color, box) for cnt, color, box in sorted_contours]

def main():
	frame, masks, contours = detect_contours()

	correct_cup, sorted_contours = find_cups(frame, masks, contours)

	print(correct_cup, sorted_contours)

if __name__ == "__main__":
	main()