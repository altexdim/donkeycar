import math
import time
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

    def run(self, mode, input_throttle, input_angle, speed, input_brake):
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
                    return self.get_recovery_output(input_angle)
                else:
                    return input_throttle, input_angle, input_brake
            else:
                self.finish_detecting_stuck()
                return input_throttle, input_angle, input_brake

        if self.state == 3:
            ''' recovering '''
            is_recovering = self.maintain_recovery()
            if is_recovering:
                return self.get_recovery_output(input_angle)
            else:
                self.finish_recovery()
                return 0, 0, 1

    def get_recovery_output(self, input_angle):
        # Simple: constant steering
        #   return self.recovery_throttle, self.recovery_angle
        # A bit smarter: reverse input angle
        #   return self.recovery_throttle, -input_angle
        # More smarter: to detect correct orientation // TODO
        return self.recovery_throttle, -input_angle, 0

    @staticmethod
    def detect_is_stop(speed):
        return speed < 0.1

    def maintain_recovery(self):
        duration = time.time() - self.timer_start
        return duration <= self.timer_duration

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
