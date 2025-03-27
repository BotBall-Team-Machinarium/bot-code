#!/usr/bin/python3

import os, sys, cv2, numpy as np, matplotlib.pyplot as plt
from matplotlib.lines import Line2D
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

def color_distance_euclidean(color1: np.ndarray[tuple[int, ...], np.dtype[np.uint8]], color2: np.ndarray[tuple[int, ...], np.dtype[np.uint8]]) -> float:
	"""
	Calculate the Euclidean color difference between two RGB colors.

	Args:
		rgb1 (tuple): RGB values of the first color (R, G, B)
		rgb2 (tuple): RGB values of the second color (R, G, B)

	Returns:
		float: Euclidean color difference value in the range [0, 1]
	"""
	distance = np.linalg.norm(color1 - color2)

	# Scale the distance to the range [0, 1]
	max_distance = np.sqrt(255**2 + 255**2 + 255**2)
	return distance / max_distance

def color_distance_cie94(color1: tuple[int, int, int], color2: tuple[int, int, int]) -> float:
	"""
	Calculate the CIE94 color difference between two RGB colors.

	Args:
		rgb1 (tuple): RGB values of the first color (R, G, B)
		rgb2 (tuple): RGB values of the second color (R, G, B)

	Returns:
		float: CIE94 color difference value (ΔE) in the range [0, 1]
	"""
	def rgb_to_xyz(rgb):
		"""
		Convert RGB to CIE XYZ.

		Args:
			rgb (tuple): RGB values (R, G, B)

		Returns:
			tuple: CIE XYZ values (X, Y, Z)
		"""
		r, g, b = rgb
		x = 0.412453 * r + 0.357580 * g + 0.180423 * b
		y = 0.212671 * r + 0.715160 * g + 0.072169 * b
		z = 0.019334 * r + 0.119193 * g + 0.950227 * b
		return (x, y, z)
	
	# Convert RGB to CIE XYZ
	xyz1 = rgb_to_xyz(color1)
	xyz2 = rgb_to_xyz(color2)

	# Calculate CIE94 color difference
	delta_e = np.sqrt(
		((xyz1[0] - xyz2[0]) / (1 + 0.045 * xyz1[0]))**2 +
		((xyz1[1] - xyz2[1]) / (1 + 0.015 * xyz1[1]))**2 +
		((xyz1[2] - xyz2[2]) / (1 + 0.015 * xyz1[2]))**2
	)

	# Scale the difference to the range [0, 1]
	max_delta_e = np.sqrt((255/1.055)**2 + (255/1.055)**2 + (255/1.055)**2)
	return delta_e / max_delta_e

