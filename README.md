# Crazyflie Check

## 1. Description

An interactive and comprehensive check script for the Crazyflie drones.

Launching the program provides you with an interactive terminal, with commands
you can run to perform tasks.

<a href="https://asciinema.org/a/1WwulP6gGqOpRmWbdwhR87WEs?autoplay=1"><img src="https://asciinema.org/a/1WwulP6gGqOpRmWbdwhR87WEs.png" width="836"/></a>

## 2. Usage

Run:

```sh
python3 main.py
```

## 3. Commands

This will run an interactive console. Below is a list
of some commands:

- enable: Enable a drone. Can take CSV list of drones.
- disable: Disable a drone. Can take CSV list of drones.
- show: List drones with addresses, and whether they are enabled.
- run: Run the tests.
- exit/quit: Exit the program
