import sys
sys.path.append("/usr/lib")
import kipr as k
import time

k.enable_servos()

def delta_time_move(port: int, position: int, interval: int) -> None:
    current_position = k.get_servo_position(port)
    steps = 1 if current_position < position else -1
    extension = 1 if current_position < position else -1
    for i in range(current_position, position + extension, steps):
        k.set_servo_position(port, i)
        print(k.get_servo_position(port))
        time.sleep(interval)

def dead_end_test() -> None:
    start_pos = 900
    end_pos = 1000
    for i in range(5):
        delta_time_move(0, start_pos, 0.01)
        delta_time_move(0, end_pos, 0.01)

k.motor(2, 100)
time.sleep(10)

# k.disable_servos()
