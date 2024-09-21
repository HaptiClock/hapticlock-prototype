#!/usr/bin/env python3


import adafruit_mpr121
import adafruit_drv2605
import board
import busio
import gc
import machine
import network
import ntptime
import time


class EffectNode:
    """An adafruit_drv2605.Effect with duration, sleep duration, and buzzer."""

    def __init__(self, timeThresholdEffectData: TimeThresholdEffectData, buzzer):
        """Simple constructor."""
        # TODO Use default sleep duration for default pause duration
        self.effect = timeThresholdEffectData.effect
        self.effect_duration: float = timeThresholdEffectData.effect_duration
        self.sleep_duration: float = timeThresholdEffectData.sleep_duration
        self.buzzer: str = buzzer


class PauseNode(EffectNode):
    """An empty class for representing Pauses."""

    def __init__(self, pause_time=1):
        """Dummy constructor for a Pause."""
        super().__init__(TimeThresholdEffectData(-1, 0, 0), "")


class EffectChain:
    """A list of EffectNodes."""

    def __init__(self):
        """Initialize chain as an empty list."""
        self.chain: list[EffectNode] = []

    def addNodeFromConfig(self, effect, effect_duration, sleep_duration, buzzer):
        """Build and append an EffectNode to the chain from config data."""
        self.chain.append(EffectNode(effect, effect_duration, sleep_duration, buzzer))

    def addNodesFromList(self, effectNodes: list[EffectNode]):
        """Append EffectNodes to the chain from a list."""
        self.chain = self.chain + effectNodes

    def addPause(self, pause_time=1):
        """Add a PauseNode to the effect chain."""
        self.chain.append(PauseNode(pause_time))


class TimeProtocolHHMM:
    # """A base class for a Time Protocol for transmitting hours and minutes."""

    def __init__(self):
        pass

    def _generateHoursEffectChain(self, HH: int):
        "Abstract method definition for generating effect chain for hours."
        pass

    def _generateMinutesEffectChain(self, MM: int):
        "Abstract method definition for generating effect chain for hours."
        pass

    def generateEffectChain(self, HHMM):
        """Abstract method definition for generating effect chain for HHMM."""
        pass


class TimeThresholdEffectData:
    """
    A data class for associating a time threshold with an Effect, effect
    duration, and sleep duration. If a time is greater than the threshold, the
    associated Effect, effect duration, and sleep duration are added to the
    EffectChain used for communicating that time.

    The threshold value (e.g. "12hr") is mapped to its TimeThresholdData object
    in a TimeProtocol.
    """

    def __init__(
        self,
        effect: adafruit_drv2605.Effect,
        effect_duration: float,
        sleep_duration: float,
    ):
        self.effect = effect
        self.effect_duration = effect_duration
        self.sleep_duration = sleep_duration


