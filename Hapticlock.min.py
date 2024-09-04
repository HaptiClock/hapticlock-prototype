#!/usr/bin/env python3
import adafruit_mpr121,adafruit_drv2605,board,busio,machine,time
class Hapticlock:
	'The Hapticlock class.'
	def __init__(A):A.EVENT_LOOP_SLEEP=.1;A.CAP_TOUCH_LEFT=0;A.CAP_TOUCH_RIGHT=1;A.CAP_TOUCH_BOARD_DATA_GP=board.GP16;A.CAP_TOUCH_BOARD_CLOCK_GP=board.GP17;A.HAPTIC_CONTROLLER_DATA_GP=board.GP18;A.HAPTIC_CONTROLLER_CLOCK_GP=board.GP19;A.FSR_GP_NUM=26;A.FSR_MIN_FORCE=40000
	def initializeCapacitiveTouch(A):'Initialize the capacitive touch breakout board.';C=busio.I2C(A.CAP_TOUCH_BOARD_CLOCK_GP,A.CAP_TOUCH_BOARD_DATA_GP);B=adafruit_mpr121.MPR121(C);A.capLeft=B[A.CAP_TOUCH_LEFT];A.capRight=B[A.CAP_TOUCH_RIGHT]
	def initializeFSR(A):'Initialize the force sensor resistor (FSR).';A.fsr=machine.ADC(A.FSR_GP_NUM)
	def initializeHapticController(A):'Initialize the haptic motor controller.';B=busio.I2C(A.HAPTIC_CONTROLLER_CLOCK_GP,A.HAPTIC_CONTROLLER_DATA_GP);A.hapController=adafruit_drv2605.DRV2605(B)
	def initializeComponents(A):'Set up sensor and actuator objects.';A.initializeCapacitiveTouch();A.initializeHapticController();A.initializeFSR()
	def playAllHapticControllerEffects(B):
		'Play through all 123 haptic controller effects.';C=1;A=1
		while True:
			print(f"Playing effect #{A}");B.hapController.sequence[0]=adafruit_drv2605.Effect(A);B.hapController.play();time.sleep(C);B.hapController.stop();A+=1
			if A>123:A=1
	def checkForceEvents(A):
		'Check for FSR events.\n\n        Currently just checks if force > MIN_FORCE.';B=A.fsr.read_u16()
		if B>A.FSR_MIN_FORCE:print('Force detected. Entering configuration mode (not yet implemented.)')
	def checkCapacitiveEvents(A):
		'Check for capacitive touch events.'
		if A.capLeft.value and A.capRight.value:print('Both capacitive sensors touched.')
	def run(A):'The Hapticlock event loop.';A.initializeComponents();print('Entering event loop.');A.playAllHapticControllerEffects()
if __name__=='__main__':hapticlock=Hapticlock();hapticlock.run()