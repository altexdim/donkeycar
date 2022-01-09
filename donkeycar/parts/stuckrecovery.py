import math
import time
from cmath import phase, rect
from datetime import datetime
import logging


class StuckRecovery:

    def __init__(self, recovery_duration=2.2, recovery_throttle=-0.5, recovery_angle=0.0, stuck_duration=0.5):
        self.recovery_angle = recovery_angle
        self.stuck_duration = stuck_duration
        self.timer_duration = recovery_duration
        self.recovery_throttle = recovery_throttle

        self.stuck_start = None
        self.timer_start = None
        ''' 1 = detecting stop, 2 = detecting stuck, 3 = recovering '''
        self.state = 1

        self.logger = logging.getLogger()

        self.directions = []
        self.last_time_directions_saved = time.time()

    @staticmethod
    def mean_angle(deg):
        if len(deg) == 0:
            return 0
        res = math.degrees(phase(sum(rect(1, math.radians(d)) for d in deg) / len(deg)))
        if res < 0:
            res += 360
        return res

    @staticmethod
    def diff_angle(deg_prev, deg_curr):
        diff = (deg_curr - deg_prev + 180) % 360 - 180
        if diff < -180:
            return diff + 360
        else:
            return diff

    def get_error_angle(self, deg_curr):
        return self.diff_angle(self.mean_angle(self.directions[-10:-1]), deg_curr)

    def get_direction_for_recovery(self, deg_curr):
        error_angle = self.get_error_angle(deg_curr)

        return 1 if error_angle >= 0 else -1

    def run(self, mode, input_throttle, input_angle, speed, input_brake, pos_x, pos_y, pos_z, car):
        # yaw - steering left <-> right
        # x - direction - right from the starting line
        # z - direcion - backward from starting line
        yaw = car[2]

        # check 4 times per second
        if (time.time() - self.last_time_directions_saved) >= 0.25:
            # only if moving forward, only when moving fast, only in stop detection state
            if input_throttle > 0 and speed > 10 and self.state == 1:
                # save the direction
                self.directions.append(yaw)
                self.last_time_directions_saved = time.time()
                if len(self.directions) > 20:
                    # keep only 20 last measurements (5 seconds)
                    self.directions.pop(0)

        if mode != "local":
            ''' the recovery mode should work only in auto pilot mode, otherwise skip stuck recovery completely '''
            return input_throttle, input_angle, input_brake

        if self.state == 1:
            ''' detecting stop '''
            is_stopped = self.detect_is_stop(speed)
            if is_stopped:
                self.start_detecting_stuck()
            return input_throttle, input_angle, input_brake

        if self.state == 2:
            ''' detecting stuck '''
            is_stopped = self.detect_is_stop(speed)
            if is_stopped:
                is_stuck = self.maintain_detecting_stuck()
                if is_stuck:
                    self.start_recovery()
                    return self.get_recovery_output(input_angle, yaw)
                else:
                    return input_throttle, input_angle, input_brake
            else:
                self.finish_detecting_stuck()
                return input_throttle, input_angle, input_brake

        if self.state == 3:
            ''' recovering '''
            is_recovering = self.maintain_recovery(yaw)
            if is_recovering:
                return self.get_recovery_output(input_angle, yaw)
            else:
                self.finish_recovery()
                return 0, 0, 1

    def get_recovery_output(self, input_angle, yaw):
        # Simple: constant steering
        #   return self.recovery_throttle, self.recovery_angle
        # A bit smarter: reverse input angle
        #   return self.recovery_throttle, -input_angle
        # More smarter: to detect correct orientation // TODO
        # return self.recovery_throttle, -input_angle, 0

        return self.recovery_throttle, self.get_direction_for_recovery(yaw), 0

    @staticmethod
    def detect_is_stop(speed):
        return speed < 0.5

    def maintain_recovery(self, yaw):
        duration = time.time() - self.timer_start
        duration_result = (duration <= self.timer_duration)

        if (not duration_result) and (abs(self.get_error_angle(yaw)) > 45):
            # add another 0.5 second to correct the direction
            self.timer_start = time.time() - self.timer_duration + 0.5
            return True

        return duration_result

    def start_recovery(self):
        self.state = 3
        self.logger.info(f'{datetime.now().time()}: Stuck Recovery is activated')
        self.timer_start = time.time()

    def finish_recovery(self):
        self.state = 1
        self.logger.info(f'{datetime.now().time()}: Stuck Recovery is deactivated by timer')

    def start_detecting_stuck(self):
        self.state = 2
        self.stuck_start = time.time()

    def maintain_detecting_stuck(self):
        duration = time.time() - self.stuck_start
        return duration > self.stuck_duration

    def finish_detecting_stuck(self):
        self.state = 1
