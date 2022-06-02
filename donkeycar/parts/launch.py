import time
from datetime import datetime

class AiLaunch():
    '''
    This part will apply a large thrust on initial activation. This is to help
    in racing to start fast and then the ai will take over quickly when it's
    up to speed.
    '''

    def __init__(self, launch_duration=1.0, launch_throttle=1.0, keep_enabled=False):
        self.active = False
        self.enabled = False
        self.timer_start = None
        self.timer_duration = launch_duration
        self.launch_throttle = launch_throttle
        self.prev_mode = None
        self.trigger_on_switch = keep_enabled
        
    def enable_ai_launch(self):
        self.enabled = True
        print('AiLauncher is enabled.')

    def run(self, mode, ai_throttle):
        new_throttle = ai_throttle

        if mode != self.prev_mode:
            self.prev_mode = mode
            if mode == "local" and self.trigger_on_switch:
                self.enabled = True

        if mode == "local" and self.enabled:
            if not self.active:
                self.active = True
                self.timer_start = time.time()
            else:
                duration = time.time() - self.timer_start
                if duration > self.timer_duration:
                    self.active = False
                    self.enabled = False
        else:
            self.active = False

        if self.active:
            print('AiLauncher is active!!!')
            new_throttle = self.launch_throttle

        return new_throttle


class AiCatapult():
    '''
    Comparing to AiLaunch this particular class also controls the angle.
    '''

    def __init__(self, launch_duration=1.0, launch_throttle=1.0, keep_enabled=False, lock_angle=False):
        self.lock_angle = lock_angle
        self.active = False
        self.enabled = False
        self.timer_start = None
        self.timer_duration = launch_duration
        self.launch_throttle = launch_throttle
        self.prev_mode = None
        self.trigger_on_switch = keep_enabled

    def enable_ai_launch(self):
        self.enabled = True
        print('AiLauncher is enabled', datetime.now().time())

    def run(self, mode, ai_throttle, ai_angle):
        new_throttle = ai_throttle
        new_angle = ai_angle

        if mode != self.prev_mode:
            self.prev_mode = mode
            if mode == "local" and self.trigger_on_switch:
                self.enabled = True
                print('AiLauncher is activated by mode and trigger', datetime.now().time())

        if mode == "local" and self.enabled:
            if not self.active:
                self.active = True
                self.timer_start = time.time()
                print('AiLauncher is activated now', datetime.now().time())
            else:
                duration = time.time() - self.timer_start
                if duration > self.timer_duration:
                    self.active = False
                    self.enabled = False
                    print('AiLauncher is deactivated by duration', datetime.now().time())
        else:
            if self.active:
                print('AiLauncher is deactivated by mode now', datetime.now().time())
            self.active = False

        if self.active:
            if self.lock_angle:
                new_angle = 0.0
            else:
                new_throttle = self.launch_throttle

        return new_throttle, new_angle
