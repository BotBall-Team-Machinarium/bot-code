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
BLACK_THRESHOLD = 3200

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

   centerity = line_sense(norm_l, norm_r, normalize=False)

   influence = max(min(centerity, 1), -1)
   l_control = round((1 + influence) * MOTOR_STRENGTH)
   r_control = round((1 - influence) * MOTOR_STRENGTH)

   print(norm_l, norm_r, centerity, influence, l_control, r_control)

   k.motor(LEFT_MOTOR, l_control)
   k.motor(RIGHT_MOTOR, r_control)

def shovel_ice():
   """
   Automates the process of shoveling ice poms.

   This function consists of four phases:

   1. Initial positions: The bot's arm and tool are positioned to prepare for
      shoveling.

   2. Sinking arm and tool into the ice poms: The arm and tool are lowered into
      the ice poms to scoop them up.

   3. Driving backwards and angling the tool out: The bot drives backwards to
      extract the scooped-up ice poms from the container, and the tool is angled
      out to release the ice poms.

   4. Lifting up the tool and leveling it: The tool is lifted up and leveled to
      complete the shoveling process.

   The bot must be positioned in front of the ice container at the start of this
   function.

   Parameters:
      None

   Returns:
      None
   """
   # It is assumed that this script starts when the bot is in front of the ice

   # Initial positions
   k.enable_servos()
   k.set_servo_position(ARM_SERVO, 1100)
   k.set_servo_position(TOOL_SERVO, 1500)

   time.sleep(0.5)

   # First phase: Sinking arm and tool into the ice poms  

   k.set_servo_position(ARM_SERVO, 700)
   k.set_servo_position(TOOL_SERVO, 1750)

   time.sleep(0.5)

   for i in range(10):

      k.set_servo_position(TOOL_SERVO, k.get_servo_position(TOOL_SERVO) - 50)

      k.set_servo_position(ARM_SERVO, k.get_servo_position(ARM_SERVO) - 30)

   time.sleep(0.5)
   
   # Second phase: Driveing backwards and angling the tool out

   k.motor(LEFT_MOTOR, -50)
   k.motor(RIGHT_MOTOR, -50)
   time.sleep(1.5)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   for i in range(10):

      k.set_servo_position(TOOL_SERVO, k.get_servo_position(TOOL_SERVO) - 80)

      # time.sleep(0.1)

      k.set_servo_position(ARM_SERVO, k.get_servo_position(ARM_SERVO) - 40)

      # time.sleep(0.1)
   
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
   
   time.sleep(0.5)
   
   # Third phase: Lifting up the tool with the ice poms
   for i in range(30):

      k.set_servo_position(TOOL_SERVO, k.get_servo_position(TOOL_SERVO) - 10)
      
      time.sleep(0.01)
   
   time.sleep(0.5)

   # Fourth phase: lifting the arm up and leveling the tool

   for i in range(20):

      k.set_servo_position(ARM_SERVO, k.get_servo_position(ARM_SERVO) + 50)
      
      # time.sleep(0.1)

      k.set_servo_position(TOOL_SERVO, k.get_servo_position(TOOL_SERVO) + 40)
      
      # time.sleep(0.1)

      time.sleep(0.05)

      k.motor(LEFT_MOTOR, 30)
      k.motor(RIGHT_MOTOR, 30)
      time.sleep(0.1)
      k.motor(LEFT_MOTOR, 0)
      k.motor(RIGHT_MOTOR, 0)

def wait_for_line():
   """
   Waits until the line is detected by the left or right line sensors.

   Parameters:
      None

   Returns:
      None
   """
   if normalize_brightness(k.analog(LEFT_SENSOR)) > 0 or normalize_brightness(k.analog(RIGHT_SENSOR)) > 0:
      while normalize_brightness(k.analog(LEFT_SENSOR)) > 0 or normalize_brightness(k.analog(RIGHT_SENSOR)) > 0:
         time.sleep(0.01)
   while normalize_brightness(k.analog(LEFT_SENSOR)) == 0 or normalize_brightness(k.analog(RIGHT_SENSOR)) == 0:
      time.sleep(0.01)

def start():
   """
   Runs the entire script, which consists of:

   1. Moving out of the starting position and to the ice poms.
   2. Shoveling ice poms.
   3. Driving to the first line and waiting for it.
   4. Driving to the second line and waiting for it.
   5. Driving to the ice poms and turning towards them.
   6. Hugging the wall to get straight.

   Parameters:
      None

   Returns:
      None
   """   
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
   time.sleep(1.35)
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
   time.sleep(2.8)
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

def drive_to_bottles():
   # Back off from ice poms
   k.motor(LEFT_MOTOR, -100)
   k.motor(RIGHT_MOTOR, -100)
   time.sleep(0.2)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Turn to main space
   k.motor(LEFT_MOTOR, 100)
   k.motor(RIGHT_MOTOR, -100)
   time.sleep(0.8)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Drive to middle line
   k.motor(LEFT_MOTOR, 100)
   k.motor(RIGHT_MOTOR, 100)
   wait_for_line()
   time.sleep(0.1)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # # Turn to face along middle line
   # k.motor(LEFT_MOTOR, -100)
   # k.motor(RIGHT_MOTOR, 100)
   # time.sleep(0.6)
   # k.motor(LEFT_MOTOR, 0)
   # k.motor(RIGHT_MOTOR, 0)

   # Follow middle line to center cross
   while True:
      line_follow()
      if normalize_brightness(k.analog(LEFT_SENSOR)) == 1 and normalize_brightness(k.analog(RIGHT_SENSOR)) == 1:
         break
   while normalize_brightness(k.analog(LEFT_SENSOR)) == 1 and normalize_brightness(k.analog(RIGHT_SENSOR)) == 1:
      time.sleep(0.01)
   while True:
      line_follow()
      if normalize_brightness(k.analog(LEFT_SENSOR)) == 1 and normalize_brightness(k.analog(RIGHT_SENSOR)) == 1:
         break

   # Backtrack to the bottles
   k.motor(LEFT_MOTOR, -100)
   k.motor(RIGHT_MOTOR, -100)
   time.sleep(1)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Face back to bottles
   k.motor(LEFT_MOTOR, 100)
   k.motor(RIGHT_MOTOR, -100)
   time.sleep(0.8)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Drive forwards to hug wall and get straight
   k.motor(LEFT_MOTOR, 100)
   k.motor(RIGHT_MOTOR, 100)
   time.sleep(1.5)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Drive backwards towards bottles
   k.motor(LEFT_MOTOR, -100)
   k.motor(RIGHT_MOTOR, -100)
   time.sleep(2)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

def main():
   start()
   shovel_ice()
   drive_to_bottles()

if __name__ == "__main__":
   main()