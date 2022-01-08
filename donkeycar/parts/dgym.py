import os
import time
import gym
import gym_donkeycar


def is_exe(fpath):
    return os.path.isfile(fpath) and os.access(fpath, os.X_OK)


class DonkeyGymEnv(object):

    def __init__(self, sim_path, host="127.0.0.1", port=9091, headless=0, env_name="donkey-generated-track-v0", sync="asynchronous", conf={}, record_location=False, record_gyroaccel=False, record_velocity=False, record_lidar=False, delay=0):

        if sim_path != "remote":
            if not os.path.exists(sim_path):
                raise Exception(
                    "The path you provided for the sim does not exist.")

            if not is_exe(sim_path):
                raise Exception("The path you provided is not an executable.")

        conf["exe_path"] = sim_path
        conf["host"] = host
        conf["port"] = port
        conf['guid'] = 0
        self.env = gym.make(env_name, conf=conf)
        self.frame = self.env.reset()
        self.action = [0.0, 0.0, 0.0]
        self.running = True
        self.info = {'pos': (0., 0., 0.),
                     'speed': 0,
                     'cte': 0,
                     'gyro': (0., 0., 0.),
                     'accel': (0., 0., 0.),
                     'vel': (0., 0., 0.)}
        self.delay = float(delay)
        self.record_location = record_location
        self.record_gyroaccel = record_gyroaccel
        self.record_velocity = record_velocity
        self.record_lidar = record_lidar

    def update(self):
        while self.running:
            self.frame, _, _, self.info = self.env.step(self.action)

    def update_action(self):
        while self.running:
            self.env.step_action(self.action)

    def update_observe(self):
        while self.running:
            self.frame, _, _, self.info = self.env.step_observe()

    def run_threaded_control(self, steering, throttle, brake=None):
        if self.delay > 0.0:
            time.sleep(self.delay / 2 / 1000.0)

        if steering is None or throttle is None:
            steering = 0.0
            throttle = 0.0
        if brake is None:
            brake = 0.0
        self.action = [steering, throttle, brake]

    def run_threaded_camera(self):
        if self.delay > 0.0:
            time.sleep(self.delay / 2 / 1000.0)

        # Output Sim-car position information if configured
        outputs = [self.frame]
        if self.record_location:
            outputs += self.info['pos'][0], self.info['pos'][1], self.info['pos'][2], self.info['speed'], self.info[
                'cte']
        if self.record_gyroaccel:
            outputs += self.info['gyro'][0], self.info['gyro'][1], self.info['gyro'][2], self.info['accel'][0], \
                       self.info['accel'][1], self.info['accel'][2]
        if self.record_velocity:
            outputs += self.info['vel'][0], self.info['vel'][1], self.info['vel'][2]
        if self.record_lidar:
            outputs.append(self.info['lidar'])
        if len(outputs) == 1:
            return self.frame
        else:
            return outputs

    def run_threaded(self, steering, throttle, brake=None):
        if steering is None or throttle is None:
            steering = 0.0
            throttle = 0.0
        if brake is None:
            brake = 0.0
        if self.delay > 0.0:
            time.sleep(self.delay / 1000.0)
        self.action = [steering, throttle, brake]

        # Output Sim-car position information if configured
        outputs = [self.frame]
        if self.record_location:
            outputs += self.info['pos'][0],  self.info['pos'][1],  self.info['pos'][2],  self.info['speed'], self.info['cte']
        if self.record_gyroaccel:
            outputs += self.info['gyro'][0], self.info['gyro'][1], self.info['gyro'][2], self.info['accel'][0], self.info['accel'][1], self.info['accel'][2]
        if self.record_velocity:
            outputs += self.info['vel'][0],  self.info['vel'][1],  self.info['vel'][2]
        if self.record_lidar:
            outputs.append(self.info['lidar'])
        if len(outputs) == 1:
            return self.frame
        else:
            return outputs

    def shutdown(self):
        if self.running:
            self.running = False
            time.sleep(0.2)
            self.env.close()

class DonkeyGymEnvControl:

    donkey_gym_env: DonkeyGymEnv

    def __init__(self, donkey_gym_env):
        self.donkey_gym_env = donkey_gym_env

    def update(self):
        self.donkey_gym_env.update_action()

    def run_threaded(self, steering, throttle, brake=None):
        return self.donkey_gym_env.run_threaded_control(steering, throttle, brake)

    def shutdown(self):
        self.donkey_gym_env.shutdown()

class DonkeyGymEnvCamera:

    donkey_gym_env: DonkeyGymEnv

    def __init__(self, donkey_gym_env):
        self.donkey_gym_env = donkey_gym_env

    def update(self):
        self.donkey_gym_env.update_observe()

    def run_threaded(self):
        return self.donkey_gym_env.run_threaded_camera()

    def shutdown(self):
        self.donkey_gym_env.shutdown()
