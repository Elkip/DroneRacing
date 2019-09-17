import av
import cv2.cv2 as cv2
import numpy
import traceback
import tellopy
import threading
from CloudComp.controllers import *
import sys
import pygame
import pygame.locals

prev_flight_data = None
run_recv_thread = True
new_image = None
flight_data = None
log_data = None
buttons = None
speed = 100
throttle = 0.0
yaw = 0.0
pitch = 0.0
roll = 0.0


def handler(event, sender, data, **args):
    global prev_flight_data
    global flight_data
    global log_data
    drone = sender
    if event is drone.EVENT_FLIGHT_DATA:
        if prev_flight_data != str(data):
            print(data)
            prev_flight_data = str(data)
        flight_data = data
    elif event is drone.EVENT_LOG_DATA:
        log_data = data
    else:
        print('event="%s" data=%s' % (event.getname(), str(data)))


def handle_input_event(drone, e):
    global speed
    global throttle
    global yaw
    global pitch
    global roll
    if e.type == pygame.locals.JOYAXISMOTION:
        # ignore small input values (Deadzone)
        if -buttons.DEADZONE <= e.value <= buttons.DEADZONE:
            e.value = 0.0
        if e.axis == buttons.LEFT_Y:
            throttle = update(throttle, e.value * buttons.LEFT_Y_REVERSE)
            drone.set_throttle(throttle)
        if e.axis == buttons.LEFT_X:
            yaw = update(yaw, e.value * buttons.LEFT_X_REVERSE)
            drone.set_yaw(yaw)
        if e.axis == buttons.RIGHT_Y:
            pitch = update(pitch, e.value *
                           buttons.RIGHT_Y_REVERSE)
            drone.set_pitch(pitch)
        if e.axis == buttons.RIGHT_X:
            roll = update(roll, e.value * buttons.RIGHT_X_REVERSE)
            drone.set_roll(roll)
    elif e.type == pygame.locals.JOYHATMOTION:
        if e.value[0] < 0:
            print("Rotating left")
            drone.counter_clockwise(speed)
        if e.value[0] == 0:
            print("Stop")
            drone.clockwise(0)
        if e.value[0] > 0:
            print("Rotating Right")
            drone.clockwise(speed)
        if e.value[1] < 0:
            print("Descending")
            drone.down(speed)
        if e.value[1] == 0:
            print("Stop")
            drone.up(0)
        if e.value[1] > 0:
            print("Ascending")
            drone.up(speed)
    elif e.type == pygame.locals.JOYBUTTONDOWN:
        if e.button == buttons.LAND:
            print("Landing...")
            drone.land()
        elif e.button == buttons.UP:
            print("Ascending")
            drone.up(speed)
        elif e.button == buttons.DOWN:
            print("Descending")
            drone.down(speed)
        elif e.button == buttons.ROTATE_RIGHT:
            print("Rotating right")
            drone.clockwise(speed)
        elif e.button == buttons.ROTATE_LEFT:
            print("Rotating left")
            drone.counter_clockwise(speed)
        elif e.button == buttons.FORWARD:
            print("Moving forwards")
            drone.forward(speed)
        elif e.button == buttons.BACKWARD:
            print("Moving backwards")
            drone.backward(speed)
        elif e.button == buttons.RIGHT:
            print("Moving right")
            drone.right(speed)
        elif e.button == buttons.LEFT:
            print("Moving left")
            drone.left(speed)
        elif e.button == buttons.FRONT_FLIP:
            print("Attempting front flip")
            drone.flip_forward()
        elif e.button == buttons.BACK_FLIP:
            print("Attempting back flip")
            drone.flip_back()
    elif e.type == pygame.locals.JOYBUTTONUP:
        if e.button == buttons.TAKEOFF:
            if throttle != 0.0:
                print('###')
                print('### throttle != 0.0 (This may hinder the drone from taking off)')
                print('###')
            print("Taking off")
            drone.takeoff()
        elif e.button == buttons.UP:
            print("Stop moving up")
            drone.up(0)
        elif e.button == buttons.DOWN:
            print("Stop moving down")
            drone.down(0)
        elif e.button == buttons.ROTATE_RIGHT:
            print("Stop rotating right")
            drone.clockwise(0)
        elif e.button == buttons.ROTATE_LEFT:
            print("Stop rotating left")
            drone.counter_clockwise(0)
        elif e.button == buttons.FORWARD:
            print("Stop moving forwards")
            drone.forward(0)
        elif e.button == buttons.BACKWARD:
            print("Stop moving backwards")
            drone.backward(0)
        elif e.button == buttons.RIGHT:
            print("Stop moving right")
            drone.right(0)
        elif e.button == buttons.LEFT:
            print("Stop moving left")
            drone.left(0)


