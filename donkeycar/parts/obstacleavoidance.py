import math
import time
from datetime import datetime
import logging
import numpy as np


class ObstacleAvoidance:

    def __init__(self):
        self.logger = logging.getLogger()
        self.logger.info(f'{datetime.now().time()}: ObstacleAvoidance initialised')

    def run(self, mode, input_throttle, input_angle, speed, lidar, input_brake):
        # TODO - we need to detect obstacles at least at the 31m distance to react in time
        # TODO - the problem with delay in sending commands in gym-donkeycar, it takes 5 frames to send a command from that part to the network

        if lidar[0] != -1:
            if input_throttle < 1:
                return input_throttle, input_angle, input_brake

            if speed < 1:
                return input_throttle, input_angle, input_brake

            self.logger.info(
                f'{datetime.now().time()}: S {speed:.2f} T {input_throttle:.2f} A {input_angle:.2f} L {lidar}')

            return -1, input_angle, 1

        return input_throttle, input_angle, input_brake

        if speed < 0.1:
            speed = 0

        # TODO: to find 2 closest points, to understand the wall, to compare velocity vector with the wall, to add PID controller to keep safe distance to wall
        min_k = -1
        min_v = 100
        for k, v in np.ndenumerate(lidar):
            if v < min_v:
                min_v = v
                min_k = k[0]

        if min_k == -1:
            return input_throttle, input_angle, input_brake


        # far_distance = 2.5
        # far_distance = 3.5
        far_distance = 4.5
        close_distance = 1.5

        if 0 < min_v < far_distance:
            if min_v < close_distance:
                alfa = 1
            else:
                alfa = (far_distance - min_v) / (far_distance - close_distance)

            delta = 1 - alfa
            angle = min_k * 20
            if angle <= 180:
                mult = -1
            else:
                mult = 1

            # new_angle = input_angle + mult * alfa * 2
            # new_angle = input_angle + mult * alfa
            new_angle = input_angle + mult * alfa * 0.5
            if new_angle < -1:
                new_angle = -1
            if new_angle > 1:
                new_angle = 1

            new_throttle = input_throttle * delta
            if new_throttle < 0.1:
                new_throttle = 0.1
            if new_throttle > 1:
                new_throttle = 1

            self.logger.info(f'{datetime.now().time()}: Obstacle detected: dir={angle:.2f} dist={min_v:.2f} sp={speed:.2f} in_t={input_throttle:.2f} in_a={input_angle:.2f} Alfa={alfa:.2f} new_t={new_throttle:.2f} new_a={new_angle:.2f}')

            # 1 - return input_throttle * delta, input_angle + mult * alfa, 1 * alfa * speed
            # 2 - return input_throttle * delta, input_angle + mult * alfa, 0
            # 3 - return input_throttle, input_angle + mult * alfa, 0
            # 4 - new_throttle, new_angle, 0
            return input_throttle, new_angle, 0

        if mode != "local":
            ''' the obstacle avoidance mode should work only in auto pilot mode, otherwise skip obstacle avoidance completely '''
            return input_throttle, input_angle, input_brake

        return input_throttle, input_angle, input_brake
