#!/usr/bin/env python3


# import adafruit_mpr121
import adafruit_drv2605
import board
import busio
import gc
import machine
import time

# EffectChainType = list[tuple[int, float, float, str]]


class TimeProtocolHHMM:
    # """A base class for a Time Protocol for transmitting hours and minutes."""

    def __init__(self):
        pass

    # def __init__(self):
    #     self.timeIntervalToEffectMap = {"12hr": 10, "1hr": 1, "5min": 7}

    # def _generateHoursEffectChain(self, HH: int):
    #     "Abstract method definition for generating effect chain for hours."
    #     pass

    # def _generateMinutesEffectChain(self, MM: int):
    #     "Abstract method definition for generating effect chain for hours."
    #     pass

    # def generateEffectChain(self, HHMM):
    #     """Abstract method definition for generating effect chain for HHMM."""
    #     pass


class TimeProtocolHHLeftMMRight(TimeProtocolHHMM):
    # """
    # Implementation of a time protocol where HH are transmitted on left finger,
    # then MM are transmitted on right finger.
    # """

    def __init__(self):
        # Separation between transmitting HH and MM
        self.HHMMseparation = 1

    def _generateHoursEffectChain(self, HH: int):
        """Return a list of Effects for the buzzer to play to transmit HH."""
        hoursChain = []
        # Add effects to signify 12 hours.
        if HH >= 12:
            # print("HH > 12")
            id = 10
            effect_duration = 0.5
            sleep_duration = 0.4
            hoursChain.append((id, effect_duration, sleep_duration, "L"))
            # Decrement time for the next hours iteration
            HH -= 12
        # Add effects for the remaining hours
        for _ in range(0, HH):
            # print(f"HH = {HH}")
            id = 1
            effect_duration = 0.65
            sleep_duration = 0.2
            hoursChain.append((id, effect_duration, sleep_duration, "L"))
        return hoursChain

    def _generateMinutesEffectChain(self, MM: int):
        """Return a list of Effects for the buzzer to play to transmit MM."""
        minutesChain = []
        # Add effects to signify 12 hours.
        if MM >= 30:
            # print("MM > 30")
            id = 10  # soft bump for 30 minutes
            effect_duration = 0.5
            sleep_duration = 0.4
            minutesChain.append((id, effect_duration, sleep_duration, "R"))
            # Decrement time for the next hours iteration
            MM -= 30
        # Add effects for the remaining hours
        for _ in range(0, MM // 5):
            # print(f"MM = {MM}")
            # TODO add this to dictionary
            id = 1  # sharp click for 5 minutes
            effect_duration = 0.5
            sleep_duration = 0.2
            minutesChain.append((id, effect_duration, sleep_duration, "R"))
        return minutesChain

    def generateEffectChain(self, HH, MM):
        """Return an EffectChain for HHMM."""
        # TODO Make EffectChain data class
        effectChain = self._generateHoursEffectChain(HH)
        effectChain.append((-1, 0, 0, self.HHMMseparation))
        effectChain = effectChain + self._generateMinutesEffectChain(MM)
        return effectChain


class BuzzerController:
    """A class to play effects from an effect chain through the correct buzzers."""

    def __init__(self, buzzerLeft: Buzzer, buzzerRight: Buzzer):
        self.buzzerLeft = buzzerLeft
        self.buzzerRight = buzzerRight

    def playEffectChain(self, effectChain: list[tuple[int, float, float, str]]):
        """Play effects from a chain.
        Buzz a chain of effects with pauses in between.

        effectChain is a list of tuples (effect_id, effect_duration, sleep_duration, buzzer_id)
        """
        # drv.sequence[1] = adafruit_drv2605.Pause(0.5)  # Pause for half a second
        for effectLink in effectChain:
            id, effect_duration, sleep_duration, buzzer_id = effectLink
            # Sleep between effects if effect id is -1
            if id == -1:
                time.sleep(sleep_duration)
            else:
                self.playEffectOnBuzzer(id, effect_duration, buzzer_id)

    def playEffectOnBuzzer(self, id, effect_duration, buzzer_id):
        """Play an effect on the correct buzzer."""
        if buzzer_id == "L":
            self.buzzerLeft.buzzEffectWithDuration(id, effect_duration)
        else:
            print("Buzz on right")
            self.buzzerRight.buzzEffectWithDuration(id, effect_duration)


class Buzzer:
    """
    A wrapper and interface to Adafruit's DRV2605 haptic controller
    breakout.
    """

    def __init__(self, DATA_GP, CLOCK_GP):
        """Initialize the haptic controller."""
        hapticI2C = busio.I2C(CLOCK_GP, DATA_GP)
        self._hapController = adafruit_drv2605.DRV2605(hapticI2C)

    # def buzzEffect(self, effect_id: int):
    #     """Buzz an effect for its default duration."""
    #     self._hapController.sequence[0] = adafruit_drv2605.Effect(effect_id)
    #     self._hapController.play()

    def buzzEffectWithDuration(self, effect_id: int, duration: float):
        """Buzz an effect for a specified duration."""
        self._hapController.sequence[0] = adafruit_drv2605.Effect(effect_id)
        self._hapController.play()
        time.sleep(duration)
        self._hapController.stop()


class Hapticlock:
    """The Hapticlock class."""

    def __init__(self):
        # Event loop sleep time between repeats
        self.EVENT_LOOP_SLEEP = 5
        # Time protocol
        self.time_protocol = TimeProtocolHHLeftMMRight()
        # Buzzer controller
        # Capacitive touch breakout pin numbers
        # self.CAP_TOUCH_LEFT = 0
        # self.CAP_TOUCH_RIGHT = 1
        # Capacitive touch GP pins
        # self.CAP_TOUCH_BOARD_DATA_GP = board.GP12
        # self.CAP_TOUCH_BOARD_CLOCK_GP = board.GP13
        # FSR GP pin
        # self.FSR_GP_NUM: int = 26
        # FSR minimum force (u16)
        # self.FSR_MIN_FORCE = 40000
        # Haptic controllers
        self.HAPTIC_CONTROLLER_DATA_GP_LEFT = board.GP14
        self.HAPTIC_CONTROLLER_CLOCK_GP_LEFT = board.GP15
        self.HAPTIC_CONTROLLER_DATA_GP_RIGHT = board.GP12
        self.HAPTIC_CONTROLLER_CLOCK_GP_RIGHT = board.GP13

        # RTC
        # self.rtc = DS3231()
        self.initializeComponents()
        # self.buzzer_controller = BuzzerController(self.buzzerLeft, self.buzzerRight)

    # def initializeCapacitiveTouch(self):
    #     """Initialize the capacitive touch breakout board."""
    #     capacitiveI2C = busio.I2C(
    #         self.CAP_TOUCH_BOARD_CLOCK_GP, self.CAP_TOUCH_BOARD_DATA_GP
    #     )
    #     mpr121 = adafruit_mpr121.MPR121(capacitiveI2C)
    #     self.capLeft = mpr121[self.CAP_TOUCH_LEFT]
    #     self.capRight = mpr121[self.CAP_TOUCH_RIGHT]

    # def initializeFSR(self):
    #     """Initialize the force sensor resistor (FSR)."""
    #     self.fsr = machine.ADC(self.FSR_GP_NUM)

    def initializeHapticController(self):
        """Initialize the haptic motor controller."""
        self.buzzerLeft = Buzzer(
            self.HAPTIC_CONTROLLER_DATA_GP_LEFT, self.HAPTIC_CONTROLLER_CLOCK_GP_LEFT
        )
        self.buzzerRight = Buzzer(
            self.HAPTIC_CONTROLLER_DATA_GP_RIGHT, self.HAPTIC_CONTROLLER_CLOCK_GP_RIGHT
        )

    def initializeComponents(self):
        """Set up sensor and actuator objects."""
        # self.initializeCapacitiveTouch()
        self.initializeHapticController()
        # self.initializeFSR()

    # def playAllHapticControllerEffects(self):
    #     """Play through all 123 haptic controller effects."""
    #     # PAUSE_BETWEEN_EFFECTS = 1  # seconds
    #     effect_id = 1
    #     while True:
    #         gc.collect()
    #         print(f"Playing effect #{effect_id}")
    #         self.buzzerLeft.buzzEffectWithDuration(effect_id, 1)
    #         # time.sleep(1)
    #         effect_id += 1
    #         if effect_id > 123:
    #             effect_id = 1

    def getHHMM(self):
        """Return the time in HHMM format."""
        # year, month, mday, hour, minute, second, weekday, yearday
        # _, _, _, hour, minute, _, _, _ = time.localtime()
        # return (hour, minute)
        # Use timeTuple to make testing with custom times more easy.
        # timeTuple = (hour, minute)
        # timeTuple = (15, 26)
        # return (18, 26)
        _, _, _, _, hour, minute, _ = self.rtc.DS3231_ReadTime(mode=1)
        return hour, minute

    # def buzzAlert(self):
    #     """Buzz a sequence to alert the user."""
    #     pass

    def buzzTime(self):
        """Buzz the time to the user."""
        HH, MM = self.getHHMM()
        # print(f"Buzzing time:  {HH}:{MM}")
        effectChain = self.time_protocol.generateEffectChain(HH, MM)
        # print(f"Effect chain: {effectChain}")
        self.buzzer_controller.playEffectChain(effectChain)

    # def checkForceEvents(self):
    #     """Check for FSR events.

    #     Currently just checks if force > MIN_FORCE."""
    #     forceU16 = self.fsr.read_u16()
    #     if forceU16 > self.FSR_MIN_FORCE:
    #         print("Force detected. Entering configuration mode (not yet implemented.)")

    # def checkCapacitiveEvents(self):
    #     """Check for capacitive touch events."""
    #     if self.capLeft.value and self.capRight.value:
    #         print("Both capacitive sensors touched.")
    #         self.buzzTime()

    def run(self):
        """The Hapticlock event loop."""
        # print("Entering event loop.")
        # self.playAllHapticControllerEffects()
        while True:
            gc.collect()
            self.buzzTime()
            # while True:
            # Check FSR
            # self.checkForceEvents()

            # Check cap touch
            # self.checkCapacitiveEvents()

            # Sleep
            time.sleep(self.EVENT_LOOP_SLEEP)


# class DS3231:
#     """Simple DS3231 class."""

#     w = ["FRI", "SAT", "SUN", "MON", "TUE", "WED", "THU"]
#     # If you want different names for Weekdays, feel free to add. Couple examples below:
#     # w = ["FR", "SA", "SU", "MO", "TU", "WE", "TH"]
#     # w = ["Friday", "Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
#     # w = ["Freitag", "Samstag", "Sonntag", "Montag", "Dienstag", "Mittwoch", "Donnerstag"]
#     # w = ["viernes", "sabado", "domingo", "lunes", "martes", "miercoles", "jueves"]

#     # Initialisation of RTC object. Several settings are possible but everything is optional.
#     # If you meet these standards no parameters are required.
#     def __init__(
#         #     capacitiveI2C = busio.I2C(
#         #         self.CAP_TOUCH_BOARD_CLOCK_GP, self.CAP_TOUCH_BOARD_DATA_GP
#         #     )
#         #     mpr121 = adafruit_mpr121.MPR121(capacitiveI2C)
#         self,
#         sda_pin=16,
#         scl_pin=17,
#         port=0,
#         speed=100000,
#         address=0x68,
#         register=0x00,
#     ):
#         self.rtc_address = address  # for using different i2c address
#         self.rtc_register = (
#             register  # for using different register on device. DON'T change for DS3231
#         )
#         # Old I2C
#         sda = machine.Pin(sda_pin)  # configure the sda pin
#         scl = machine.Pin(scl_pin)  # configure the scl pin
#         self.i2c = machine.I2C(
#             port, sda=sda, scl=scl, freq=speed
#         )  # configure the i2c interface with given parameters

#     # Method for setting the Time
#     # def DS3231_SetTime(self, NowTime=b"\x00\x23\x12\x28\x14\x07\x21"):
#     #     # NowTime has to be in format like b'\x00\x23\x12\x28\x14\x07\x21'
#     #     # It is encoded like this           sec min hour week day month year
#     #     # Then it's written to the DS3231
#     #     self.i2c.writeto_mem(int(self.rtc_address), int(self.rtc_register), NowTime)

#     # DS3231 gives data in bcd format. This has to be converted to a binary format.
#     def bcd2bin(self, value):
#         return (value or 0) - 6 * ((value or 0) >> 4)

#     # Add a 0 in front of numbers smaller than 10
#     def pre_zero(self, value):
#         pre_zero = True  # Change to False if you don't want a "0" in front of numbers smaller than 10
#         if pre_zero:
#             if value < 10:
#                 value = f"0{value}"  # From now on the value is a string!
#         return value

#     # Read the Realtime from the DS3231 with errorhandling. Currently two output modes can be used.
#     def DS3231_ReadTime(self, mode=0) -> tuple:
#         try:
#             # Read RT from DS3231 and write to the buffer variable. It's a list with 7 entries.
#             # Every entry needs to be converted from bcd to bin.
#             buffer = self.i2c.readfrom_mem(self.rtc_address, self.rtc_register, 7)
#             # The year consists of 2 digits. Here 2000 years are added to get format like "2021"
#             # year = self.bcd2bin(buffer[6]) + 2000
#             # Just put the month value in the month variable and convert it.
#             # month = self.bcd2bin(buffer[5])
#             # Same for the day value
#             # day = self.bcd2bin(buffer[4])
#             # Weekday will be converted in the weekdays name or shortform like "Sunday" or "SUN"
#             # weekday = self.w[self.bcd2bin(buffer[3])]
#             # Uncomment the line below if you want a number for the weekday and comment the line before.
#             # weekday = self.bcd2bin(buffer[3])
#             # Convert bcd to bin and add a "0" if necessary
#             hour = self.pre_zero(self.bcd2bin(buffer[2]))
#             # Convert bcd to bin and add a "0" if necessary
#             minute = self.pre_zero(self.bcd2bin(buffer[1]))
#             # Convert bcd to bin and add a "0" if necessary
#             # second = self.pre_zero(self.bcd2bin(buffer[0]))
#             # return (year, month, day, weekday, hour, minute, second)
#             return (hour, minute)
#             # if mode == 0:  # Mode 0 returns a list of second, minute, ...
#             #     return second, minute, hour, weekday, day, month, year
#             # if mode == 1:
#             # Mode 1 returns a formated string with time, weekday and date
#             # time_string = (
#             #     f"{hour}:{minute}:{second}      {weekday} {day}.{month}.{year}"
#             # )
#             # return (year, month, day, weekday, hour, minute, second)
#             # return time_string
#             # If you need different format, feel free to add

#         except Exception as e:
#             raise e
#             # return (
#             #     "Error: is the DS3231 not connected or some other problem (%s)" % e
#             # )  # exception occurs in any case of error.


if __name__ == "__main__":
    # pass
    hapticlock = Hapticlock()
    # rtc = DS3231()
    # print(rtc.DS3231_ReadTime())
    # hapticlock.testRTC()
    # hapticlock.run()
