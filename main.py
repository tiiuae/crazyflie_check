"""This module is a Crazyflie Checker"""
import logging
import sys

import cflib.crtp

import colorama

from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.shortcuts import checkboxlist_dialog
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.validation import Validator, ValidationError

from tomlkit import parse

from lib import check_drone

colorama.init(autoreset=True)

f = open('drones.toml', 'r', encoding='utf-8')
drones = parse(f.read())
f.close()

logging.basicConfig(level=logging.ERROR)


DEF_URI = "radio://0/"

#print("Latency settings: packet_size=%d count=%d\n"  % (LAT_PACKET_SIZE, LAT_COUNT))

def cmd_run():
    """cmd_run represents the run command"""
    tests = checkboxlist_dialog(
        title="Tests to run",
        text="What tests should run?",
        values=[
            ("latency", "Latency test"),
            ("rot", "Rotation test"),
            ("motor", "Motor power test"),
        ]
    ).run()
    if tests is None:
        return
    for drone in drones:
        if drones[drone][1]:
            check_drone(drone, DEF_URI + drones[drone][0],
                    'latency' in tests, 'rot' in tests, 'motor' in tests)

def cmd_show():
    """cmd_show represents the show command"""
    print(colorama.Fore.CYAN + "=== Available Drones ===")
    for drone in drones:
        print(drone + ":\t(radio://x/" + drones[drone][0] +") - ", end='')
        if drones[drone][1]:
            print(colorama.Back.GREEN + colorama.Fore.BLACK + "Enabled")
        else:
            print(colorama.Back.RED + "Disabled")

drone_names = []
for x in drones:
    drone_names.append(x)
drone_completer = WordCompleter(drone_names)

class DroneValidator(Validator):
    """DroneValidator is a validator prompt_toolkit validator, that checks
    if the drone name exists."""
    def validate(self, document):
        """validate function validates the drone name."""
        text = document.text
        lst = text.split(",")
        if len(lst) > 1:
            for drone in lst:
                if drone not in drones:
                    raise ValidationError(message='Drone ('+drone+') doesn\'t exist')
        else:
            if text not in drones:
                raise ValidationError(message='Drone doesn\'t exist')

def cmd_enable():
    """cmd_enable represents the enable command."""
    text = prompt('enable drone> ', completer=drone_completer, validator=DroneValidator())
    lst = text.split(",")
    if len(lst) == 1:
        drones[text][1] = True
    else:
        for drone in lst:
            drones[drone][1] = True

def cmd_disable():
    """cmd_disable represents the disable command."""
    text = prompt('disable drone> ', completer=drone_completer, validator=DroneValidator())
    lst = text.split(",")
    if len(lst) == 1:
        drones[text][1] = False
    else:
        for drone in lst:
            drones[drone][1] = False

def cmd_exit():
    sys.exit(0)

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
        "exit": cmd_exit,
        "quit": cmd_exit,
        "q": cmd_exit,
    }
    while 1:
        user_input = prompt('> ', history=FileHistory('hist.txt'))
        if user_input in switch:
            switch.get(user_input)()
        else:
            print("Unknown command")
