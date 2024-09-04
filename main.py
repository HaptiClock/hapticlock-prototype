#!/usr/bin/env python3

import time

# Time constants (seconds)
PULSE_TIMES = {"hh12+": 1, "hh": 0.5, "5m": 0.3}
WAIT_TIME_BETWEEN_H_M = 1
WAIT_TIME_BETWEEN_H = 0.2
WAIT_TIME_BETWEEN_5M = 0.1


def getHHMM():
    year, month, mday, hour, minute, second, weekday, yearday = time.localtime()
    # return (hour, minute)
    return (3, 26)


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
