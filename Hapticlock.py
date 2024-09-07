#!/usr/bin/env python3


import adafruit_mpr121
import adafruit_drv2605
import board
import busio
import gc
import machine
import time


# class TimeProtocol:
#     """
#     A base class for a Time Protocol.
#     """

#     def __init__(self):
#         self.effectIDs = {"12hr": 10, "1hr": 1, "5min": 7}

#     def generateBuzzHoursList(self, HH: int):
#         """Return a list of Effects for the buzzer to play to transmit HH."""
#         effects = []
#         if HH >= 12:
#             effects.append(adafruit_drv2605.Effect(self.effectIDs["12hr"]))
#             HH = -12
#         for _ in range(0, HH):
#             effects.append(adafruit_drv2605.Effect(self.effectIDs["1hr"]))


class Buzzer:
    """
    A wrapper and interface to Adafruit's DRV2605 haptic controller
    breakout.
    """

    def __init__(self, DATA_GP, CLOCK_GP):
        """Initialize the haptic controller."""
        self.DATA_GP = DATA_GP
        self.CLOCK_GP = CLOCK_GP
        hapticI2C = busio.I2C(self.CLOCK_GP, self.DATA_GP)
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

    # def buzzEffectChain(self, effectChain: list[tuple[int, float]]):
    #     """Buzz a chain of effects with pauses in between."""
    #     # iterate through effect chain
    #     #   if effect ID is 0, no effect, just pause
    #     # drv.sequence[1] = adafruit_drv2605.Pause(0.5)  # Pause for half a second
    #     for effectLink in effectChain:
    #         id, duration = effectLink
    #         if id == 0:
    #             time.sleep(duration)
    #         else:
    #             self.buzzEffectWithDuration(id, duration)


class Hapticlock:
    """The Hapticlock class."""

    def __init__(self):
        # Event loop sleep time between repeats
        self.EVENT_LOOP_SLEEP = 0.10
        # Capacitive touch breakout pin numbers
        self.CAP_TOUCH_LEFT = 0
        self.CAP_TOUCH_RIGHT = 1
        # Capacitive touch GP pins
        self.CAP_TOUCH_BOARD_DATA_GP = board.GP12
        self.CAP_TOUCH_BOARD_CLOCK_GP = board.GP13
        # FSR GP pin
        self.FSR_GP_NUM: int = 26
        # FSR minimum force (u16)
        self.FSR_MIN_FORCE = 40000
        # Hapic controllers
        self.HAPTIC_CONTROLLER_DATA_GP_LEFT = board.GP14
        self.HAPTIC_CONTROLLER_CLOCK_GP_LEFT = board.GP15
        self.HAPTIC_CONTROLLER_DATA_GP_RIGHT = board.GP12
        self.HAPTIC_CONTROLLER_CLOCK_GP_RIGHT = board.GP13

    # def initializeCapacitiveTouch(self):
    #     """Initialize the capacitive touch breakout board."""
    #     capacitiveI2C = busio.I2C(
    #         self.CAP_TOUCH_BOARD_CLOCK_GP, self.CAP_TOUCH_BOARD_DATA_GP
    #     )
    #     mpr121 = adafruit_mpr121.MPR121(capacitiveI2C)
    #     self.capLeft = mpr121[self.CAP_TOUCH_LEFT]
    #     self.capRight = mpr121[self.CAP_TOUCH_RIGHT]

    def initializeFSR(self):
        """Initialize the force sensor resistor (FSR)."""
        self.fsr = machine.ADC(self.FSR_GP_NUM)

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

    def playAllHapticControllerEffects(self):
        """Play through all 123 haptic controller effects."""
        # PAUSE_BETWEEN_EFFECTS = 1  # seconds
        effect_id = 1
        while True:
            gc.collect()
            print(f"Playing effect #{effect_id}")
            self.buzzerLeft.buzzEffectWithDuration(effect_id, 1)
            # time.sleep(1)
            effect_id += 1
            if effect_id > 123:
                effect_id = 1

    # def getHHMM(self):
    #     """Return the time in HHMM format."""
    #     # year, month, mday, hour, minute, second, weekday, yearday
    #     _, _, _, hour, minute, _, _, _ = time.localtime()
    #     # return (hour, minute)
    #     # Use timeTuple to make testing with custom times more easy.
    #     # timeTuple = (hour, minute)
    #     timeTuple = (3, 26)
    #     return timeTuple

    # def buzzAlert(self):
    #     """Buzz a sequence to alert the user."""
    #     pass

    # def buzzHours(self, HH):
    #     """Buzz the hours."""
    #     pass

    # def buzzMinutes(self, MM):
    #     """Buzz the minutes."""
    #     pass

    # def buzzTime(self):
    #     """Buzz the time to the user."""
    #     HH, MM = self.getHHMM()
    #     self.buzzHours(HH)
    #     self.buzzMinutes(MM)

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
        self.initializeComponents()
        print("Entering event loop.")
        self.playAllHapticControllerEffects()
        # while True:
        # Check FSR
        # self.checkForceEvents()

        # Check cap touch
        # self.checkCapacitiveEvents()

        # Sleep
        # time.sleep(self.EVENT_LOOP_SLEEP)


if __name__ == "__main__":
    hapticlock = Hapticlock()
    hapticlock.run()
