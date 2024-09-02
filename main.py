#!/usr/bin/env python3

import adafruit_mpr121
import board
import busio
import machine
import time

# Time constants (seconds)
PULSE_TIMES = {"hh12+": 1, "hh": 0.7, "5m": 0.5}
WAIT_TIME_BETWEEN_H_M = 1
WAIT_TIME_BETWEEN_H = 0.2
WAIT_TIME_BETWEEN_5M = 0.2
EVENT_LOOP_SLEEP = 0.10

# Force constants (u16)
MIN_FORCE = 40000

# Set up haptic motor
haptic = machine.Pin(6, machine.Pin.OUT)
# Set up force-resistance sensor
fsr = machine.ADC(26)
# Set up capacitive touch
i2c = busio.I2C(board.GP17, board.GP16)
mpr121 = adafruit_mpr121.MPR121(i2c)
cap = mpr121[0]


def getHHMM():
    year, month, mday, hour, minute, second, weekday, yearday = time.localtime()
    return (hour, minute)


def buzzPulse(buzzTime):
    """Activate the haptic, sleep for buzzTime, then deactive the haptic."""
    haptic.value(1)
    time.sleep(buzzTime)
    haptic.value(0)


def hourSleep():
    """Sleep between transmitHour()."""
    time.sleep(WAIT_TIME_BETWEEN_H)


def fiveMinSleep():
    """Sleep between transmitMin()."""
    time.sleep(WAIT_TIME_BETWEEN_5M)


def buzz12Hour():
    """Send a haptic pulse signifying twelve hours.

    Sleeps after the pulse to allow user to distinguish next pulse."""
    print("Buzzing 12h.")
    buzzPulse(PULSE_TIMES["hh12+"])
    hourSleep()


def buzzHour():
    """Send a haptic pulse signifying one hour.

    Sleeps after the pulse to allow user to distinguish next pulse."""
    print("Buzzing 1h.")
    buzzPulse(PULSE_TIMES["hh"])
    hourSleep()


def buzzFiveMin():
    """Send a haptic pulse signifying five minutes.

    Sleeps after the pulse to allow user to distinguish next pulse."""
    print("Buzzing 5m.")
    buzzPulse(PULSE_TIMES["5m"])
    fiveMinSleep()


def transmitHours(hh):
    """Transmit pulses for the hours."""
    if hh >= 12:
        print("Hours greater than 12.")
        buzz12Hour()
    else:
        print("Hours less than 12.")
        for _ in range(0, hh):
            buzzHour()


def transmitMins(mm):
    """Transmit pulses for the minutes."""
    fiveMins = mm // 5

    for _ in range(0, fiveMins):
        buzzFiveMin()


def buzzTime():
    hh, mm = getHHMM()
    print(f"Buzzing time: {hh}:{mm}")
    transmitHours(hh)
    time.sleep(WAIT_TIME_BETWEEN_H_M)
    transmitMins(mm)


def main():
    # Event loop
    while True:
        # Check FSR
        forceU16 = fsr.read_u16()
        if forceU16 > MIN_FORCE:
            print("Force detected. Entering configuration mode (not yet implemented.)")
        # Check cap touch
        if cap.value:
            print(f"Time: {time.time()}")
            buzzTime()
        time.sleep(EVENT_LOOP_SLEEP)


main()
# Turn off haptic (debug)
# haptic.value(0)
