#!/usr/bin/env python3

import adafruit_mpr121
import board
import busio
import machine
import time

PULSE_TIMES = {"hh12+": 1, "hh": 0.7, "5m": 0.5}


# Set up haptic motor
haptic = machine.Pin(6, machine.Pin.OUT)


def getHHMM():
    year, month, mday, hour, minute, second, weekday, yearday = time.localtime()
    return (hour, minute)


def buzzPulse(buzzTime):
    haptic.value(1)
    time.sleep(buzzTime)
    haptic.value(0)


def hourSleep():
    time.sleep(0.2)


def minSleep():
    time.sleep(0.2)


def buzzHours(hh):
    if hh >= 12:
        print("Hours greater than 12.")
        print("Buzzing 12h.")
        buzzPulse(PULSE_TIMES["hh12+"])

        hourSleep()

        for hour in range(0, hh - 12):
            print("Buzzing 1h.")
            buzzPulse(PULSE_TIMES["hh"])
            hourSleep()
    else:
        print("Hours less than 12.")
        for hour in range(0, hh):
            print("Buzzing 1h.")
            buzzPulse(PULSE_TIMES["hh"])
            hourSleep()


def buzzMins(mm):
    fives: int = mm // 5
    for five in range(0, fives):
        print("Buzzing 5m.")
        buzzPulse(PULSE_TIMES["5m"])
        minSleep()


def buzzTime():
    hh, mm = getHHMM()
    print(f"Buzzing time: {hh}:{mm}")
    buzzHours(hh)
    time.sleep(1)
    buzzMins(mm)


def main():
    # Set up capacitive touch
    i2c = busio.I2C(board.GP17, board.GP16)
    mpr121 = adafruit_mpr121.MPR121(i2c)
    cap = mpr121[0]

    haptic.value(0)

    while True:
        if cap.value:
            print(f"Time: {time.time()}")
            buzzTime()


main()