def update(old, new, max_delta=0.3):
    if abs(old - new) <= max_delta:
        res = new
    else:
        res = 0.0
    return res


def draw_text(image, text, row):
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    font_size = 24
    font_color = (255, 255, 255)
    bg_color = (0, 0, 0)
    d = 2
    height, width = image.shape[:2]
    left_mergin = 10
    if row < 0:
        pos = (left_mergin, height + font_size * row + 1)
    else:
        pos = (left_mergin, font_size * (row + 1))
    cv2.putText(image, text, pos, font, font_scale, bg_color, 6)
    cv2.putText(image, text, pos, font, font_scale, font_color, 1)


def recv_thread(drone):
    global run_recv_thread
    global new_image
    global flight_data
    global log_data

    print('start recv_thread()')
    try:
        container = av.open(drone.get_video_stream())
        # skip first 300 frames
        frame_skip = 300
        while True:
            for frame in container.decode(video=0):
                if 0 < frame_skip:
                    frame_skip = frame_skip - 1
                    continue
                start_time = time.time()
                image = cv2.cvtColor(numpy.array(frame.to_image()), cv2.COLOR_RGB2BGR)

                if flight_data:
                    draw_text(image, 'TelloPy: joystick_and_video ' + str(flight_data), 0)
                if log_data:
                    draw_text(image, 'MVO: ' + str(log_data.mvo), -3)
                    draw_text(image, ('IMU: ' + str(log_data.imu))[0:52], -2)
                    draw_text(image, '     ' + ('IMU: ' + str(log_data.imu))[52:], -1)
                new_image = image
                if frame.time_base < 1.0 / 60:
                    time_base = 1.0 / 60
                else:
                    time_base = frame.time_base
                frame_skip = int((time.time() - start_time) / time_base)
    except Exception as ex:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print(ex)


def main():
    global buttons
    global run_recv_thread
    global new_image
    pygame.init()
    pygame.joystick.init()
    current_image = None
    try:
        js = pygame.joystick.Joystick(0)
        js.init()
        js_name = js.get_name()
        print('Joystick name: ' + js_name)
        if js_name in ('Wireless Controller', 'Sony Computer Entertainment Wireless Controller', 'Sony Interactive Entertainment Wireless Controller'):
            buttons = JoystickPS4
        elif js_name in ('PLAYSTATION(R)3 Controller', 'Sony PLAYSTATION(R)3 Controller', 'Afterglow controller for PS3'):
            buttons = JoystickPS3
        elif js_name in ('Xbox One Wired Controller', 'Xbox One Wireless Controller', 'Microsoft X-Box One S pad', 'Microsoft X-Box One pad'):
            buttons = JoystickXONE
        elif js_name == 'mayflash limited MAYFLASH GameCube Controller Adapter':
            buttons = JoystickGC
    except pygame.error:
        pass

    if buttons is None:
        print('no supported joystick found')
        return

    drone = tellopy.Tello()
    drone.connect()
    drone.wait_for_connection(40.0)
    frame_skip = 300
    drone.subscribe(drone.EVENT_FLIGHT_DATA, handler)
    drone.subscribe(drone.EVENT_LOG_DATA, handler)
    threading.Thread(target=recv_thread, args=[drone]).start()
    try:
        # Begin video stream
        while True:
            # Skip first 300 frames
            time.sleep(0.01)
            start_time = time.time()
            # Handle Drone input
            for e in pygame.event.get():
                handle_input_event(drone, e)
            # Handle video
            if current_image is not new_image:
                cv2.imshow('Tello', new_image)
                current_image = new_image
                cv2.waitKey(1)

    except KeyboardInterrupt as key:
        print(key)
    except Exception as ex:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print(ex)
    finally:
        run_recv_thread = False
        cv2.destroyAllWindows()
        drone.quit()
        exit(1)


if __name__ == '__main__':
    main()