class TimeProtocolHHLeftMMRight(TimeProtocolHHMM):
    """
    Implementation of a time protocol where HH are transmitted on left finger,
    then MM are transmitted on right finger.
    """

    def __init__(self):
        # Time delay between transmitting HH and MM
        self.delayBetweenHHMM = 1
        # Map time thresholds to effects
        self.timeThresholdEffectMap = {
            "12hr": TimeThresholdEffectData(adafruit_drv2605.Effect(10), 0.5, 0.5),
            "1hr": TimeThresholdEffectData(adafruit_drv2605.Effect(1), 0.65, 0.2),
            "30min": TimeThresholdEffectData(adafruit_drv2605.Effect(10), 0.5, 0.4),
            "5min": TimeThresholdEffectData(adafruit_drv2605.Effect(7), 0.5, 0.2),
        }
        self.timeThresholdDurationMap = {}

    def _generateHoursEffectChain(self, HH: int) -> list[EffectNode]:
        """Return a list of EffectNodes for the buzzer to play to transmit HH."""
        hoursChain = []
        # Add effects to signify 12 hours.
        if HH >= 12:
            timeThresholdEffectData = self.timeThresholdEffectMap["12hr"]
            hoursChain.append(EffectNode(timeThresholdEffectData, "L"))
            # Decrement time for the next hours iteration
            # TODO verify that HH is correct, and not 1 too many
            HH -= 12
        # Add effects for the remaining hours
        for _ in range(0, HH):
            timeThresholdEffectData = self.timeThresholdEffectMap["1hr"]
            hoursChain.append(EffectNode(timeThresholdEffectData, "L"))
        return hoursChain

    def _generateMinutesEffectChain(self, MM: int) -> list[EffectNode]:
        """Return a list of Effects for the buzzer to play to transmit MM."""
        minutesChain = []
        # Add effects to signify 12 hours.
        if MM >= 30:
            timeThresholdEffectData = self.timeThresholdEffectMap[
                "30min"
            ]  # soft bump for 30 minutes
            minutesChain.append(EffectNode(timeThresholdEffectData, "R"))
            # Decrement time for the next hours iteration
            # TODO verify that MM is correct, and not 1 too many
            MM -= 30
        # Add effects for the remaining 5 minute intervals
        num_5min_intervals_rounded = round(MM / 5)
        for _ in range(0, num_5min_intervals_rounded):
            timeThresholdEffectData = self.timeThresholdEffectMap[
                "5min"
            ]  # sharp click for 5 minutes
            minutesChain.append(EffectNode(timeThresholdEffectData, "R"))
            # minutesChain.append((id, effect_duration, sleep_duration, "R"))
        return minutesChain

    def generateEffectChain(self, HH, MM) -> EffectChain:
        """Return an EffectChain for HHMM."""
        # If minutes round up to the next hour, increment HH and set MM to zero.
        if MM > 58:
            HH += 1
            MM = 0
        effectChain = EffectChain()
        effectChain.addNodesFromList(self._generateHoursEffectChain(HH))
        effectChain.addPause(self.delayBetweenHHMM)
        effectChain.addNodesFromList(self._generateMinutesEffectChain(MM))
        return effectChain


class Buzzer:
    """
    A wrapper and interface to Adafruit's DRV2605 haptic controller
    breakout.
    """

    def __init__(self, DATA_GP, CLOCK_GP):
        """Initialize the haptic controller."""
        self._hapController = adafruit_drv2605.DRV2605(busio.I2C(CLOCK_GP, DATA_GP))

    def buzzEffectWithDuration(self, effect: adafruit_drv2605.Effect, duration: float):
        """Buzz an effect for a specified duration."""
        self._hapController.sequence[0] = effect
        self._hapController.play()
        time.sleep(duration)
        self._hapController.stop()


class BuzzerController:
    """A class to play effects from an effect chain through the correct buzzers."""

    def __init__(self, buzzerLeft: Buzzer, buzzerRight: Buzzer):
        self.buzzerLeft = buzzerLeft
        self.buzzerRight = buzzerRight

    def playEffectOnBuzzer(self, id, effect_duration, buzzer_id):
        """Play an effect on the correct buzzer."""
        if buzzer_id == "L":
            self.buzzerLeft.buzzEffectWithDuration(id, effect_duration)
        else:
            self.buzzerRight.buzzEffectWithDuration(id, effect_duration)

    def playEffectChain(self, effectChain: EffectChain):
        """Play through effects, including pauses, from an EffectChain."""
        # TODO Make effectChain iterable
        for effectNode in effectChain.chain:
            if isinstance(effectNode, PauseNode):
                time.sleep(effectNode.sleep_duration)
            else:
                self.playEffectOnBuzzer(
                    effectNode.effect, effectNode.effect_duration, effectNode.buzzer
                )


