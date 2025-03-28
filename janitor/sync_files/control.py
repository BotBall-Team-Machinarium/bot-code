#!/usr/bin/python3
import os, sys, time
sys.path.append("/usr/lib")
import kipr as k

# CONSTANTS
LEFT_SENSOR = 0
RIGHT_SENSOR = 1
LEFT_MOTOR = 0
RIGHT_MOTOR = 1
# At 0 the arm is horizontal, at 1100 it is vertical, at 1700 it is touching the controller
ARM_SERVO = 0
# At 1550 the tool is horizontal, if the arm is vertical (tool is normal to arm at 1550)
TOOL_SERVO = 1

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

def line_sense(brightness_left: float, brightness_right: float, normalize: bool = True) -> float:
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
   if normalize:
      brightness_left = normalize_brightness(brightness_left)
      brightness_right = normalize_brightness(brightness_right)
   if brightness_left > brightness_right:
      centerity = -(brightness_left + brightness_right)
   elif brightness_left < brightness_right:
      centerity = brightness_left + brightness_right
   else:
      centerity = 0

   return centerity

def line_follow():
   val_l = k.analog(LEFT_SENSOR)
   val_r = k.analog(RIGHT_SENSOR)

   norm_l = normalize_brightness(val_l)
   norm_r = normalize_brightness(val_r)

   centerity = line_sense(norm_l, norm_r)

   influence = max(min(centerity, 1), -1)
   l_control = round((1 + influence) * MOTOR_STRENGTH)
   r_control = round((1 - influence) * MOTOR_STRENGTH)

   print(norm_l, norm_r, centerity, influence, l_control, r_control)

   k.motor(LEFT_MOTOR, l_control)
   k.motor(RIGHT_MOTOR, r_control)

def shovel_ice():
   # It is assumed that this script starts when the bot is in front of the ice

   # Initial positions
   k.enable_servos()
   k.set_servo_position(ARM_SERVO, 1100)
   k.set_servo_position(TOOL_SERVO, 1500)

   time.sleep(0.1)

   k.set_servo_position(ARM_SERVO, 500)
   k.set_servo_position(TOOL_SERVO, 1650)

   time.sleep(0.5)

   # First phase: Sinking arm and tool into the ice poms   
   for i in range(10):

      k.set_servo_position(TOOL_SERVO, k.get_servo_position(TOOL_SERVO) - 50)

      # time.sleep(0.1)

      k.set_servo_position(ARM_SERVO, k.get_servo_position(ARM_SERVO) - 20)

      # time.sleep(0.1)

   time.sleep(0.1)
   
   # Second phase: Driveing backwards and angling the tool out

   k.motor(LEFT_MOTOR, -30)
   k.motor(RIGHT_MOTOR, -30)
   time.sleep(2)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   for i in range(10):

      k.set_servo_position(TOOL_SERVO, k.get_servo_position(TOOL_SERVO) - 60)

      # time.sleep(0.1)

      k.set_servo_position(ARM_SERVO, k.get_servo_position(ARM_SERVO) - 30)

      time.sleep(0.01)
   
   k.motor(LEFT_MOTOR, 30)
   k.motor(RIGHT_MOTOR, 30)
   time.sleep(0.5)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   time.sleep(0.1)
   
   k.motor(LEFT_MOTOR, -30)
   k.motor(RIGHT_MOTOR, -30)
   time.sleep(0.3)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)
   
   time.sleep(0.1)
   
   # Third phase: Lifting up the tool with the ice poms
   for i in range(40):

      k.set_servo_position(TOOL_SERVO, k.get_servo_position(TOOL_SERVO) - 10)
      
      time.sleep(0.01)
   
   time.sleep(5)

   k.motor(LEFT_MOTOR, 50)
   k.motor(RIGHT_MOTOR, 50)

   # Fourth phase: lifting the arm up and leveling the tool

   for i in range(20):

      k.set_servo_position(ARM_SERVO, k.get_servo_position(ARM_SERVO) + 50)
      
      # time.sleep(0.1)

      k.set_servo_position(TOOL_SERVO, k.get_servo_position(TOOL_SERVO) + 40)
      
      # time.sleep(0.1)

      time.sleep(0.05)
   
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

def start():
   def wait_for_line():
      if normalize_brightness(k.analog(LEFT_SENSOR)) > 0 or normalize_brightness(k.analog(RIGHT_SENSOR)) > 0:
         while normalize_brightness(k.analog(LEFT_SENSOR)) > 0 or normalize_brightness(k.analog(RIGHT_SENSOR)) > 0:
            time.sleep(0.01)
      while normalize_brightness(k.analog(LEFT_SENSOR)) == 0 or normalize_brightness(k.analog(RIGHT_SENSOR)) == 0:
         time.sleep(0.01)
   
   # A function for getting the robot out of the starting position and to the ice poms
   k.enable_servos()
   k.set_servo_position(ARM_SERVO, 1100)
   k.set_servo_position(TOOL_SERVO, 1550)

   k.motor(LEFT_MOTOR, -100)
   k.motor(RIGHT_MOTOR, -100)
   time.sleep(0.3)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   k.motor(LEFT_MOTOR, 100)
   k.motor(RIGHT_MOTOR, -100)
   time.sleep(0.8)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Move to first line
   k.motor(LEFT_MOTOR, -96)
   k.motor(RIGHT_MOTOR, -100)
   wait_for_line()
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   k.motor(LEFT_MOTOR, -100)
   k.motor(RIGHT_MOTOR, 100)
   time.sleep(1.4)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Move to second line
   k.motor(LEFT_MOTOR, 100)
   k.motor(RIGHT_MOTOR, 100)
   wait_for_line()
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Drive to ice poms
   k.motor(LEFT_MOTOR, 100)
   k.motor(RIGHT_MOTOR, 100)
   time.sleep(3)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Turn towards ice
   k.motor(LEFT_MOTOR, 100)
   k.motor(RIGHT_MOTOR, -100)
   time.sleep(0.8)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Hug wall to get straight
   k.motor(LEFT_MOTOR, 75)
   k.motor(RIGHT_MOTOR, 100)
   time.sleep(1)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

def main():
   start()
   shovel_ice()

if __name__ == "__main__":
   main()