import sys
sys.path.append("/usr/lib")
import kipr as k
import threading
import subprocess
import time
import utils
import os

k.enable_servos()

def delta_time_move(port: int, position: int, interval: float) -> None:
    k.enable_servo(port)
    current_position = k.get_servo_position(port)
    steps = 1 if current_position < position else -1
    for i in range(current_position, position + steps, steps):
        k.set_servo_position(port, i)
        print(k.get_servo_position(port))
        time.sleep(interval)

def dead_end_test() -> None:
    start_pos = 900
    end_pos = 1000
    for i in range(5):
        delta_time_move(0, start_pos, 0.01)
        delta_time_move(0, end_pos, 0.01)

def move(left: bool, right: bool, velocity: float, move_time: float) -> None:
    print(f"Left: {left}, Right: {right}, Velocity: {velocity}, Time: {move_time}")
    if left:
        k.motor(3, velocity)
    if right:
        k.motor(2, -velocity)
    time.sleep(move_time)
    k.off(3)
    k.off(2)

def wind(up: bool, speed: float) -> None:
    calibration: float = 1.0
    if up:
        k.motor(1, speed)
    else:
        k.motor(1, -speed)

    time.sleep(8 * calibration)
    k.off(1)

def wind_test() -> None:
    for i in range(5):
        wind(True, 100)
        wind(False, 100)

def shake_it_baby() -> None:
    for i in range(4):
        k.set_servo_position(1, 950)  # Leveled Position when winded up
        time.sleep(0.1)
        k.set_servo_position(1, 1250)  # Leveled Position when winded up
        time.sleep(0.1)

def starting_sequence(motor_down_wind: float = 3) -> None:
    delta_time_move(1, 700, 0.0005)  # make magazine beautifully positioned
    k.motor(0, -10)
    time.sleep(3) # time winding down
    k.off(0)
    k.motor(1, 100)
    time.sleep(motor_down_wind - 1.5)  #* CRITICAL
    k.off(1)

def fill_cups_test() -> None:
    delta_time_move(1, 450, 0.001)  # default starting position
    time.sleep(3)  # time to refill drinlpods manually
    delta_time_move(1, 1250, 0.005)  # Fill cup slowly
    shake_it_baby()   # why not

def collect_drinkpods_test() -> None:
    delta_time_move(1, 1600, 0.001)  # 1600 (magazine on ground)
    move(True, True, 50, 3.25)
    # move(True, True, -100, 3)

def fill_cups() -> None:
    # prepare magazine level
    delta_time_move(1, 300, 0.001)
    # wind up
    k.motor(1, -100)
    time.sleep(MOTOR_WIND_LENGTH + 1.5)
    k.off(1)
    # level magazine
    delta_time_move(1, 250, 0.001)
    move(True, False, 100, 5.75)
    move(True, True, 100, 1.35)
    for i in range(6):
        time.sleep(0.05)
        delta_time_move(1, 725, 0.0001)
        time.sleep(0.05)
        delta_time_move(1, 875, 0.0001)

    # time.sleep(1) #! DEBUG
    # #! go back to standard checkpoint position
    # delta_time_move(1, 820, 0.001) #! DEBUG

def collect_drinkpods() -> None:
    # move forward
    move(True, True, 100, 0.3) #! ACTIVATE
    # magazine up
    delta_time_move(1, 925, 0.001)
    # wait for assistant
    print("wait for assistant ..")
    time.sleep(10)
    # rotate to the left
    move(False, True, 100, 3.3975) #! ACTIVATE
    # prepare magazine level
    calib = -200
    delta_time_move(1, 780 + calib, 0.0001)
    # close grabber
    delta_time_move(0, 1850, 0.001)
    # wind down
    k.motor(1, 100)
    time.sleep(MOTOR_WIND_LENGTH + 0.675)
    k.off(1)
    # start moving
    k.motor(3, 100)
    k.motor(2, -100)
    # level magazine
    for i in range(6):
        delta_time_move(1, 800 + calib, 0.0001)
        time.sleep(0.25)
        delta_time_move(1, 760 + calib, 0.0001)
        time.sleep(0.25)
    k.motor(3, -100)
    k.motor(2, 100)
    time.sleep(3)
    k.off(3)
    k.off(2)

