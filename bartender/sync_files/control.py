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
MIN_AREA = 500
# Colors to seach for in hsv
COLORS = {
	"pink": {
		"lower_hue": 150,
		"upper_hue": 180,
		"lower_saturation": 50,
		"upper_saturation": 170,
		"lower_value": 255,
		"upper_value": 255
	},
	"green": {
		"lower_hue": 40,
		"upper_hue": 80,
		"lower_saturation": 70,
		"upper_saturation": 255,
		"lower_value": 100,
		"upper_value": 255
	},
	"blue": {
		"lower_hue": 80,
		"upper_hue": 110,
		"lower_saturation": 140,
		"upper_saturation": 255,
		"lower_value": 125,
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

def cup_locator():
	# Detect cup color contours using OpenCV integrated functionality

	# Start webcam
	cap = cv2.VideoCapture(0)

	ret, frame = cap.read()
	if not ret:
		print("Error: Could not read frame.")
		return
	
	# Release resources
	cap.release()

	# Flip frame
	frame = cv2.flip(frame, -1)

	# Convert to HSV
	hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

	# Copy frame for drawing contours
	output = frame.copy()

	# Process each color separately
	for color_name, values in COLORS.items():
		# Define lower and upper HSV bounds
		lower_bound = np.array([values["lower_hue"], values["lower_saturation"], values["lower_value"]])
		upper_bound = np.array([values["upper_hue"], values["upper_saturation"], values["upper_value"]])

		# Create mask
		mask = cv2.inRange(hsv, lower_bound, upper_bound)

		# Morphological operations to reduce noise
		kernel = np.ones((5, 5), np.uint8)
		mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
		mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

		# Find contours
		contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

		# Filter small contours
		contours = [cnt for cnt in contours if cv2.contourArea(cnt) > MIN_AREA]

		# Calculate middle HSV color
		mid_hue = (values["lower_hue"] + values["upper_hue"]) // 2
		mid_saturation = (values["lower_saturation"] + values["upper_saturation"]) // 2
		mid_value = (values["lower_value"] + values["upper_value"]) // 2

		# Convert mid HSV to BGR for display
		mid_bgr = cv2.cvtColor(np.uint8([[[mid_hue, mid_saturation, mid_value]]]), cv2.COLOR_HSV2BGR)[0][0]
		mid_bgr = tuple(int(c) for c in mid_bgr)  # Convert to tuple

		# Draw filtered contours with the calculated color
		cv2.drawContours(output, contours, -1, mid_bgr, 2)

	# Show the final result with colored contours
	cv2.imshow("Detected Colors", output)

	# Wait for a key press to exit
	cv2.waitKey(0)

	cv2.destroyAllWindows()

def main():
	cup_locator()

if __name__ == "__main__":
	main()