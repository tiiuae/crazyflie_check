import logging
import time
import sys

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.utils import uri_helper

from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncLogger import SyncLogger
import colorama

from lat import latency

colorama.init(autoreset=True)
def_uri = "radio://0/30/2M/E7E7E7E7"

drones = {
    "cf00": "00",
    "cf01": "01",
    "cf02": "02",
    "cf03": "03",
    "cf04": "04",
    "cf05": "05",
    "cf06": "06",
    "cf07": "07",
    "cf08": "08",
    #"cf09": "09",
    "cf10": "10",
    #"cf11": "11",
    "cf12": "E7",
}

drone_data = {}


logging.basicConfig(level=logging.ERROR)

lat_packet_size=24
lat_count=500

print("Latency settings: packet_size=%d count=%d\n"  % (lat_packet_size, lat_count))

def vari(a):
    max_roll=-sys.maxsize-1
    min_roll=sys.maxsize
    max_pitch=-sys.maxsize-1
    min_pitch=sys.maxsize
    max_yaw=-sys.maxsize-1
    min_yaw=sys.maxsize
    for x in a:
        #print("%d %d %d" % x)
        roll = x[0]
        pitch = x[1]
        yaw = x[2]
        if max_roll < roll:
            max_roll = roll
        elif min_roll > roll:
            min_roll = roll

        if max_pitch < pitch:
            max_pitch = pitch
        elif min_pitch > pitch:
            min_pitch = pitch
        
        if max_yaw < yaw:
            max_yaw = yaw
        elif min_yaw > yaw:
            min_yaw = yaw
    return (max_roll - min_roll, max_pitch - min_pitch, max_yaw - min_yaw)


def print_bool(a):
    if a:
        print(colorama.Back.GREEN+colorama.Fore.BLACK+"OK", end='')
    else:
        print(colorama.Back.RED+"FAIL", end='')

def simple_log(drone, scf, logconf):
    cf = scf.cf
    cf.param.set_value('sound.effect', int('10'))
    cf.param.set_value('ring.effect', '7')
    cf.param.set_value('ring.solidRed', str(255))
    cf.param.set_value('ring.solidGreen', str(0))
    cf.param.set_value('ring.solidBlue', str(0))
    print( drone+": "+colorama.Fore.GREEN + "Connected. Press enter and move device", end='')
    #input()
    print()
    time.sleep(0.8)
    cf.param.set_value('ring.solidRed', str(0))
    cf.param.set_value('ring.solidGreen', str(255))
    cf.param.set_value('ring.solidBlue', str(0))
    with SyncLogger(scf, lg_stab) as logger:
        i = 0
        bat = 0.0
        bat_stat = 0
        entries = [ ]
        for log_entry in logger:
            #timestamp = log_entry[0]
            data = log_entry[1]
            #logconf_name = log_entry[2]
            drone_data[drone] = data
            bat = data['pm.vbat']
            bat_stat = data['pm.state']

            #print('%s: [%d][%s]: %s' % (drone, timestamp, logconf_name, data))
            entries.append((data['stabilizer.roll'], data['stabilizer.pitch'], data['stabilizer.yaw']))
            #i=i+1
            #if i > 150:
            #    break
            break
        cf.param.set_value('ring.effect', '0')
        bcol = colorama.Fore.GREEN
        if bat < 3.8:
            bcol = colorama.Fore.RED
        print(drone +':'+bcol +' Bat: %s volts' % (round(bat,3)))
        if bat_stat == BatteryStates.LOW_POWER:
            print(colorama.Fore.RED + "Low Battery")
        varis = vari(entries)
        roll, pitch, yaw = (varis[0] > 20), (varis[1] > 20), (varis[2] > 5)
        print("Roll: ", end='')
        print_bool(roll)
        print(", Pitch: ", end='')
        print_bool(pitch)
        print(", Yaw: ", end='')
        print_bool(yaw)
        print("")



class BatteryStates:
    BATTERY, CHARGING, CHARGED, LOW_POWER = list(range(4))

if __name__ == '__main__':
    # Initialize the low-level drivers
    cflib.crtp.init_drivers()

    for x in drones:
        lg_stab = LogConfig(name='Stabilizer', period_in_ms=10)
        lg_stab.add_variable('stabilizer.roll', 'float')
        lg_stab.add_variable('stabilizer.pitch', 'float')
        lg_stab.add_variable('stabilizer.yaw', 'float')
        lg_stab.add_variable('pm.vbat', 'float')
        lg_stab.add_variable('pm.state', 'int8_t')
        uri = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E7'+drones[x])

        try:
            with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
                simple_log(x, scf, lg_stab)
            #lat_ms = latency(uri, lat_packet_size, lat_count)
            #col=colorama.Fore.GREEN
            #if lat_ms > 10:
            #    col=colorama.Fore.RED
            #elif lat_ms > 8:
            #    col=colorama.Fore.YELLOW
            #print("Latency: "+col+"%dms" % lat_ms)
            print("")
        except Exception as e:
            print(colorama.Fore.RED + x+" failed: ", e)

