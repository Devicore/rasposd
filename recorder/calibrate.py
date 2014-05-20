import smbus
import ConfigParser

from position.bitify.python.utils.i2cutils import

from position.bitify.python.sensors.hmc5883l import HMC5883L
from position.bitify.python.utils.i2cutils import i2c_raspberry_pi_bus_number

compass_address = 0x1e


bus = smbus.SMBus(i2c_raspberry_pi_bus_number())
compass = HMC5883L(bus, compass_address,"compass", rate=5)

print "Now repeatedly rotate the hmc5883l around all three axes"
[x_offset, y_offset, z_offset] = compass.get_calibration()
print("X offset : " + x_offset)
print("Y offset : " + y_offset)
print("Z offset : " + z_offset)

config = ConfigParser.RawConfigParser()

config.add_section('calibration')
config.set('calibration', 'x_offset', x_offset)
config.set('calibration', 'y_offset', y_offset)
config.set('calibration', 'z_offset', z_offset)

# Writing our configuration file to 'example.cfg'
with open('calibration/last.cfg', 'wb') as configfile:
    config.write(configfile)

print("Data saved to config file")