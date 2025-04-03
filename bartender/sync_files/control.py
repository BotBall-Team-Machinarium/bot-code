import sys
sys.path.append("/usr/lib")
import kipr as k
import time
import threading
import utils

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
    k.motor(3, 0)
    k.motor(2, 0)

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
    delta_time_move(1, 850, 0.0005)  # make magazine beautifully positioned
    k.motor(0, -10)
    time.sleep(2.9)
    k.off(0)
    k.motor(1, 100)
    time.sleep(motor_down_wind)
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

def grab_cups(correct_cup) -> None:
    # if targeted cup is index 2 take 0 as secondary cup
    # if targeted cup is index 1 take 0 as secondary cup
    if correct_cup == 1 or correct_cup == 2:
        for i in range(5):
            move(True, True, 100, 1)
            move(False, False, 0, 0.2)
        move(True, True, 100, 3)
    # if targeted cup is index 0 take 2 as secondary cup
    pass

def detect_cup() -> int:
    try:
        frame, masks, contours = utils.detect_contours()
        correct_cup, sorted_contours = utils.find_cups(frame, masks, contours)
        print(correct_cup)
        print(sorted_contours)
    except Exception:
        return 2

    return correct_cup  # cup index (from left to right)

# Todo: Cable-Managment, Check for invalid parts
if __name__ == "__main__":
    # Setup: Winding String must be 34cm long at start
    delta_time_move(1, 1560, 0.001)
    while True:
        # print("Light Signal:", k.analog(2))
        # if k.analog(2) <= 100:  # light starting signal
            # time.sleep(1) #! DEBUG
            k.enable_servos()
            k.set_servo_position(0, 1840)
            cup_index = detect_cup()
            time.sleep(1) #! DEBUGs
            motor_wind_length = 4.75  # 4.75 standard
            starting_sequence(motor_wind_length)
            k.set_servo_position(0, 1000)
            time.sleep(2)
            grab_cups(cup_index)
            k.motor(1, -100)
            time.sleep(motor_wind_length)
            k.off(1)
            break
        # time.sleep(0.1)
