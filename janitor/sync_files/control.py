#!/usr/bin/python3
import os, sys, time, threading, multiprocessing
sys.path.append("/usr/lib")
import kipr as k

# CONSTANTS
LEFT_SENSOR = 0
RIGHT_SENSOR = 1
START_LIGHT = 9
LEFT_MOTOR = 0
RIGHT_MOTOR = 1
# At 0 the arm is horizontal, at 1100 it is vertical, at 1700 it is touching the controller
ARM_SERVO = 0
# At 1550 the tool is horizontal, if the arm is vertical (tool is normal to arm at 1550)
TOOL_SERVO = 1
# At 450 the fork is horizontal, at 1500 it is vertical, at 1900 it touches the controller
FORK_SERVO = 2

# Brightness normalization thresholds
WHITE_THRESHOLD = 220
BLACK_THRESHOLD = 3000

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

def line_follow(left_sensor_index: int = LEFT_SENSOR, right_sensor_index: int = RIGHT_SENSOR, speed: int = 100):
   val_l = k.analog(left_sensor_index)
   val_r = k.analog(right_sensor_index)

   centerity = line_sense(val_l, val_r, normalize=True)

   influence = max(min(centerity, 1), -1)
   l_control = round((1 + influence) * speed)
   r_control = round((1 - influence) * speed)

   k.motor(LEFT_MOTOR, l_control)
   k.motor(RIGHT_MOTOR, r_control)

def shovel_ice():
   # It is assumed that this script starts when the bot is in front of the ice hugging the wall, with the fork horizontal behind the robot to avoid collisions

   # Initial positions
   k.set_servo_position(ARM_SERVO, 1100)
   k.set_servo_position(TOOL_SERVO, 1500)

   time.sleep(0.5)

   # First phase: Sinking arm and tool into the ice poms  

   k.set_servo_position(TOOL_SERVO, 1750)
   time.sleep(0.1)
   k.set_servo_position(ARM_SERVO, 700)

   time.sleep(0.5)

   for i in range(10):

      k.set_servo_position(TOOL_SERVO, 1750 - 50 * i)

      k.set_servo_position(ARM_SERVO, 700 - 25 * i)

      time.sleep(0.1)

   time.sleep(0.5)
   
   # Second phase: Driveing backwards and angling the tool out
   for i in range(10):
      k.set_servo_position(TOOL_SERVO, 1250 - 80 * i)
      k.set_servo_position(ARM_SERVO, 450 - 40 * i)
      time.sleep(0.1)
   
   time.sleep(0.2)
   
   k.motor(LEFT_MOTOR, -85)
   k.motor(RIGHT_MOTOR, -100)
   time.sleep(0.15)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)
   
   time.sleep(0.5)
   
   # Third phase: Lifting up the tool with the ice poms
   for i in range(30):

      k.set_servo_position(TOOL_SERVO, 450 - 15 * i)
      
      time.sleep(0.05)
   
   time.sleep(0.5)

   # Fourth phase: lifting the arm up and leveling the tool
   k.motor(LEFT_MOTOR, 85)
   k.motor(RIGHT_MOTOR, 100)
   for i in range(20):

      k.set_servo_position(ARM_SERVO, 0 + 50 * i)

      k.set_servo_position(TOOL_SERVO, 0 + 40 * i)
      
      time.sleep(0.1)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)
   
   # Finish: Get shovel into position for transport
   for i in range(10):
      k.set_servo_position(ARM_SERVO, 1000 + 60 * i)
      k.set_servo_position(TOOL_SERVO, 800 + 60 * i)

      time.sleep(0.1)

def wait_for_line():
   # Wait till no line if starts on line
   if normalize_brightness(k.analog(LEFT_SENSOR)) > 0 or normalize_brightness(k.analog(RIGHT_SENSOR)) > 0:
      while normalize_brightness(k.analog(LEFT_SENSOR)) > 0 or normalize_brightness(k.analog(RIGHT_SENSOR)) > 0:
         time.sleep(0.000000001)
   # Wait till no floor
   while normalize_brightness(k.analog(LEFT_SENSOR)) == 0 or normalize_brightness(k.analog(RIGHT_SENSOR)) == 0:
      time.sleep(0.000000001)

