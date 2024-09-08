#!/usr/bin/env python3


# import adafruit_mpr121
import adafruit_drv2605
import board
import busio
import gc
import machine
import network
import ntptime
import time

# EffectChainType = list[tuple[int, float, float, str]]


class EffectNode:
    """
    An adafruit_drv2605.Effect with duration, sleep duration, and buzzer.
    """

    def __init__(self, effect_id, effect_duration, sleep_duration, buzzer):
        self.effect_id = effect_id
        self.effect_duration: float = effect_duration
        self.sleep_duration: float = sleep_duration
        self.buzzer: str = buzzer


class PauseNode(EffectNode):
    """An empty class for representing Pauses."""

    def __init__(self, pause_time=1):
        """Dummy constructor for a Pause."""
        super().__init__(-1, 0, pause_time, "")


class EffectChain:
    """A list of EffectNodes."""

    def __init__(self):
        """Initialize chain as an empty list."""
        self.chain: list[EffectNode] = []

    def addNodeFromConfig(self, effect_id, effect_duration, sleep_duration, buzzer):
        """Build and append an EffectNode to the chain from config data."""
        self.chain.append(
            EffectNode(effect_id, effect_duration, sleep_duration, buzzer)
        )

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

    # def __init__(self):
    #     pass

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
        # Map time thresholds to effects
        # TODO Use Effects instead of IDs, and append effects
        self.timeThresholdEffectMap = {"12hr": 10, "1hr": 1, "30min": 10, "5min": 7}

    def _generateHoursEffectChain(self, HH: int):
        """Return a list of EffectNodes for the buzzer to play to transmit HH."""
        hoursChain = []
        # Add effects to signify 12 hours.
        if HH >= 12:
            id = self.timeThresholdEffectMap["12hr"]
            effect_duration = 0.5
            sleep_duration = 0.5
            hoursChain.append(EffectNode(id, effect_duration, sleep_duration, "L"))
            # hoursChain.append((id, effect_duration, sleep_duration, "L"))
            # Decrement time for the next hours iteration
            HH -= 12
        # Add effects for the remaining hours
        for _ in range(0, HH):
            id = self.timeThresholdEffectMap["1hr"]
            effect_duration = 0.65
            sleep_duration = 0.2
            hoursChain.append(EffectNode(id, effect_duration, sleep_duration, "L"))
            # hoursChain.append((id, effect_duration, sleep_duration, "L"))
        return hoursChain

    def _generateMinutesEffectChain(self, MM: int):
        """Return a list of Effects for the buzzer to play to transmit MM."""
        minutesChain = []
        # Add effects to signify 12 hours.
        if MM >= 30:
            id = self.timeThresholdEffectMap["30min"]  # soft bump for 30 minutes
            effect_duration = 0.5
            sleep_duration = 0.4
            minutesChain.append(EffectNode(id, effect_duration, sleep_duration, "R"))
            # minutesChain.append((id, effect_duration, sleep_duration, "R"))
            # Decrement time for the next hours iteration
            MM -= 30
        # Add effects for the remaining hours
        for _ in range(0, MM // 5):
            id = self.timeThresholdEffectMap["5min"]  # sharp click for 5 minutes
            effect_duration = 0.5
            sleep_duration = 0.2
            minutesChain.append(EffectNode(id, effect_duration, sleep_duration, "R"))
            # minutesChain.append((id, effect_duration, sleep_duration, "R"))
        return minutesChain

    def generateEffectChain(self, HH, MM):
        """Return an EffectChain for HHMM."""
        effectChain = EffectChain()
        effectChain.addNodesFromList(self._generateHoursEffectChain(HH))
        effectChain.addPause(self.HHMMseparation)
        effectChain.addNodesFromList(self._generateMinutesEffectChain(MM))
        return effectChain


class BuzzerController:
    """A class to play effects from an effect chain through the correct buzzers."""

    def __init__(self, buzzerLeft: Buzzer, buzzerRight: Buzzer):
        self.buzzerLeft = buzzerLeft
        self.buzzerRight = buzzerRight

    def playEffectChain(self, effectChain: EffectChain):
        """Play effects from a chain.
        Buzz a chain of effects with pauses in between.

        effectChain is a list of tuples (effect_id, effect_duration, sleep_duration, buzzer_id)
        """
        for effectNode in effectChain.chain:
            # Sleep between effects if effect id is -1
            if isinstance(effectNode, PauseNode):
                time.sleep(effectNode.sleep_duration)
            else:
                self.playEffectOnBuzzer(
                    effectNode.effect_id, effectNode.effect_duration, effectNode.buzzer
                )

    def playEffectOnBuzzer(self, id, effect_duration, buzzer_id):
        """Play an effect on the correct buzzer."""
        if buzzer_id == "L":
            self.buzzerLeft.buzzEffectWithDuration(id, effect_duration)
        else:
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
        self.WIFI_CONNECT_SLEEP = 1
        self.EST_TIMEZONE_OFFSET = -4 * 3600  # UTC-4, in seconds
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
        self.initializeComponents()
        # self.rtc = DS3231()
        # self.buzzerLeft = []
        self.buzzer_controller = BuzzerController(self.buzzerLeft, self.buzzerRight)

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
        # _, _, _, _, hour, minute, _ = self.rtc.DS3231_ReadTime(mode=1)
        # year, month, mday, hour, minute, second, weekday, yearday
        unix_time_UTC = ntptime.time()
        unix_time_EST = unix_time_UTC + self.EST_TIMEZONE_OFFSET
        _, _, _, hour, minute, _, _, _ = ntptime.utime.localtime(unix_time_EST)
        return hour, minute

    # def buzzAlert(self):
    #     """Buzz a sequence to alert the user."""
    #     pass

    def buzzTime(self):
        """Buzz the time to the user."""
        HH, MM = self.getHHMM()
        print(f"Buzzing time:  {HH}:{MM}")
        effectChain = self.time_protocol.generateEffectChain(HH, MM)
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

    def connectWifi(self):
        """Connect to WiFi."""
        # Check if already connected
        wlan = network.WLAN(network.STA_IF)
        if not wlan.isconnected():
            ssid = "vscode"
            with open("vscode.password", "r") as passfile:
                password = passfile.read().strip()

            wlan = network.WLAN(network.STA_IF)
            wlan.active(True)
            wlan.connect(ssid, password)

            while not wlan.isconnected():
                print("Connecting to Wi-Fi: '{ssid}'...")
                time.sleep(self.WIFI_CONNECT_SLEEP)
                print(f"Connected to Wi-Fi: '{ssid}'.")
        else:
            print(f"Already connected to Wi-Fi.")

    def run(self):
        """The Hapticlock event loop."""
        # print("Entering event loop.")
        self.connectWifi()

        max_runs = 5
        runs = 0
        while runs < max_runs:
            gc.collect()
            self.buzzTime()

            # Check FSR
            # self.checkForceEvents()

            # Check cap touch
            # self.checkCapacitiveEvents()

            # Sleep
            time.sleep(self.EVENT_LOOP_SLEEP)
            runs += 1


if __name__ == "__main__":
    # pass
    hapticlock = Hapticlock()
    hapticlock.run()