def grab_cups(correct_cup) -> None:
    # if targeted cup is index 2 take 0 as secondary cup
    # if targeted cup is index 1 take 0 as secondary cup
    if correct_cup == 0 or correct_cup == 1 or correct_cup == 2:
        # turn sligthy to the left
        move(False, True, 50, 0.485)
        # move forward
        move(True, True, 100, 1.6275)
        time.sleep(0.2)
        # close grabber
        delta_time_move(0, 1560, 0.001)
        # back up
        move(True, True, -100, 1.9)
        # wind up to very high position
        k.motor(1, -100)
        time.sleep(MOTOR_WIND_LENGTH + 2)
        k.off(1)
        # level magazines
        delta_time_move(1, 550, 0.001)  # was 550 before
        # wait for assistant
        print("wait for assistant ..")
        time.sleep(9.5)
        # rotate to the right
        move(True, False, 100, 4.005)
        time.sleep(0.1)
        # move forward
        move(True, True, 100, 0.5)
        time.sleep(0.1)
        # wind down to place cups
        k.motor(1, 100)
        time.sleep(MOTOR_WIND_LENGTH - 0.25)
        k.off(1)
        # level magazine
        delta_time_move(1, 450, 0.001)
        time.sleep(0.1)
        # open grabbers
        delta_time_move(0, 700, 0.001)
        # wind up
        k.motor(1, -100)
        time.sleep(MOTOR_WIND_LENGTH - 2)
        k.off(1)
        # magazine up
        delta_time_move(1, 700, 0.001)
        # rotate to the left
        move(True, False, -100, 3.9)  #* 1st RUN: 4.0 before
        # level magazine
        delta_time_move(1, 570, 0.001)
        # wind down
        k.motor(1, 100)
        time.sleep(MOTOR_WIND_LENGTH - 1.3 + 0.2)
        k.off(1)
        # move forward
        move(True, True, 100, 2.2)
        # close grabber
        delta_time_move(0, 1560, 0.001)
        # back up
        move(True, True, -100, 2)
        # wind up
        k.motor(1, -100)
        time.sleep(MOTOR_WIND_LENGTH - 1)
        k.off(1)
        # rotate to the right
        move(True, False, 100, 3.95)
        time.sleep(0.1)
        # back up
        move(True, True, -100, 0.75)
        # wind down
        k.motor(1, 100)
        time.sleep(MOTOR_WIND_LENGTH - 1)
        k.off(1)
        # open grabbers
        delta_time_move(0, 700, 0.001)
        # wind up
        k.motor(1, -100)
        time.sleep(MOTOR_WIND_LENGTH - 1)
        k.off(1)
    
    # if targeted cup is index 0 take 2 as secondary cup

def detect_cup() -> int:
    try:
        frame, masks, contours = utils.detect_contours()
        correct_cup, sorted_contours = utils.find_cups(frame, masks, contours)
        print(correct_cup)
        print(sorted_contours)
    except Exception:
        return 2

    return correct_cup  # cup index (from left to right)

def off(wait_time: float = 0):
    time.sleep(wait_time)
    print(f"Turning off, {wait_time} s passed!")
    code = """
import sys
sys.path.append("/usr/lib")
import kipr as k
import time
time.sleep(0.01)
k.ao()
k.disable_servos()
    """
    subprocess.run(['python3', '-c', code])
    os._exit(0)

# Todo: Cable-Managment, Check for invalid parts
# Setup: Winding String must be 34cm long at start
MOTOR_WIND_LENGTH = 4.75 + 1.45  # 4.75 standard
if __name__ == "__main__":
    # delta_time_move(1, 1560, 0.001)  #! DEBUG
    print("Waiting for light-signal..")
    while k.digital(9) == 0:
        time.sleep(0.001)
    timer = threading.Thread(target=off, kwargs={"wait_time": 119})
    timer.start()
    k.enable_servos()
    k.set_servo_position(0, 1840)
    cup_index = detect_cup()
    starting_sequence(MOTOR_WIND_LENGTH)
    k.set_servo_position(0, 1000)
    time.sleep(3)
    grab_cups(cup_index)
    collect_drinkpods()
    fill_cups()