def wait_for_floor():
   # Wait till no floor if starts on floor
   if normalize_brightness(k.analog(LEFT_SENSOR)) == 0 or normalize_brightness(k.analog(RIGHT_SENSOR)) == 0:
      while normalize_brightness(k.analog(LEFT_SENSOR)) == 0 or normalize_brightness(k.analog(RIGHT_SENSOR)) == 0:
         time.sleep(0.000000001)
   # Wait till no line
   while normalize_brightness(k.analog(LEFT_SENSOR)) > 0 or normalize_brightness(k.analog(RIGHT_SENSOR)) > 0:
      time.sleep(0.000000001)

def start_to_ice(): 
   # It is assumed that this routine starts when the game starts

   # Initial positions
   k.set_servo_position(ARM_SERVO, 1800)
   k.set_servo_position(TOOL_SERVO, 2000)
   k.set_servo_position(FORK_SERVO, 1500)

   # Back off from wall
   k.motor(LEFT_MOTOR, -100)
   k.motor(RIGHT_MOTOR, -100)
   time.sleep(0.3)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Turn to middle
   k.motor(LEFT_MOTOR, 100)
   k.motor(RIGHT_MOTOR, -100)
   time.sleep(0.8)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Move to first line
   k.motor(LEFT_MOTOR, -90)
   k.motor(RIGHT_MOTOR, -100)
   wait_for_line()
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Turn around
   k.motor(LEFT_MOTOR, -100)
   k.motor(RIGHT_MOTOR, 100)
   time.sleep(1.37)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Move to second line
   k.motor(LEFT_MOTOR, 90)
   k.motor(RIGHT_MOTOR, 100)
   wait_for_line()
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Drive to ice poms
   k.motor(LEFT_MOTOR, 90)
   k.motor(RIGHT_MOTOR, 100)
   time.sleep(3.0)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Lower fork to avoid collisions
   k.set_servo_position(FORK_SERVO, 500)

   # Turn towards ice
   k.motor(LEFT_MOTOR, 100)
   k.motor(RIGHT_MOTOR, -100)
   time.sleep(0.75)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Hug wall to get straight
   k.motor(LEFT_MOTOR, 90)
   k.motor(RIGHT_MOTOR, 100)
   time.sleep(1)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

def ice_to_bottles():
   # Back off from ice poms
   k.motor(LEFT_MOTOR, -100)
   k.motor(RIGHT_MOTOR, -100)
   time.sleep(0.2)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Lift fork up again to avoid collisions
   k.set_servo_position(FORK_SERVO, 1200)

   # Turn to main space
   k.motor(LEFT_MOTOR, -100)
   k.motor(RIGHT_MOTOR, 100)
   time.sleep(0.7)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Drive to middle line
   k.motor(LEFT_MOTOR, -100)
   k.motor(RIGHT_MOTOR, -100)
   wait_for_line()
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)
   
   # Correct overshoot
   k.motor(LEFT_MOTOR, 100)
   k.motor(RIGHT_MOTOR, 100)
   time.sleep(0.2)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Turn to face along middle line
   k.motor(LEFT_MOTOR, 100)
   k.motor(RIGHT_MOTOR, -100)
   time.sleep(0.8)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

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
   
   # Gradually drive backwards
   for i in range(10):
      k.motor(LEFT_MOTOR, i * -10)
      k.motor(RIGHT_MOTOR, i * -10)
      time.sleep(0.05)

   # Backtrack to the bottles
   k.motor(LEFT_MOTOR, -100)
   k.motor(RIGHT_MOTOR, -100)
   time.sleep(0.85)
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

def grab_bottles():
   # It is assumed that this routine starts when the robot is in line with the bottles, hugging the wall infront of the bottles, with the fork up in a resting position

   # Get distance from the bottles
   k.motor(LEFT_MOTOR, 47)
   k.motor(RIGHT_MOTOR, 50)
   time.sleep(1.7)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)
   
   # Angle fork
   k.set_servo_position(FORK_SERVO, 545)

   time.sleep(0.5)

   # Move shovel out of the way
   k.set_servo_position(ARM_SERVO, 1100)
   k.set_servo_position(TOOL_SERVO, 1550)

   # Drive fork into bottles slowly
   k.motor(LEFT_MOTOR, -30)
   k.motor(RIGHT_MOTOR, -31)
   time.sleep(3)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Lift fork with bottles
   for i in range(10):
      k.set_servo_position(FORK_SERVO, 500 + i * 100)
      time.sleep(0.05)

