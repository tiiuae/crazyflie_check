"""This module contains Crazyflie related functions."""
import sys
import time
import colorama

from cflib.utils import uri_helper
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncLogger import SyncLogger

from lat import latency

drone_data = {}
console_data = ""

LAT_PACKET_SIZE=24
LAT_COUNT=500

def vari(arr):
    """vari calculates the variability for the roll, pitch, and yaw."""
    max_roll=-sys.maxsize-1
    min_roll=sys.maxsize
    max_pitch=-sys.maxsize-1
    min_pitch=sys.maxsize
    max_yaw=-sys.maxsize-1
    min_yaw=sys.maxsize
    for entry in arr:
        roll = entry[0]
        pitch = entry[1]
        yaw = entry[2]
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


def print_bool(var):
    """print_bool prints the fail/OK message"""
    if var:
        print(colorama.Back.GREEN+colorama.Fore.BLACK+"OK", end='')
    else:
        print(colorama.Back.RED+"FAIL", end='')

def print_motor_callback(data):
    global console_data
    #print(data, end='')
    if "\n" in data:
        full = console_data + data
        console_data = ""
        if len(full) > 8 and "HEALTH" in full:
            print(full, end='')
    else:
        console_data = console_data + data


def simple_log(drone, scf, lg_stab, rot_test, motor_test):
    """simple_log gets the logging data from the drones."""
    cf = scf.cf
    cf.console.__init__(cf)
    cf.console.receivedChar.add_callback(print_motor_callback)
    print( drone+": "+colorama.Fore.GREEN + "Connected.")
    print(colorama.Fore.CYAN + "(Running battery stress test)")
    time.sleep(1)
    cf.param.set_value('health.startBatTest', int('1'))
    time.sleep(1)
    if rot_test:
        print(colorama.Fore.GREEN + "Press enter and move device", end='')
        input()
        time.sleep(0.8)


    with SyncLogger(scf, lg_stab) as logger:
        i = 0
        bat = 0.0
        bat_stat = 0
        mem_err = -1
        entries = [ ]
        for log_entry in logger:
            #timestamp = log_entry[0]
            data = log_entry[1]
            #logconf_name = log_entry[2]
            drone_data[drone] = data
            bat = data['pm.vbat']
            bat_stat = data['pm.state']
            mem_err = data['memTst.errCntW']

            #print('%s: [%d][%s]: %s' % (drone, timestamp, logconf_name, data))
            if rot_test:
                entries.append((data['stabilizer.roll'], data['stabilizer.pitch'],
                    data['stabilizer.yaw']))

            i=i+1
            if i > 150:
                break
        cf.param.set_value('ring.effect', '0')
        if mem_err > 0:
            print(colorama.Fore.RED + drone + ": Memory error count non-zero: ", mem_err)

        if motor_test and rot_test:
            print(colorama.Fore.MAGENTA + "Please place drone on the floor, to run propeller test")
            time.sleep(2.5)

        if motor_test:
            time.sleep(2.5)
            cf.param.set_value('health.startPropTest', int('1'))
            time.sleep(5)

        bcol = colorama.Fore.GREEN
        if bat < 3.8:
            bcol = colorama.Fore.RED
        print(drone +':'+bcol +' Bat: %s volts' % (round(bat,3)))
        if bat_stat == BatteryStates.LOW_POWER:
            print(colorama.Fore.RED + "Low Battery")
        if rot_test:
            varis = vari(entries)
            roll, pitch, yaw = (varis[0] > 20), (varis[1] > 20), (varis[2] > 5)
            print("Roll: ", end='')
            print_bool(roll)
            print(", Pitch: ", end='')
            print_bool(pitch)
            print(", Yaw: ", end='')
            print_bool(yaw)
            print("")
    cf.close_link()



class BatteryStates:
    """BatteryStates defines the enumeration for the battery status
    reported by the Crazyflie."""
    BATTERY, CHARGING, CHARGED, LOW_POWER = list(range(4))


def check_drone(drone_name, drone_uri, lat_test=False, rot_test=False, motor_test=False):
    """check_drone checks a specific drone."""
    lg_stab = LogConfig(name='Stabilizer', period_in_ms=10)
    if rot_test:
        lg_stab.add_variable('stabilizer.roll', 'float')
        lg_stab.add_variable('stabilizer.pitch', 'float')
        lg_stab.add_variable('stabilizer.yaw', 'float')
    lg_stab.add_variable('pm.vbat', 'float')
    lg_stab.add_variable('pm.state', 'int8_t')
    lg_stab.add_variable('memTst.errCntW', 'uint32_t')
    #lg_stab.add_variable('deck.bcActiveMarker', 'int8_t')
    uri = uri_helper.uri_from_env(default=drone_uri)
    print(uri)

    try:
        with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
            simple_log(drone_name, scf, lg_stab, rot_test, motor_test)

        if lat_test:
            lat_ms = latency(uri, LAT_PACKET_SIZE, LAT_COUNT)
            col=colorama.Fore.GREEN
            if lat_ms > 10:
                col=colorama.Fore.RED
            elif lat_ms > 8:
                col=colorama.Fore.YELLOW
            print("Latency: "+col+"%dms" % lat_ms)
    except Exception as ex:
        print(colorama.Fore.RED + drone_name+" failed: ", ex)
