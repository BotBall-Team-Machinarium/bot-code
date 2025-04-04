import sys
sys.path.append("/usr/lib")
import kipr as k
import time
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
    delta_time_move(1, 830, 0.0005)  # make magazine beautifully positioned
    k.motor(0, -10)
    time.sleep(2.9)
    k.off(0)
    k.motor(1, 100)
    time.sleep(motor_down_wind - 1)
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

def collect_drinkpods() -> None:
    # close grabber
    delta_time_move(0, 1850, 0.001)
    # wind up
    k.motor(1, 100)
    time.sleep(MOTOR_WIND_LENGTH -0.5)
    k.off(1)
    # start moving
    k.motor(3, 100)
    k.motor(2, -100)
    # level magazine
    for i in range(6):
        delta_time_move(1, 850, 0.0001)
        time.sleep(0.25)
        delta_time_move(1, 800, 0.0001)
        time.sleep(0.25)
    k.motor(3, -100)
    k.motor(2, 100)
    time.sleep(4)
    k.off(3)
    k.off(2)

def grab_cups(correct_cup) -> None:
    # if targeted cup is index 2 take 0 as secondary cup
    # if targeted cup is index 1 take 0 as secondary cup
    if correct_cup == 1 or correct_cup == 2:
        # turn sligthy to the left
        move(False, True, 50, 0.5)
        # move forward
        move(True, True, 100, 1.7)
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
        delta_time_move(1, 350, 0.001)
        # rotate to the right
        move(True, False, 100, 4)
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
        time.sleep(MOTOR_WIND_LENGTH - 1.5)
        k.off(1)
        # rotate to the left
        move(True, False, -100, 3.9)
        # wind down
        k.motor(1, 100)
        time.sleep(MOTOR_WIND_LENGTH - 0.8)
        k.off(1)
        # level magazine
        delta_time_move(1, 570, 0.001)
        # move forward
        move(True, True, 100, 1.75)
        # close grabber
        delta_time_move(0, 1560, 0.001)
        # back up
        move(True, True, -100, 2)
        # wind up
        k.motor(1, -100)
        time.sleep(MOTOR_WIND_LENGTH - 1)
        k.off(1)
        # rotate to the right
        move(True, False, 100, 3.9)
        time.sleep(0.1)
        # back up
        move(True, True, -100, 0.75)
        # wind down
        k.motor(1, 100)
        time.sleep(MOTOR_WIND_LENGTH - 1)
        k.off(1)
        # open grabbers
        delta_time_move(0, 700, 0.001)
        #! wind up DEBUG IG
        k.motor(1, -100)
        time.sleep(MOTOR_WIND_LENGTH - 1)
        k.off(1)
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
# Setup: Winding String must be 34cm long at start
MOTOR_WIND_LENGTH = 4.75  # 4.75 standard
if __name__ == "__main__":
    # delta_time_move(1, 1560, 0.001)
    # while True:
    #     # * print("Light Signal:", k.analog(2))
    #     # * if k.analog(2) <= 100:  # light starting signal
    #         k.enable_servos()
    #         k.set_servo_position(0, 1840)
    #         cup_index = detect_cup()
    #         time.sleep(1) #! DEBUGs
    #         starting_sequence(MOTOR_WIND_LENGTH)
    #         k.set_servo_position(0, 1000)
    #         time.sleep(2)
    #         grab_cups(cup_index)
    #         break
    #     #* time.sleep(0.1)
    collect_drinkpods()