def bottles_to_beverages():
   # It is assumed this script begins right after lifting the bottles up

   # Spin around to face beverage station with fork
   k.motor(RIGHT_MOTOR, 100)
   k.motor(LEFT_MOTOR, -100)
   time.sleep(1.2)
   k.motor(RIGHT_MOTOR, 0)
   k.motor(LEFT_MOTOR, 0)

   # Drive towards beverage station
   k.motor(LEFT_MOTOR, -85)
   k.motor(RIGHT_MOTOR, -100)
   time.sleep(1.35)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Turn to beverage station
   k.motor(RIGHT_MOTOR, 100)
   k.motor(LEFT_MOTOR, -100)
   time.sleep(0.3)
   k.motor(RIGHT_MOTOR, 0)
   k.motor(LEFT_MOTOR, 0)

   # Hug wall
   k.motor(LEFT_MOTOR, -85)
   k.motor(RIGHT_MOTOR, -100)
   time.sleep(0.7)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

def drop_bottles():
   # It is assumed that this routine starts with the robot hugging the beverage station, with the fork with the bottles vertical

   # Put down bottles
   for i in range(10):
      k.set_servo_position(FORK_SERVO, 1500 - i * 105)
      time.sleep(0.1)
   time.sleep(0.5)

   # Drive away from beverage station to middle line
   k.motor(LEFT_MOTOR, 45)
   k.motor(RIGHT_MOTOR, 50)
   time.sleep(2)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)
   
   # Put fork away
   k.set_servo_position(FORK_SERVO, 1500)

   # Lower shovel, to push bottles
   k.set_servo_position(ARM_SERVO, 880)
   k.set_servo_position(TOOL_SERVO, 1500)

   # Turn to face shovel to bottles
   k.motor(LEFT_MOTOR, 100)
   k.motor(RIGHT_MOTOR, -90)
   time.sleep(1.7)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Drive forwards to push bottles and hug wall
   k.motor(LEFT_MOTOR, 87)
   k.motor(RIGHT_MOTOR, 100)
   time.sleep(2.2)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Lift shovel again
   k.set_servo_position(ARM_SERVO, 1800)
   k.set_servo_position(TOOL_SERVO, 2000)

   # Back off
   k.motor(LEFT_MOTOR, -87)
   k.motor(RIGHT_MOTOR, -100)
   time.sleep(1)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

def beverages_to_cups():
   # TODO: Implement driving to cups (needs cooperation with bartender)
   ...

   # It is assumed that this script starts right after dropping the bottles, with the assistant hugging the beverage station wall

   # Distance from wall
   k.motor(LEFT_MOTOR, 100)
   k.motor(RIGHT_MOTOR, 100)
   time.sleep(0.5)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Turn towards place where cups will be (brought by the bartender)
   k.motor(LEFT_MOTOR, -100)
   k.motor(RIGHT_MOTOR, 100)
   time.sleep(0.4)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Drive to cups
   k.motor(LEFT_MOTOR, 100)
   k.motor(RIGHT_MOTOR, 100)
   time.sleep(4)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Turn to face the cups
   k.motor(LEFT_MOTOR, -100)
   k.motor(RIGHT_MOTOR, 100)
   time.sleep(0.25)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

def ice_cups():
   # Drop ice poms into cups
   ...

   # It is assumed that this script starts when the robot is hugging the beverage wall, with the cups in there next to each other

   # Drive backwards so shovel is ontop the cups
   k.motor(LEFT_MOTOR, -85)
   k.motor(RIGHT_MOTOR, -100)
   time.sleep(0.5)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Lower shovel to cups
   for i in range(10):
      k.set_servo_position(ARM_SERVO, 1650 - i * 58)
      time.sleep(0.1)

   # Shake to get ice poms out of the shovel
   for i in range(30):
      # k.set_servo_position(ARM_SERVO, k.get_servo_position(ARM_SERVO) + 75)
      k.motor(LEFT_MOTOR, 20)
      k.motor(RIGHT_MOTOR, -20)
      time.sleep(0.1)
      # k.set_servo_position(ARM_SERVO, k.get_servo_position(ARM_SERVO) - 75)
      k.motor(LEFT_MOTOR, -20)
      k.motor(RIGHT_MOTOR, 20)
      time.sleep(0.1)