class Hapticlock:
    """The Hapticlock class."""

    def __init__(self):
        # SLeep time between event loop repeats
        self.EVENT_LOOP_SLEEP = 1
        # Sleep time between Wi-Fi connection checking
        self.WIFI_CONNECT_SLEEP = 1
        # Timezone offset between UTC and EST
        self.EST_TIMEZONE_OFFSET = -4 * 3600  # UTC-4, in seconds
        # Enable a ime protocol
        self.time_protocol = TimeProtocolHHLeftMMRight()
        # Capacitive touch breakout pin numbers
        self.CAP_TOUCH_LEFT = 0
        self.CAP_TOUCH_RIGHT = 1
        # Capacitive touch GP pins
        self.CAP_TOUCH_BOARD_DATA_GP = board.GP10
        self.CAP_TOUCH_BOARD_CLOCK_GP = board.GP11
        # FSR GP pin
        self.FSR_GP_NUM: int = 26
        # FSR minimum force (u16)
        self.FSR_MIN_FORCE = 40000
        # LSR GP pin
        self.LSR_GP_NUM: int = 27
        # Haptic controllers
        self.HAPTIC_CONTROLLER_LEFT_DATA_GP = board.GP14
        self.HAPTIC_CONTROLLER_LEFT_CLOCK_GP = board.GP15
        self.HAPTIC_CONTROLLER_RIGHT_DATA_GP = board.GP12
        self.HAPTIC_CONTROLLER_RIGHT_CLOCK_GP = board.GP13

        # Initialize sensors and actuators
        self.initializeComponents()
        self.buzzer_controller = BuzzerController(self.buzzerLeft, self.buzzerRight)

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

    def initializeLSR(self):
        """Initialize the light sensitive resistor (LSR), or photoresistor."""
        self.lsr = machine.ADC(self.LSR_GP_NUM)

    def initializeHapticController(self):
        """Initialize the haptic motor controller."""
        self.buzzerLeft = Buzzer(
            self.HAPTIC_CONTROLLER_LEFT_DATA_GP, self.HAPTIC_CONTROLLER_LEFT_CLOCK_GP
        )
        self.buzzerRight = Buzzer(
            self.HAPTIC_CONTROLLER_RIGHT_DATA_GP, self.HAPTIC_CONTROLLER_RIGHT_CLOCK_GP
        )

    def initializeComponents(self):
        """Set up sensor and actuator objects."""
        self.initializeCapacitiveTouch()
        self.initializeHapticController()
        self.initializeFSR()
        self.initializeLSR()

    def getHHMM(self):
        """Return the time in HHMM format, using NTP."""
        unix_time_UTC = ntptime.time()
        unix_time_EST = unix_time_UTC + self.EST_TIMEZONE_OFFSET
        _, _, _, hour, minute, _, _, _ = ntptime.utime.localtime(unix_time_EST)
        # return hour, minute

    def buzzTime(self):
        """Buzz the time to the user."""
        HH, MM = self.getHHMM()
        print(f"Buzzing time:  {HH}:{MM}")
        effectChain = self.time_protocol.generateEffectChain(HH, MM)
        self.buzzer_controller.playEffectChain(effectChain)

    def checkForceEvents(self):
        """Check for FSR events.

        Currently just checks if force > MIN_FORCE."""
        forceU16 = self.fsr.read_u16()
        if forceU16 > self.FSR_MIN_FORCE:
            print("Force detected. Entering configuration mode (not yet implemented.)")

    def recordLightLevels(self):
        """Record light levels."""
        lightU16 = self.lsr.read_u16()
        print(lightU16)

    def checkCapacitiveEvents(self):
        """Check for capacitive touch events."""
        if self.capLeft.value and self.capRight.value:
            print("Both capacitive sensors touched.")
            self.buzzTime()

    def connectWifi(self):
        """Connect to WiFi."""
        # Check if already connected
        wlan = network.WLAN(network.STA_IF)
        if not wlan.isconnected():
            ssid = "PC-380"
            with open("pc380.password", "r") as passfile:
                password = passfile.read().strip()

            wlan = network.WLAN(network.STA_IF)
            wlan.active(True)
            wlan.connect(ssid, password)

            while not wlan.isconnected():
                print(f"Connecting to Wi-Fi: '{ssid}'...")
                time.sleep(self.WIFI_CONNECT_SLEEP)
            print(f"Connected to Wi-Fi: '{ssid}'.")
        else:
            print(f"Already connected to Wi-Fi.")

    def run(self):
        # """The Hapticlock event loop."""
        # print("Entering event loop.")
        self.connectWifi()

        # max_runs = 5
        # runs = 0
        # while runs < max_runs:
        while True:
            gc.collect()

            self.recordLightLevels()

            # Check FSR
            self.checkForceEvents()

            # Check cap touch
            self.checkCapacitiveEvents()

            # Sleep
            time.sleep(self.EVENT_LOOP_SLEEP)
            # runs += 1


if __name__ == "__main__":
    # pass
    hapticlock = Hapticlock()
    hapticlock.run()
