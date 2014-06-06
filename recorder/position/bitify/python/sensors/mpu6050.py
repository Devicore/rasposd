import math

import position.bitify.python.utils.i2cutils as I2CUtils


class MPU6050(object):
    '''
    Simple MPU-6050 implementation
    '''

    PWR_MGMT_1 = 0x6b

    FS_SEL = 0x1b
    FS_250 = 0
    FS_500 = 1
    FS_1000 = 2
    FS_2000 = 3

    AFS_SEL = 0x1c
    AFS_2g = 0
    AFS_4g = 1
    AFS_8g = 2
    AFS_16g = 3

    ACCEL_START_BLOCK = 0x3b
    ACCEL_XOUT_H = 0
    ACCEL_XOUT_L = 1
    ACCEL_YOUT_H = 2
    ACCEL_YOUT_L = 3
    ACCEL_ZOUT_H = 4
    ACCEL_ZOUT_L = 5

    # Specify accelerometer ADC sampling scale
    # You should specify the smallest scale you need to mesure. Higher the scale, less precise is the data
    ACCEL_SCALE = { AFS_2g  : [ 2, 16384.0], AFS_4g  : [ 4, 8192.0], AFS_8g  : [ 8, 4096.0], AFS_16g : [16, 2048.0] }

    TEMP_START_BLOCK = 0x41
    TEMP_OUT_H = 0
    TEMP_OUT_L = 1

    GYRO_START_BLOCK = 0x43
    GYRO_XOUT_H = 0
    GYRO_XOUT_L = 1
    GYRO_YOUT_H = 2
    GYRO_YOUT_L = 3
    GYRO_ZOUT_H = 4
    GYRO_ZOUT_L = 5

    # Specify gyroscope ADC sampling scale
    # You should specify the smallest scale you need to mesure. Higher the scale, less precise is the data
    GYRO_SCALE = { FS_250  : [ 250, 131.0], FS_500  : [ 500, 65.5], FS_1000 : [1000, 32.8], FS_2000 : [2000, 16.4] }

    K = 0.98
    K1 = 1 - K

    def __init__(self, bus, address, name,
                 obj_x='x', obj_y='y', obj_z='z', reverse=False,
                 fs_scale=FS_250, afs_scale=AFS_2g):
        '''
        Constructor
        '''

        self.bus = bus
        self.address = address
        self.name = name
        self.fs_scale = fs_scale
        self.afs_scale = afs_scale

        self.obj_x = obj_x
        self.obj_y = obj_y
        self.obj_z = obj_z

        if reverse:
            self.reverse = -1
        else:
            self.reverse = 1
        
        self.raw_gyro_data = [0, 0, 0, 0, 0, 0]
        self.raw_accel_data = [0, 0, 0, 0, 0, 0]
        self.raw_temp_data = [0, 0]
        
        self.gyro_raw_x = 0
        self.gyro_raw_y = 0
        self.gyro_raw_z = 0
        
        self.gyro_scaled_x = 0
        self.gyro_scaled_y = 0
        self.gyro_scaled_z = 0
        
        self.raw_temp = 0
        self.scaled_temp = 0
        
        self.accel_raw_x = 0
        self.accel_raw_y = 0
        self.accel_raw_z = 0
        
        self.accel_scaled_x = 0
        self.accel_scaled_y = 0
        self.accel_scaled_z = 0
        
        self.pitch = 0.0
        self.roll = 0.0

        try:
            self.hw_init()
        except IOError:
            try:
                print("Accelerometer/gyroscope hardware init failed, trying again")
                self.hw_init()
                print("Hardware init OK")
            except IOError:
                print("Hardware init failed twice, your power supply may be too weak. Please run again.")
                return


    def hw_init(self):
        # We need to wake up the module as it start in sleep mode
        I2CUtils.i2c_write_byte(self.bus, self.address, MPU6050.PWR_MGMT_1, 0)
        # Set the gryo resolution
        I2CUtils.i2c_write_byte(self.bus, self.address, MPU6050.FS_SEL, self.fs_scale << 3)
        # Set the accelerometer resolution
        I2CUtils.i2c_write_byte(self.bus, self.address, MPU6050.AFS_SEL, self.afs_scale << 3)


    def get_gyro_axis(self, axis):
        return {
            'x': I2CUtils.twos_compliment(self.raw_gyro_data[MPU6050.GYRO_XOUT_H], self.raw_gyro_data[MPU6050.GYRO_XOUT_L]),
            'y': I2CUtils.twos_compliment(self.raw_gyro_data[MPU6050.GYRO_YOUT_H], self.raw_gyro_data[MPU6050.GYRO_YOUT_L]),
            'z': I2CUtils.twos_compliment(self.raw_gyro_data[MPU6050.GYRO_ZOUT_H], self.raw_gyro_data[MPU6050.GYRO_ZOUT_L])
            }.get(axis, 0)

    def get_accel_axis(self, axis):
        return {
            'x': I2CUtils.twos_compliment(self.raw_accel_data[MPU6050.ACCEL_XOUT_H], self.raw_accel_data[MPU6050.ACCEL_XOUT_L]),
            'y': I2CUtils.twos_compliment(self.raw_accel_data[MPU6050.ACCEL_YOUT_H], self.raw_accel_data[MPU6050.ACCEL_YOUT_L]),
            'z': I2CUtils.twos_compliment(self.raw_accel_data[MPU6050.ACCEL_ZOUT_H], self.raw_accel_data[MPU6050.ACCEL_ZOUT_L])
            }.get(axis, 0)

    def read_raw_data(self):
        '''
        Read the raw data from the sensor, scale it appropriately and store for later use
        '''
        self.raw_gyro_data = I2CUtils.i2c_read_block(self.bus, self.address, MPU6050.GYRO_START_BLOCK, 6)
        self.raw_accel_data = I2CUtils.i2c_read_block(self.bus, self.address, MPU6050.ACCEL_START_BLOCK, 6)
        self.raw_temp_data = I2CUtils.i2c_read_block(self.bus, self.address, MPU6050.TEMP_START_BLOCK, 2)


        self.gyro_raw_x = self.get_gyro_axis(self.obj_x)*self.reverse
        self.gyro_raw_y = self.get_gyro_axis(self.obj_y)
        self.gyro_raw_z = self.get_gyro_axis(self.obj_z)*self.reverse
        
        self.accel_raw_x = self.get_accel_axis(self.obj_x)*self.reverse
        self.accel_raw_y = self.get_accel_axis(self.obj_y)
        self.accel_raw_z = self.get_accel_axis(self.obj_z)*self.reverse

        self.raw_temp = I2CUtils.twos_compliment(self.raw_temp_data[MPU6050.TEMP_OUT_H], self.raw_temp_data[MPU6050.TEMP_OUT_L])

        # We convert these to radians for consistency and so we can easily combine later in the filter
        self.gyro_scaled_x = math.radians(self.gyro_raw_x / MPU6050.GYRO_SCALE[self.fs_scale][1]) 
        self.gyro_scaled_y = math.radians(self.gyro_raw_y / MPU6050.GYRO_SCALE[self.fs_scale][1]) 
        self.gyro_scaled_z = math.radians(self.gyro_raw_z / MPU6050.GYRO_SCALE[self.fs_scale][1]) 

        self.scaled_temp = self.raw_temp / 340 + 36.53

        self.accel_scaled_x = self.accel_raw_x / MPU6050.ACCEL_SCALE[self.afs_scale][1]
        self.accel_scaled_y = self.accel_raw_y / MPU6050.ACCEL_SCALE[self.afs_scale][1]
        self.accel_scaled_z = self.accel_raw_z / MPU6050.ACCEL_SCALE[self.afs_scale][1]
        
        self.pitch = self.read_x_rotation(self.read_scaled_accel_x(),self.read_scaled_accel_y(),self.read_scaled_accel_z())
        self.roll =  self.read_y_rotation(self.read_scaled_accel_x(),self.read_scaled_accel_y(),self.read_scaled_accel_z())

        #print(str(self.pitch) + " - " + str(self.roll))
        
    def distance(self, x, y):
        '''Returns the distance between two point in 2d space'''
        return math.sqrt((x * x) + (y * y))
    
    def read_x_rotation(self, x, y, z):
        '''Returns the rotation around the X axis in radians'''
        return math.atan2(y, self.distance(x, z))
    
    def read_y_rotation(self, x, y, z):
        '''Returns the rotation around the Y axis in radians'''
        if z < 0:
            distance = -self.distance(y, z)
        else:
            distance = self.distance(y, z)

        return -math.atan2(x, distance)
    
    def read_raw_accel_x(self):
        '''Return the RAW X accelerometer value'''
        return self.accel_raw_x
        
    def read_raw_accel_y(self):
        '''Return the RAW Y accelerometer value'''
        return self.accel_raw_y
        
    def read_raw_accel_z(self):
        '''Return the RAW Z accelerometer value'''        
        return self.accel_raw_z
    
    def read_scaled_accel_x(self):
        '''Return the SCALED X accelerometer value'''
        return self.accel_scaled_x
    
    def read_scaled_accel_y(self):
        '''Return the SCALED Y accelerometer value'''
        return self.accel_scaled_y

    def read_scaled_accel_z(self):
        '''Return the SCALED Z accelerometer value'''
        return self.accel_scaled_z

    def read_raw_gyro_x(self):
        '''Return the RAW X gyro value'''
        return self.gyro_raw_x
        
    def read_raw_gyro_y(self):
        '''Return the RAW Y gyro value'''
        return self.gyro_raw_y
        
    def read_raw_gyro_z(self):
        '''Return the RAW Z gyro value'''
        return self.gyro_raw_z
    
    def read_scaled_gyro_x(self):
        '''Return the SCALED X gyro value in radians/second'''
        return self.gyro_scaled_x

    def read_scaled_gyro_y(self):
        '''Return the SCALED Y gyro value in radians/second'''
        return self.gyro_scaled_y

    def read_scaled_gyro_z(self):
        '''Return the SCALED Z gyro value in radians/second'''
        return self.gyro_scaled_z

    def read_temp(self):
        '''Return the temperature'''
        return self.scaled_temp
    
    def read_pitch(self):
        '''Return the current pitch value in radians'''
        return self.pitch

    def read_roll(self):
        '''Return the current roll value in radians'''
        self.roll
        
    def read_all(self):
        '''Return pitch and roll in radians and the scaled x, y & z values from the gyroscope and accelerometer'''
        self.read_raw_data()
        return self.pitch, self.roll, self.gyro_scaled_x, self.gyro_scaled_y, self.gyro_scaled_z, self.accel_scaled_x, \
               self.accel_scaled_y, self.accel_scaled_z