def start_to_bottles():
   # It is assumed that this routine starts with the assistant at its start position 3 cm from the wall

   # Turn to middle
   k.motor(LEFT_MOTOR, 100)
   k.motor(RIGHT_MOTOR, -100)
   time.sleep(0.85)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Drive to center line
   k.motor(LEFT_MOTOR, -85)
   k.motor(RIGHT_MOTOR, -100)
   wait_for_line()
   wait_for_floor()
   wait_for_line()
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Equalize overshoot
   k.motor(LEFT_MOTOR, 100)
   k.motor(RIGHT_MOTOR, 100)
   time.sleep(0.3)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)
   
   # Turn to center
   k.motor(LEFT_MOTOR, -100)
   k.motor(RIGHT_MOTOR, 100)
   time.sleep(0.75)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)
   
   # Follow middle line to center cross
   while True:
      if normalize_brightness(k.analog(LEFT_SENSOR)) == 1 and normalize_brightness(k.analog(RIGHT_SENSOR)) == 1:
         k.motor(LEFT_MOTOR, 0)
         k.motor(RIGHT_MOTOR, 0)
         break
      else:
         line_follow(speed=80)
   while True:
      if normalize_brightness(k.analog(LEFT_SENSOR)) == 1 and normalize_brightness(k.analog(RIGHT_SENSOR)) == 1:
         k.motor(LEFT_MOTOR, 0)
         k.motor(RIGHT_MOTOR, 0)
         break
      else:
         line_follow(speed=80)

   # Equalize unstraightness
   k.motor(LEFT_MOTOR, 100)
   k.motor(RIGHT_MOTOR, -95)
   time.sleep(0.05)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Backtrack to the bottles
   k.motor(LEFT_MOTOR, -85)
   k.motor(RIGHT_MOTOR, -97)
   time.sleep(1.25)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Face fork to bottles
   k.motor(LEFT_MOTOR, 100)
   k.motor(RIGHT_MOTOR, -95)
   time.sleep(0.82)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Fork up
   k.set_servo_position(FORK_SERVO, 1200)

   # Hug wall to get straight
   k.motor(LEFT_MOTOR, -45)
   k.motor(RIGHT_MOTOR, -50)
   time.sleep(2)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

def beverages_to_ice():
   # Drive from middle line infront of beverages to wall infront of ice
   ...

   # It is assumed that this routine starts right after the robot dropped the bottles into the beverage station, with it now standing on the middle line normal to it

   # Return tools to resting position
   k.set_servo_position(ARM_SERVO, 1800)
   k.set_servo_position(TOOL_SERVO, 2000)
   k.set_servo_position(FORK_SERVO, 1600)

   # Turn to face along the middle line
   k.motor(LEFT_MOTOR, 100)
   k.motor(RIGHT_MOTOR, -100)
   time.sleep(0.9)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Follow middle line for some time
   follow_time = 0
   while follow_time < 0.87:
      line_follow()
      time.sleep(0.001)
      follow_time += 0.001
   
   # Turn to drive to drinks & ice
   k.motor(LEFT_MOTOR, 100)
   k.motor(RIGHT_MOTOR, -100)
   time.sleep(0.82)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Drive to drinks & ice
   k.motor(LEFT_MOTOR, 85)
   k.motor(RIGHT_MOTOR, 100)
   time.sleep(2.35)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Lower fork to avoid collisions
   k.set_servo_position(FORK_SERVO, 200)

   # Turn towards ice
   k.motor(LEFT_MOTOR, 100)
   k.motor(RIGHT_MOTOR, -100)
   time.sleep(0.77)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Hug wall to get straight
   k.motor(LEFT_MOTOR, 85)
   k.motor(RIGHT_MOTOR, 100)
   time.sleep(1.5)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