def find_colors(image: cv2.typing.MatLike, colors: list[list[int]], tolerance: int = 0, kernel_radius: int = 0) -> dict[int, np.ndarray[tuple[int, ...], np.dtype[np.uint8]]]:
	"""
	Find the pixels in the middle-most horizontal line of the image that are similar within tolerance to one of the predefined colors.

	Parameters:
		image (cv2.typing.MatLike): The image to process.
		colors (list[list[int]]): A list of predefined colors to detect, in BGR format.
		tolerance (int, optional): The maximum distance between a pixel's color and a predefined color for the pixel to be considered a match. Should be in range [0, 1], as color difference values are normalized. Defaults to 0.
		kernel_radius (int, optional): The size of the kernel to average over when computing the color of a pixel. Defaults to 0.

	Returns:
		dict[int, np.ndarray[tuple[int, ...], np.dtype[np.uint8]]]: A dictionary mapping x-coordinates of pixels to their corresponding colors.
	"""
	# Convert the image to RGB
	image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
	# Get the middle-most horizontal line
	height, width, _ = image.shape
	middle_line = image[height // 2, :, :]

	# Convert predefined colors to NumPy arrays for easy comparison
	color_arrays = [np.array(color).flatten() for color in colors]

	# Scan from right to left
	color_pixels: dict[int, np.ndarray[tuple[int,  ...], np.dtype[np.uint8]]] = {}

	# Iterate over the pixels in the middle line from right to left
	for x in range(width - 1, -1, -1):
		# Get the average color of the pixels in the kernel
		pixel_colors = []
		for kernel_x in range(x - kernel_radius, x + kernel_radius + 1):
			if 0 <= kernel_x < width:
				pixel_colors.append(middle_line[kernel_x])
		pixel_color = np.mean(pixel_colors, axis=0)

		# Find the smallest distance to one of the predefined colors, and assign the pixel to that color if it's within tolerance
		best_color: np.ndarray[tuple[int, ...], np.dtype[np.uint8]] | None = None
		best_distance = np.inf
		for color in color_arrays:
			# Color distance
			distance = color_distance_cie94(pixel_color, color)
			if distance <= tolerance and distance < best_distance:
				best_color = color
				best_distance = distance
		if best_color is not None:
			color_pixels[x] = best_color.copy()

	return color_pixels

def get_color_regions(pixel_colors: dict[int, np.ndarray[tuple[int, ...], np.dtype[np.uint8]]], region_reach: int = 1, min_region_size: int = 1) -> list[tuple[list[int], list[tuple[int, np.ndarray[tuple[int, ...], np.dtype[np.uint8]]]]]]:
	"""
	Identify and group continuous regions of pixels with the same color.

	Parameters:
		pixel_colors (dict[int, np.ndarray[tuple[int, ...], np.dtype[np.uint8]]]): A dictionary mapping x-coordinates of pixels to their corresponding colors.
		region_reach (int, optional): The maximum distance between adjacent pixels to be considered part of the same region. Defaults to 1.
		min_region_size (int, optional): The minimum number of continuous pixels required for a region to be considered valid. Defaults to 1.

	Returns:
		list[tuple[list[int], list[tuple[int, np.ndarray[tuple[int, ...], np.dtype[np.uint8]]]]]]: A list of tuples where each tuple contains a list of color components and a list of x-coordinates representing continuous regions of pixels with the same color.
	"""
	# List of all found regions - format: [(color, [x, ...]), ...]
	color_regions: list[tuple[list[int], list[int]]] = []
	# Currently processed region - format: (color, [x, ...])
	current_region: tuple[list[int], list[int]] | None = None
	for x in sorted(pixel_colors.keys()):
		if current_region is None:
			# If the current region is None, set the current region to the current pixel
			current_region = (pixel_colors[x], [x])
		elif np.array_equal(pixel_colors[x], current_region[0]) and abs(x - current_region[1][-1]) <= region_reach:
			# If the current pixel is the same as the last pixel in the current region, add the pixel to the current region
			current_region[1].append(x)
		else:
			# If the current pixel is different from the last pixel in the current region, add the current region to the list of color regions under the key of the first pixel's color (if the region is long enough)
			if len(current_region[1]) >= min_region_size:
				color_regions.append(current_region)
			current_region = (pixel_colors[x], [x])
	# Add the last region if it fits the criteria
	if current_region is not None:
		if len(current_region[1]) >= min_region_size:
			color_regions.append(current_region)

	return color_regions

def init_cam():
	"""
	Initialize the camera and return a VideoCapture object.

	Returns:
		cv2.VideoCapture: A VideoCapture object representing the camera, or None if the camera could not be opened.
	"""
	cap = cv2.VideoCapture(CAM_INDEX)
	if not cap.isOpened():
		print("Error: Could not open webcam.")
		return None
	return cap

def get_frame(cap):
	"""
	Retrieve a frame from the given VideoCapture object.

	Parameters:
		cap (cv2.VideoCapture): The VideoCapture object to retrieve a frame from.

	Returns:
		cv2.Mat or None: The retrieved frame, or None if the frame could not be read.
	"""
	ret, frame = cap.read()
	if not ret:
		print("Error: Could not read frame.")
		return None
	return frame

def deinit_cam(cap):
	"""
	Deinitialize the camera.

	Parameters:
		cap (cv2.VideoCapture): The VideoCapture object to deinitialize.
	"""
	cap.release()

def cup_locator():
	# Capture an image from the webcam
	cam = init_cam()
	frame = get_frame(cam)
	deinit_cam(cam)
	
	# Process the image
	found_colors = find_colors(frame, SEARCH_COLORS, tolerance=SEARCH_TOLERANCE, kernel_radius=10)

	for x in found_colors:
		print(f"Found color {found_colors[x]} at x={x}")

	color_regions = get_color_regions(found_colors, region_reach=10, min_region_size=10)

	for color, region in color_regions:
		print(f"Found region {color} of length {len(region)} from x={region[0]} to x={region[-1]}")

	# Show the captured frame using Matplotlib
	fig, ax = plt.subplots()

	# Convert the frame to RGB, to display it in Matplotlib
	rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
	ax.imshow(rgb_frame)

	# Create a legend of the predefined ideal colors
	legend_elements = [Line2D([0], [0], marker='o', color='w', label=f'{x}', markerfacecolor=(x[0] / 255, x[1] / 255, x[2] / 255), markersize=10) for i, x in enumerate(SEARCH_COLORS)]
	ax.legend(handles=legend_elements, loc='upper right')

	# Display found colors (Colored dots)
	ax.scatter([x for x in found_colors], [frame.shape[0] // 2] * len(found_colors), c=[[y / 255 for y in found_colors[x]] for x in found_colors])
	
	# Display color regions (black lines connecting the dots)
	for region in color_regions:
		x = region[1]
		y = [frame.shape[0] // 2] * len(x)
		ax.plot(x, y, color=[0, 0, 0])
	
	# Show the plot
	plt.show()

def cup_locator_new():
	# Detect cup color contours using OpenCV integrated functionality

	# Start webcam
	cap = cv2.VideoCapture(0)

	ret, frame = cap.read()
	if not ret:
		print("Error: Could not read frame.")
		return
	
	# Release resources
	cap.release()

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
	cup_locator_new()

if __name__ == "__main__":
	main()