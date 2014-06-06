import time

from position.bitify.python.sensors.mpu6050 import MPU6050
from position.bitify.python.sensors.hmc5883l import HMC5883L
from position.bitify.python.sensors.bmp085 import BMP085


class GY88(object):

    K = 0.98
    K1 = 1 - K

    def __init__(self, bus, gyro_address, compass_address, barometer_address, name, compass_calibration,
                 obj_x='x', obj_y='y', obj_z='z', reverse=False,
                 gyro_scale=MPU6050.FS_2000, accel_scale=MPU6050.AFS_16g):
        self.bus = bus
        self.gyro_address = gyro_address
        self.name = name
        self.gyro_scale = gyro_scale
        self.accel_scale = accel_scale

        self.accel_scaled_x = 0

        self.accel_gyro = MPU6050(bus, gyro_address, name + "-gyroscope", obj_x, obj_y, obj_z, reverse, gyro_scale, accel_scale)
        self.compass = HMC5883L(bus, compass_address, name + "-compass", rate=5,
                                x_offset=compass_calibration[0],
                                y_offset=compass_calibration[1],
                                z_offset=compass_calibration[2],
                                obj_x=obj_x, obj_y=obj_y, obj_z=obj_z, reverse=reverse)
        self.barometer = BMP085(bus, barometer_address, name + "-barometer")

        self.mesure_time = time.time()
        self.last_time = time.time()
        self.time_diff = 0

        self.pitch = 0
        self.roll = 0
        self.yaw = 0
        # Take a reading as a starting point
        self.read_all()

    def read_all(self):
        '''
        Return pitch and roll in radians and the scaled x, y & z values from the gyroscope and accelerometer
        '''

        self.mesure_time = time.time()
        self.time_diff = self.mesure_time - self.last_time
        self.last_time = self.mesure_time

        self.accel_gyro.read_raw_data()
        self.compass.read_raw_data()

        self.gyro_raw_x = self.accel_gyro.read_raw_gyro_x()
        self.gyro_raw_y = self.accel_gyro.read_raw_gyro_y()
        self.gyro_raw_z = self.accel_gyro.read_raw_gyro_z()

        self.accel_raw_x = self.accel_gyro.read_raw_accel_x()
        self.accel_raw_y = self.accel_gyro.read_raw_accel_y()
        self.accel_raw_z = self.accel_gyro.read_raw_accel_z()

        self.gyro_scaled_x = self.accel_gyro.read_scaled_gyro_x()
        self.gyro_scaled_y = self.accel_gyro.read_scaled_gyro_y()
        self.gyro_scaled_z = self.accel_gyro.read_scaled_gyro_z()

        self.last_accel_scaled_x = self.accel_scaled_x

        self.accel_scaled_x = self.accel_gyro.read_scaled_accel_x()
        self.accel_scaled_y = self.accel_gyro.read_scaled_accel_y()
        self.accel_scaled_z = self.accel_gyro.read_scaled_accel_z()

        self.temperature, self.pressure = self.barometer.calculate()

        self.pitch, self.roll, self.yaw = self.compute_pitch_roll_yaw()

        return self.mesure_time,\
               self.pitch, self.roll, self.yaw, \
               self.gyro_scaled_x, self.gyro_scaled_y, self.gyro_scaled_z, \
               self.accel_scaled_x, self.accel_scaled_y, self.accel_scaled_z, \
               self.temperature, self.pressure

    def comp_filter(self, current_x, current_y):
        '''
        Apply a complementary filter to the Gyroscope and Accelerometer data
        '''

        if abs(self.gyro_scaled_x) < 15:
            new_pitch = GY88.K * (self.pitch + self.gyro_scaled_x * self.time_diff) + (GY88.K1 * current_x)
        else:
            new_pitch = self.pitch

        if abs(self.gyro_scaled_y) < 15:
            if self.accel_scaled_z < 0 and (self.last_accel_scaled_x < 0 <= self.accel_scaled_x or self.last_accel_scaled_x >= 0 > self.accel_scaled_x):
                self.roll = -self.roll

            new_roll = GY88.K * (self.roll + self.gyro_scaled_y * self.time_diff) + (GY88.K1 * current_y)
        else:
            new_roll = self.roll

        return new_pitch, new_roll

    def compute_pitch_roll_yaw(self):
        '''
        Return pitch, roll and yaw in radians
        '''

        (self.pitch, self.roll) = self.comp_filter(self.accel_gyro.pitch, self.accel_gyro.roll)
        self.yaw = self.compass.read_compensated_bearing(self.pitch, self.roll)

        return self.pitch, self.roll, self.yaw

    def set_compass_offsets(self,x_offset, y_offset, z_offset):
        self.compass.set_offsets(x_offset, y_offset, z_offset)