def ice_to_beverages():
   # Drive from ice to beverages with ice
   ...

   # It is assumed that this routine starts at the end of the ice shoveling, with the robot hugging the ice wall

   # Pull in shovel
   k.set_servo_position(ARM_SERVO, 1650)
   k.set_servo_position(TOOL_SERVO, 1450)
   
   # Back off from ice poms
   k.motor(LEFT_MOTOR, -85)
   k.motor(RIGHT_MOTOR, -100)
   time.sleep(0.2)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Turn to main space
   k.motor(LEFT_MOTOR, -100)
   k.motor(RIGHT_MOTOR, 95)
   time.sleep(0.8)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Lift fork up again to avoid collisions
   k.set_servo_position(FORK_SERVO, 1600)

   # Drive out a bit
   k.motor(LEFT_MOTOR, -85)
   k.motor(RIGHT_MOTOR, -100)
   time.sleep(0.3)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Turn around for better mobility
   k.motor(LEFT_MOTOR, 100)
   k.motor(RIGHT_MOTOR, -95)
   time.sleep(1.65)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Go back out of way
   k.motor(LEFT_MOTOR, -85)
   k.motor(RIGHT_MOTOR, -100)
   time.sleep(0.5)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Wait for bartender to put second cup into beverage station (fork is kept down for this)
   time.sleep(35)

   # Drive to middle line and a bit further
   k.motor(LEFT_MOTOR, 85)
   k.motor(RIGHT_MOTOR, 100)
   wait_for_line()
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)
   
   # Drive on line
   k.motor(LEFT_MOTOR, 85)
   k.motor(RIGHT_MOTOR, 100)
   time.sleep(0.3)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Turn to face along middle line
   k.motor(LEFT_MOTOR, -100)
   k.motor(RIGHT_MOTOR, 95)
   time.sleep(0.4)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Drive along middle line
   follow_time = 0
   while follow_time < 0.4:
      line_follow()
      time.sleep(0.001)
      follow_time += 0.001

   # Turn to beverage station
   k.motor(LEFT_MOTOR, 100)
   k.motor(RIGHT_MOTOR, -95)
   time.sleep(0.8)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Hug wall
   k.motor(LEFT_MOTOR, 85)
   k.motor(RIGHT_MOTOR, 100)
   time.sleep(2)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

def push_poms():
   # Back off from beverage station to make space for bartender, and push poms to condiment station
   ...

   # It is assumed that this routine starts right after the icing the cups, with the robot infront of the beverage station

   # Back off to middle line
   k.motor(LEFT_MOTOR, -85)
   k.motor(RIGHT_MOTOR, -100)
   wait_for_line()
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Correct overshoot
   k.motor(LEFT_MOTOR, 85)
   k.motor(RIGHT_MOTOR, 100)
   time.sleep(0.3)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Turn to face along middle line
   k.motor(LEFT_MOTOR, -100)
   k.motor(RIGHT_MOTOR, 100)
   time.sleep(0.7)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Put shovel down
   k.set_servo_position(ARM_SERVO, 800)
   k.set_servo_position(TOOL_SERVO, 1800)

   # Follow middle line over center cross
   follow_time = 0
   while follow_time < 1.5:
      line_follow()
      time.sleep(0.001)
      follow_time += 0.001
   # Drive along middle line to right cross
   while True:
      line_follow()
      if normalize_brightness(k.analog(LEFT_SENSOR)) == 1 and normalize_brightness(k.analog(RIGHT_SENSOR)) == 1:
         break
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Turn to face condiment station
   k.motor(LEFT_MOTOR, 100)
   k.motor(RIGHT_MOTOR, -100)
   time.sleep(0.3)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Push poms into condiment station
   k.motor(LEFT_MOTOR, 85)
   k.motor(RIGHT_MOTOR, 100)
   time.sleep(1)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

def off(wait_time: float = 0, double: bool = True):
   # This function stops all actions of the robot after wait_time, and is meant to be called to end the game

   time.sleep(wait_time)

   # Turn off motors
   k.ao()
   k.disable_servos()

   # Turn actors off a second time
   if double:

      print(f"Turning off, {wait_time} s passed!")

      multiprocessing.Process(target=off, kwargs={"wait_time": 0, "double": False}).start()

   os._exit(0)

def routine():
   # This is the function meant to be run during the game

   # Enable servos, signaling game start
   k.enable_servos()

   # Initial positions
   k.set_servo_position(ARM_SERVO, 1800)
   k.set_servo_position(TOOL_SERVO, 2000)
   k.set_servo_position(FORK_SERVO, 1500)

   # Wait for starting light
   print("Awaiting starting light...")
   while k.digital(START_LIGHT) == 0:
      time.sleep(0.00000001)
   print("Starting light received!")
   
   # Create and start timer for stopping the robot on time
   timer = threading.Thread(target=off, kwargs={"wait_time": 119})
   timer.start()

   # Execute game plan
   start_to_bottles()
   grab_bottles()
   bottles_to_beverages()
   drop_bottles()
   beverages_to_ice()
   shovel_ice()
   ice_to_beverages()
   ice_cups()
   push_poms()

def test():
   k.enable_servos()

   # Initial positions
   k.set_servo_position(ARM_SERVO, 1800)
   k.set_servo_position(TOOL_SERVO, 2000)
   k.set_servo_position(FORK_SERVO, 1500)

   time.sleep(3)

   # Functions/routines to test
   grab_bottles()
   # time.sleep(1)
   # drop_bottles()

def main():
   routine()

   # test()

if __name__ == "__main__":
   main()