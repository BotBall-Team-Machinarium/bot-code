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
# At 450 the fork is horizontal, at 1500 it is vertical, at 1900 it touches the controller
FORK_SERVO = 2

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

   centerity = line_sense(val_l, val_r, normalize=True)

   influence = max(min(centerity, 1), -1)
   l_control = round((1 + influence) * MOTOR_STRENGTH)
   r_control = round((1 - influence) * MOTOR_STRENGTH)

   k.motor(LEFT_MOTOR, l_control)
   k.motor(RIGHT_MOTOR, r_control)

def shovel_ice():
   # It is assumed that this script starts when the bot is in front of the ice, with the fork horizontal behind the robot to avoid collisions

   # Initial positions
   k.enable_servos()
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
      k.set_servo_position(ARM_SERVO, 400 - 40 * i)
      time.sleep(0.1)
   
   time.sleep(0.2)
   
   k.motor(LEFT_MOTOR, -100)
   k.motor(RIGHT_MOTOR, -100)
   time.sleep(0.15)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)
   
   time.sleep(0.5)
   
   # Third phase: Lifting up the tool with the ice poms
   for i in range(30):

      k.set_servo_position(TOOL_SERVO, 450 - 15 * i)
      
      time.sleep(0.01)
   
   time.sleep(0.5)

   # Fourth phase: lifting the arm up and leveling the tool
   k.motor(LEFT_MOTOR, 100)
   k.motor(RIGHT_MOTOR, 100)
   for i in range(20):

      k.set_servo_position(ARM_SERVO, 0 + 50 * i)
      
      # time.sleep(0.1)

      k.set_servo_position(TOOL_SERVO, 0 + 40 * i)
      
      # time.sleep(0.1)

      time.sleep(0.05)
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
   k.enable_servos()
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
   # It is assumed that this routine starts when the robot is in line with the bottles, hugging the opposing wall, with the fork up in a resting position

   # Get a bit of distance from the bottles
   k.motor(LEFT_MOTOR, 29)
   k.motor(RIGHT_MOTOR, 30)
   time.sleep(0.2)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)
   
   # Angle fork
   k.set_servo_position(FORK_SERVO, 480)

   # Move shovel out of the way
   k.set_servo_position(TOOL_SERVO, 1550)
   time.sleep(0.1)
   k.set_servo_position(ARM_SERVO, 1100)

   time.sleep(1)

   # Drive fork into bottles slowly
   k.motor(LEFT_MOTOR, -29)
   k.motor(RIGHT_MOTOR, -30)
   time.sleep(3)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Lift fork with bottles
   for i in range(10):
      k.set_servo_position(FORK_SERVO, 500 + i * 100)
      time.sleep(0.1)

def bottles_to_beverages():
   # It is assumed this script begins right after lifting the bottles up

   # Spin around to face beverage station with fork
   k.motor(RIGHT_MOTOR, 100)
   k.motor(LEFT_MOTOR, -100)
   time.sleep(1.2)
   k.motor(RIGHT_MOTOR, 0)
   k.motor(LEFT_MOTOR, 0)

   # Drive towards beverage station
   k.motor(LEFT_MOTOR, -100)
   k.motor(RIGHT_MOTOR, -100)
   time.sleep(1.3)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Turn to beverage station
   k.motor(RIGHT_MOTOR, 100)
   k.motor(LEFT_MOTOR, -100)
   time.sleep(0.3)
   k.motor(RIGHT_MOTOR, 0)
   k.motor(LEFT_MOTOR, 0)

   # Hug wall
   k.motor(LEFT_MOTOR, -100)
   k.motor(RIGHT_MOTOR, -100)
   time.sleep(1)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

def drop_bottles():
   # It is assumed that this routine starts with the robot hugging the beverage station, with the fork with the bottles vertical

   # Put down bottles
   for i in range(10):
      k.set_servo_position(FORK_SERVO, 1500 - i * 100)
      time.sleep(0.1)
   k.set_servo_position(FORK_SERVO, 480)
   time.sleep(0.5)

   # Drive away from beverage station to middle line
   k.motor(LEFT_MOTOR, 100)
   k.motor(RIGHT_MOTOR, 90)
   time.sleep(0.8)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)
   
   # Put fork away
   k.set_servo_position(FORK_SERVO, 1500)

   # Lower shovel, to push bottles
   k.set_servo_position(ARM_SERVO, 880)
   k.set_servo_position(TOOL_SERVO, 1600)

   # Turn to face shovel to bottles
   k.motor(LEFT_MOTOR, 100)
   k.motor(RIGHT_MOTOR, -90)
   time.sleep(1.5)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Drive forwards to push bottles and hug wall
   k.motor(LEFT_MOTOR, 100)
   k.motor(RIGHT_MOTOR, 90)
   time.sleep(2)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Back off
   k.motor(LEFT_MOTOR, -100)
   k.motor(RIGHT_MOTOR, -90)
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
   # It is assumed that this script starts when the cups are directly infront of the shovel, standing next to each other
   # It is also assumed that the arm and tool servos are still in the positions from the ice shoveling (1100 and 900)

   # Lowering shovel to the cups
   k.set_servo_position(TOOL_SERVO, 1450)

   # Shake to get ice poms out of the shovel
   for i in range(100):
      k.set_servo_position(ARM_SERVO, k.get_servo_position(ARM_SERVO) + 50)
      # k.motor(LEFT_MOTOR, -50)
      # k.motor(RIGHT_MOTOR, -50)
      time.sleep(0.1)
      k.set_servo_position(ARM_SERVO, k.get_servo_position(ARM_SERVO) - 50)
      # k.motor(LEFT_MOTOR, 50)
      # k.motor(RIGHT_MOTOR, 50)
      time.sleep(0.1)

def start_to_bottles():
   # It is assumed that this routine starts with the assistant at its start position 3 cm from the wall

   # Initial positions
   k.enable_servos()
   k.set_servo_position(ARM_SERVO, 1800)
   k.set_servo_position(TOOL_SERVO, 2000)
   k.set_servo_position(FORK_SERVO, 1500)

   # Turn to middle
   k.motor(LEFT_MOTOR, 100)
   k.motor(RIGHT_MOTOR, -100)
   time.sleep(0.85)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Drive to center line
   k.motor(LEFT_MOTOR, -90)
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
      line_follow()
      if normalize_brightness(k.analog(LEFT_SENSOR)) == 1 and normalize_brightness(k.analog(RIGHT_SENSOR)) == 1:
         break
   while normalize_brightness(k.analog(LEFT_SENSOR)) == 1 and normalize_brightness(k.analog(RIGHT_SENSOR)) == 1:
      time.sleep(0.00000001)
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
   time.sleep(0.95)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

   # Face fork to bottles
   k.motor(LEFT_MOTOR, 100)
   k.motor(RIGHT_MOTOR, -100)
   time.sleep(0.8)
   k.motor(LEFT_MOTOR, 0)
   k.motor(RIGHT_MOTOR, 0)

def beverages_to_ice():
   # Drive from middle line infront of beverages to wall infront of ice
   ...

def ice_to_beverages():
   # Drive from ice to beverages with ice
   ...

def main():
   k.enable_servos()
   # start_to_ice()
   # shovel_ice()
   # ice_to_bottles()
   # grab_bottles()
   # bottles_to_beverages()
   # drop_bottles()
   # beverages_to_cups()
   # ice_cups()

   # start_to_bottles()
   # grab_bottles()
   # bottles_to_beverages()
   drop_bottles()
   # beverages_to_ice()
   # shovel_ice()
   # ice_to_beverages()
   # ice_cups()

if __name__ == "__main__":
   main()