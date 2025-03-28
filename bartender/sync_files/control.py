import sys
sys.path.append("/usr/lib")
import kipr as k
import time
import threading

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
        k.motor(0, velocity)
    if right:
        k.motor(1, -velocity)
    time.sleep(move_time)
    k.motor(0, 0)
    k.motor(1, 0)

def wind(up: bool, speed: float) -> None:
    calibration: float = 1.0
    if up:
        k.motor(2, speed)
    else:
        k.motor(2, -speed)

    time.sleep(8 * calibration)
    k.motor(2, 0)

print("I'm in.")
for i in range(5):
    wind(True, 100)
    wind(False, 100)

# delta_time_move(1, 1600, 0.001)  # 1600 (magazine on ground)
# delta_time_move(2, 1000, 0.01)  # 1000 (closed), 0 (max open ~85°)
# move(True, True, 100, 4)
# k.disable_servos()
