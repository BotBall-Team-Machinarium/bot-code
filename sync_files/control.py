#!/usr/bin/python3
import os, sys
sys.path.append("/usr/lib")
import kipr as k

# CONSTANTS

# Brightness normalization thresholds
WHITE_THRESHOLD = 220
BLACK_THRESHOLD = 3000

# Line following constants
MOTOR_STRENGTH = 100

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
            __    /  \__
              \__/
   """
   if brightness_left > brightness_right:
      centerity = -(brightness_left + brightness_right)
   elif brightness_left < brightness_right:
      centerity = brightness_left + brightness_right
   else:
      centerity = 0

   return centerity

def line_follow():
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

def main():
   while True: 
      # print(line_sense())
      line_follow()

if __name__ == "__main__":
   main()