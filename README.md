# Crazyflie Check

<a href="https://asciinema.org/a/1WwulP6gGqOpRmWbdwhR87WEs?autoplay=1"><img src="https://asciinema.org/a/1WwulP6gGqOpRmWbdwhR87WEs.png" width="836"/></a>

(this is a video, click to watch)

## 1. Description

An interactive and comprehensive check script for the Crazyflie drones.

Launching the program provides you with an interactive terminal, with commands
you can run to perform tasks.

The current tests that can be run:

- Latency test
	- Checks the latency between your computer and the drone. Allows you to
	  rule out latency related issues.
- Propeller test
	- Performs a propeller test, testing each individual propeller for any
	  abnormalities. This allows you to identify issues with defected
	  propellers before starting the mission.
- Rotation test
	- This is a manual test, which requires you to rotate the Crazyflie
	  when you press enter. It will check if the roll/pitch/yaw readings
	  are responsive. If any of the sensors are not reporting a variance in
	  values, it will be labeled as a fail.
- Battery test (always runs)
	- Performs a battery stress test, and reads out the battery voltage.
	  This provides an accurate battery level reading.
- Memory error count test (always runs)
	- It will alert you if it detects a drone with an error count greater
	  than zero.

## 2. Usage

Run:

```sh
python3 main.py
```

## 3. Commands

These are the following commands available:

- enable: Enable a drone. Can take CSV list of drones.
- disable: Disable a drone. Can take CSV list of drones.
- show: List drones with addresses, and whether they are enabled.
- run: Run the tests.
- exit/quit: Exit the program
