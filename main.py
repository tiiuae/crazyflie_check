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

from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
import click

colorama.init(autoreset=True)
def_uri = "radio://0/"

drones = {
    "cf0": ["80/2M/E7E7E7E700", False],
    "cf1": ["80/2M/E7E7E7E701", False],
    "cf2": ["80/2M/E7E7E7E702", True],
    "cf3": ["80/2M/E7E7E7E703", False],
    "cf4": ["80/2M/E7E7E7E704", False],
    "cf5": ["80/2M/E7E7E7E705", True],
    "cf6": ["80/2M/E7E7E7E706", True],
    "cf7": ["80/2M/E7E7E7E707", True],
    "cf8": ["80/2M/E7E7E7E708", True],
    "cf9": ["80/2M/E7E7E7E709", False],
    "cf10": ["80/2M/E7E7E7E710", True],
    "cf11": ["80/2M/E7E7E7E711", False],
    "cf12": ["80/2M/E7E7E7E7E7", True],
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

def simple_log(drone, scf, lg_stab, rot_test, motor_test):
    cf = scf.cf
    print(drone, 'a')
    print( drone+": "+colorama.Fore.GREEN + "Connected. Press enter and move device", end='')
    if rot_test:
        print(colorama.Fore.GREEN + " Press enter and move device", end='')
        input()
        time.sleep(0.8)
    else:
        print()

    print(colorama.Fore.CYAN + "(Running battery stress test)")
    time.sleep(1)
    cf.param.set_value('health.startBatTest', int('1'))
    time.sleep(1)
    
    with SyncLogger(scf, lg_stab) as logger:
        i = 0
        bat = 0.0
        bat_stat = 0
        memErr = -1
        entries = [ ]
        for log_entry in logger:
            #timestamp = log_entry[0]
            data = log_entry[1]
            #logconf_name = log_entry[2]
            drone_data[drone] = data
            bat = data['pm.vbat']
            bat_stat = data['pm.state']
            memErr = data['memTst.errCntW']

            #print('%s: [%d][%s]: %s' % (drone, timestamp, logconf_name, data))
            if rot_test:
                entries.append((data['stabilizer.roll'], data['stabilizer.pitch'], data['stabilizer.yaw']))

            i=i+1
            if i > 150:
                break
        cf.param.set_value('ring.effect', '0')
        if memErr > 0:
            print(colorama.Fore.RED + drone + ": Memory error count non-zero: ", memErr)

        if motor_test:
            cf.param.set_value('health.startPropTest', int('1'))

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



class BatteryStates:
    BATTERY, CHARGING, CHARGED, LOW_POWER = list(range(4))


def check_drone(drone, lat_test=False, rot_test=False, motor_test=False):
    lg_stab = LogConfig(name='Stabilizer', period_in_ms=10)
    if rot_test:
        lg_stab.add_variable('stabilizer.roll', 'float')
        lg_stab.add_variable('stabilizer.pitch', 'float')
        lg_stab.add_variable('stabilizer.yaw', 'float')
    lg_stab.add_variable('pm.vbat', 'float')
    lg_stab.add_variable('pm.state', 'int8_t')
    lg_stab.add_variable('memTst.errCntW', 'uint32_t')
    #lg_stab.add_variable('deck.bcActiveMarker', 'int8_t')
    uri = uri_helper.uri_from_env(default=def_uri+drones[drone][0])
    print(uri)
    
    try:
        print(drone, 'start')
        with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
            simple_log(drone, scf, lg_stab, rot_test, motor_test)
        print(drone, 'end')

        if lat_test:
            lat_ms = latency(uri, lat_packet_size, lat_count)
            col=colorama.Fore.GREEN
            if lat_ms > 10:
                col=colorama.Fore.RED
            elif lat_ms > 8:
                col=colorama.Fore.YELLOW
            print("Latency: "+col+"%dms" % lat_ms)
    except Exception as e:
        print(colorama.Fore.RED + drone+" failed: ", e)

from prompt_toolkit.shortcuts import checkboxlist_dialog

def cmd_run():
    tests = checkboxlist_dialog(
        title="Tests to run",
        text="What tests should run?",
        values=[
            ("latency", "Latency test"),
            ("rot", "Rotation test"),
            ("motor", "Motor power test"),
        ]
    ).run()
    print(tests)
    for x in drones:
        if drones[x][1]:
            check_drone(x, 'latency' in tests, 'rot' in tests, 'motor' in tests)

def cmd_show():
    print(colorama.Fore.CYAN + "=== Available Drones ===")
    for x in drones:
        print(x + ":\t(radio://x/" + drones[x][0] +") - ", end='')
        if drones[x][1]:
            print(colorama.Back.GREEN + colorama.Fore.BLACK + "Enabled")
        else:
            print(colorama.Back.RED + "Disabled")

from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.validation import Validator, ValidationError


drone_names = []
for x in drones:
    drone_names.append(x)
drone_completer = WordCompleter(drone_names)

class DroneValidator(Validator):
    def validate(self, document):
        text = document.text
        lst = text.split(",")
        if len(lst) > 1:
            for x in lst:
                if x not in drones:
                    raise ValidationError(message='Drone ('+x+') doesn\'t exist')
        else:
            if text not in drones:
                raise ValidationError(message='Drone doesn\'t exist')

def cmd_enable():
    text = prompt('enable drone> ', completer=drone_completer, validator=DroneValidator())
    lst = text.split(",")
    if len(lst) == 1:
        drones[text][1] = True
    else:
        for x in lst:
            drones[x][1] = True

def cmd_disable():
    text = prompt('disable drone> ', completer=drone_completer, validator=DroneValidator())
    lst = text.split(",")
    if len(lst) == 1:
        drones[text][1] = False
    else:
        for x in lst:
            drones[x][1] = False

if __name__ == '__main__':
    # Initialize the low-level drivers
    cflib.crtp.init_drivers()

    switch={
        "run": cmd_run,
        "show": cmd_show,
        "status": cmd_show,
        "e": cmd_enable,
        "enable": cmd_enable,
        "d": cmd_disable,
        "disable": cmd_disable,
    }
    while 1:
        user_input = prompt('> ', history=FileHistory('hist.txt'))
        if user_input in switch:
            switch.get(user_input)()
        else:
            print("Unknown command")


    #for x in drones:
    #    check_drone(x, True, True)
    #    print("")

