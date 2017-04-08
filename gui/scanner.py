from picamera import PiCamera 
import RPi.GPIO as GPIO
import time
import datetime
from threading import Thread
import os
import uuid

from picamera.array import PiRGBArray
from picamera import PiCamera
import cv2

STREL = 5

class FlipDetector(Thread):
	__instance = None

	TRIG = 7
	ECHO = 11

	@classmethod
	def get_instance(cls):
		if cls.__instance is None:
			cls.__instance = FlipDetector()
		return cls.__instance

	def __init__(self):
		Thread.__init__(self)
		GPIO.setmode(GPIO.BOARD)


		GPIO.setup(FlipDetector.TRIG, GPIO.OUT)
		GPIO.output(FlipDetector.TRIG, GPIO.LOW)

		GPIO.setup(FlipDetector.ECHO, GPIO.IN)

		time.sleep(0.1)

		self.enabled = True
		self.rawCapture = PiRGBArray(Scanner.get_instance().camera)

	def run(self):
		while True:
			if self.enabled:
				buf = []
				quiet_counter = 0
				flip_detected = False

				camera = Scanner.get_instance().camera
				camera.resolution = (320, 240)

				for frame in camera.capture_continuous(self.rawCapture, format='rgb', use_video_port=True):
					frame = self.rawCapture.array
					gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
					gray1 = cv2.GaussianBlur(gray, (STREL, STREL), 0)

					left1 = gray1[:120, :160]
					right1 = gray1[:120, 160:]

					# time.sleep(.1)
					self.rawCapture.truncate(0)

					camera.capture(self.rawCapture, 'rgb')
					frame = self.rawCapture.array
					gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
					gray2 = cv2.GaussianBlur(gray, (STREL, STREL), 0)

					left2 = gray2[:120, :160]
					right2 = gray2[:120, 160:]

					self.rawCapture.truncate(0)

					delta_left = cv2.absdiff(left1, left2)
					delta_right = cv2.absdiff(right1, right2)

					_, thresh_left = cv2.threshold(delta_left, 25, 255,
					    cv2.THRESH_BINARY)
					_, thresh_right = cv2.threshold(delta_right, 25, 255,
					    cv2.THRESH_BINARY)

					ratio = ( cv2.countNonZero(thresh_left) - cv2.countNonZero(thresh_right) ) / (160*120)
					if abs(ratio) > 0.01:						
						print(ratio)

						buf.append(ratio)
						quiet_counter = 0
					else:
						quiet_counter += 1

						# Listen for pause
						if quiet_counter < 3 or len(buf) == 0:
							continue

						# If we detected pause, but action was too fast, start over
						neg = [item for item in buf if item < 0]
						pos = [item for item in buf if item > 0]
						if len(neg) == 0 or len(pos) == 0:
							print('Action too fast, flip page back again')
							buf = []
							quiet_counter = 0
							continue

						# If we started with neg gradient & ended +ve, then we have a fwd page flip, else rev
						if buf[0] < 0 and buf[-1] > 0:
							flip_detected = True						
							print('Fwd page flip')
							break							
						elif buf[0] > 0 and buf[-1] < 0:
							print('Rev page flip')
						buf = []
						quiet_counter = 0

				if flip_detected:
					flip_detected = False
					print('Capturing image')
					scanfile, pgno = Scanner.get_instance().scan()
					imgloc = os.path.join('../imgs/', scanfile)
					Scanner.get_instance().send_msg({'loc': imgloc, 'scanNum': pgno})


class ScanModes(object):
	NONE = 0
	SINGLE_SCAN = 1
	AUTO_SCAN = 2
	TEST = 3


class Scanner(object):

	__instance = None

	def __init__(self):
		self.camera = PiCamera()
		time.sleep(2)
		self.img_dir = '/var/www/html/imgs'
		self.pgno = 0
		self.started = False
		self.currbookid = -1
		self.currbook = None
		self.msg_channel = None
		self.tmpdir = '/var/www/html/test'
		self.mode = ScanModes.TEST
		
	@classmethod
	def get_instance(cls):
		if cls.__instance is None:
			cls.__instance = Scanner()
		return cls.__instance

	def __str__(self):
		return str(self.__dict__)  

	def scan(self):
		if self.mode != ScanModes.TEST:
			self.pgno += 1 
			self.camera.resolution = (3280,2464)
			scanfile = '%d/%d.jpg' % (self.currbookid, self.pgno)
			self.camera.capture(os.path.join(self.img_dir, scanfile), format='jpeg', quality=100)
			return scanfile, self.pgno
		else:
			randid = uuid.uuid4()
			self.camera.resolution = (640, 480)
			scanfile = '%s.jpg' % (randid)
			self.camera.capture(os.path.join(self.tmpdir, scanfile), format='jpeg')
			return scanfile, None

	def send_msg(self, msg):
		if self.msg_channel:
			self.msg_channel.send(msg)

	def set_mode(self, mode):
		self.mode = mode		
		FlipDetector.get_instance().enabled = True if mode == ScanModes.AUTO_SCAN else False

		if self.mode == ScanModes.AUTO_SCAN:
			if not FlipDetector.get_instance().is_alive():
				FlipDetector.get_instance().start()

if __name__ == '__main__':
	scanner = Scanner.get_instance()
	scanner.set_mode(ScanModes.AUTO_SCAN)
