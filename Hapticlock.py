#!/usr/bin/env python3


import adafruit_mpr121
import adafruit_drv2605
import board
import busio
import machine
import time


class Hapticlock:
    """The Hapticlock class."""

    def __init__(self):
        # Event loop sleep time between repeats
        self.EVENT_LOOP_SLEEP = 0.10
        # Capacitive touch breakout pin numbers
        self.CAP_TOUCH_LEFT = 0
        self.CAP_TOUCH_RIGHT = 1
        # Capacitive touch GP pins
        self.CAP_TOUCH_BOARD_DATA_GP = board.GP16
        self.CAP_TOUCH_BOARD_CLOCK_GP = board.GP17
        # Haptic motor controller GP pins
        self.HAPTIC_CONTROLLER_DATA_GP = board.GP18
        self.HAPTIC_CONTROLLER_CLOCK_GP = board.GP19
        # FSR GP pin
        self.FSR_GP_NUM: int = 26
        # FSR minimum force (u16)
        self.FSR_MIN_FORCE = 40000

    def initializeCapacitiveTouch(self):
        """Initialize the capacitive touch breakout board."""
        capacitiveI2C = busio.I2C(
            self.CAP_TOUCH_BOARD_CLOCK_GP, self.CAP_TOUCH_BOARD_DATA_GP
        )
        mpr121 = adafruit_mpr121.MPR121(capacitiveI2C)
        self.capLeft = mpr121[self.CAP_TOUCH_LEFT]
        self.capRight = mpr121[self.CAP_TOUCH_RIGHT]

    def initializeFSR(self):
        """Initialize the force sensor resistor (FSR)."""
        self.fsr = machine.ADC(self.FSR_GP_NUM)

    def initializeHapticController(self):
        """Initialize the haptic motor controller."""
        hapticI2C = busio.I2C(
            self.HAPTIC_CONTROLLER_CLOCK_GP, self.HAPTIC_CONTROLLER_DATA_GP
        )
        self.hapController = adafruit_drv2605.DRV2605(hapticI2C)

    def initializeComponents(self):
        """Set up sensor and actuator objects."""
        self.initializeCapacitiveTouch()
        self.initializeHapticController()
        self.initializeFSR()

    def playAllHapticControllerEffects(self):
        """Play through all 123 haptic controller effects."""
        PAUSE_BETWEEN_EFFECTS = 1  # seconds
        effect_id = 1
        while True:
            print(f"Playing effect #{effect_id}")
            self.hapController.sequence[0] = adafruit_drv2605.Effect(effect_id)
            # You can assign effects to up to 8 different slots to combine
            # them in interesting ways. Index the sequence property with a
            # slot number 0 to 7.
            # Optionally, you can assign a pause to a slot. E.g.
            # drv.sequence[1] = adafruit_drv2605.Pause(0.5)  # Pause for half a second
            self.hapController.play()  # play the effect
            time.sleep(PAUSE_BETWEEN_EFFECTS)
            self.hapController.stop()  # stop (if it's still running)
            # Increment effect ID and wrap back around to 1.
            effect_id += 1
            if effect_id > 123:
                effect_id = 1

    def checkForceEvents(self):
        """Check for FSR events.

        Currently just checks if force > MIN_FORCE."""
        forceU16 = self.fsr.read_u16()
        if forceU16 > self.FSR_MIN_FORCE:
            print("Force detected. Entering configuration mode (not yet implemented.)")

    def checkCapacitiveEvents(self):
        """Check for capacitive touch events."""
        if self.capLeft.value and self.capRight.value:
            print("Both capacitive sensors touched.")
            # print(f"Time: {time.time()}")
            # buzzTime()

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
