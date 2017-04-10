from picamera import PiCamera 
import RPi.GPIO as GPIO
import time
import datetime
from threading import Thread
import os
import uuid
import json

from picamera.array import PiRGBArray
from picamera import PiCamera
import cv2
import numpy as np

STREL = 5

FLIP_STARTED = 3
FLIP_OK = 5
FLIP_INVALID = 7
SCANNING = 11

ALL_PINS = [FLIP_STARTED, FLIP_INVALID, FLIP_OK, SCANNING]

class FlipDetector(Thread):
	__instance = None

	@classmethod
	def get_instance(cls):
		if cls.__instance is None:
			cls.__instance = FlipDetector()
		return cls.__instance

	def __init__(self):
		Thread.__init__(self)
		self.enabled = True

	def run(self):
		print('Running flip detector')
		while True:	
			if not self.enabled:
				time.sleep(1)		
				continue

			buf = []
			quiet_counter = 0
			flip_detected = False

			scanner = Scanner.get_instance()
			scanner.raw_capture.truncate(0)
			camera = scanner.camera
			camera.resolution = (320, 240)

			for frame in camera.capture_continuous(scanner.raw_capture, format='bgr', use_video_port=True):
				if not self.enabled:
					break

				frame = scanner.raw_capture.array
				gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
				gray1 = cv2.GaussianBlur(gray, (STREL, STREL), 0)

				left1 = gray1[:120, :160]
				right1 = gray1[:120, 160:]

				# time.sleep(.1)
				scanner.raw_capture.truncate(0)

				camera.capture(scanner.raw_capture, 'rgb')
				frame = scanner.raw_capture.array
				gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
				gray2 = cv2.GaussianBlur(gray, (STREL, STREL), 0)

				left2 = gray2[:120, :160]
				right2 = gray2[:120, 160:]

				scanner.raw_capture.truncate(0)

				delta_left = cv2.absdiff(left1, left2)
				delta_right = cv2.absdiff(right1, right2)

				_, thresh_left = cv2.threshold(delta_left, 25, 255,
				    cv2.THRESH_BINARY)
				_, thresh_right = cv2.threshold(delta_right, 25, 255,
				    cv2.THRESH_BINARY)

				ratio = ( cv2.countNonZero(thresh_left) - cv2.countNonZero(thresh_right) ) / (160*120)
				if abs(ratio) > 0.01:
					Scanner.get_instance().set_pin_status(FLIP_STARTED)
					# print(ratio)

					buf.append(ratio)
					quiet_counter = 0
				else:
					quiet_counter += 1

					# Reset pins if we waited too long
					if quiet_counter > 3 and len(buf) == 0:
						Scanner.get_instance().set_pin_status(FLIP_STARTED, False)
						continue

					# Listen for pause
					if quiet_counter < 3 or len(buf) == 0:
						continue

					# If we detected pause, but action was too fast, start over
					neg = [item for item in buf if item < 0]
					pos = [item for item in buf if item > 0]
					if len(neg) == 0 or len(pos) == 0:							
						print('Action too fast, flip page back again')
						Scanner.get_instance().set_pin_status(FLIP_INVALID)
						buf = []
						quiet_counter = 0
						continue

					# If we started with neg gradient & ended +ve, then we have a fwd page flip, else rev
					if buf[0] < 0 and buf[-1] > 0:							
						flip_detected = True			
						Scanner.get_instance().set_pin_status(FLIP_OK)		
						print('Fwd page flip')
						break							
					elif buf[0] > 0 and buf[-1] < 0:
						Scanner.get_instance().set_pin_status(FLIP_INVALID)
						print('Rev page flip')
					else:
						Scanner.get_instance().set_pin_status(FLIP_INVALID)
						print('Invalid page flip')							

					buf = []
					quiet_counter = 0

			if flip_detected:
				flip_detected = False
				print('Capturing image')
				scanfile, pgno = Scanner.get_instance().scan()
				imgloc = os.path.join('../imgs/', scanfile)
				Scanner.get_instance().send_msg({'text': json.dumps({'loc': imgloc, 'scanNum': pgno})})


class ScanModes(object):
	NONE = 0
	SINGLE_SCAN = 1
	AUTO_SCAN = 2
	TEST = 3


class Scanner(object):

	__instance = None

	def __init__(self):
		GPIO.setmode(GPIO.BOARD)
		self.camera = PiCamera()
		time.sleep(2)
		self.raw_capture = PiRGBArray(self.camera)		
		self.img_dir = '/var/www/html/imgs'
		self.pgno = 0
		self.started = False
		self.currbookid = -1
		self.currbook = None
		self.msg_channel = None
		self.tmpdir = '/var/www/html/test'
		self.__mode = ScanModes.TEST

		for pin in ALL_PINS:
			GPIO.setup(pin, GPIO.OUT)
			GPIO.output(pin, GPIO.LOW)	
		
	@classmethod
	def get_instance(cls):
		if cls.__instance is None:
			cls.__instance = Scanner()
		return cls.__instance

	def __str__(self):
		return str(self.__dict__)  

	def scan(self):
		self.set_pin_status(SCANNING)
		if self.__mode != ScanModes.TEST:
			self.pgno += 1 

			self.raw_capture.truncate(0)
			self.camera.resolution = (3200,2400)
			scanfile = '%d/%d.jpg' % (self.currbookid, self.pgno)

			self.camera.capture(self.raw_capture, 'bgr')
			cv2.imwrite(os.path.join(self.img_dir, str(self.currbookid), str(self.pgno) + '_orig.jpg') ,self.raw_capture.array)
			# self.camera.capture(os.path.join(self.img_dir, scanfile), format='jpeg', quality=100)

			img = self.process_img(self.raw_capture.array)
			cv2.imwrite(os.path.join(self.img_dir, scanfile),img)

		else:
			randid = uuid.uuid4()
			self.raw_capture.truncate(0)
			self.camera.resolution = (640, 480)
			scanfile = '%s.jpg' % (randid)
			self.camera.capture(self.raw_capture, 'bgr')
			cv2.imwrite(os.path.join(self.tmpdir, scanfile) ,self.raw_capture.array)			

		self.set_pin_status(SCANNING, False)
		return scanfile, self.pgno
		

	def process_img(self, scan):
		# img = scan
		img = np.copy(scan)
		img = np.array(img[::16, ::16, :])
		gray = cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)

		thresh_val, thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
		
		length = len(thresh)
		width = len(thresh[0])

		proj = np.sum(thresh, 0)/ ( length * 255)
		above_thr = [i for i in range(width) if proj[i] > 0.2]
		ymin = np.min(above_thr)
		ymax = np.max(above_thr)

		proj = np.sum(thresh, 1) / (width * 255)
		above_thr = [i for i in range(length) if proj[i] > 0.2]
		xmin = np.min(above_thr)
		xmax = np.max(above_thr)

		return scan[xmin*16:xmax*16, ymin*16:ymax*16, :]

	def send_msg(self, msg):
		if self.msg_channel:
			self.msg_channel.send(msg)

	@property
	def mode(self):
		return self.__mode

	@mode.setter
	def mode(self, mode):
		self.__mode = mode		
		FlipDetector.get_instance().enabled = True if mode == ScanModes.AUTO_SCAN else False

		if self.__mode == ScanModes.AUTO_SCAN:
			if not FlipDetector.get_instance().is_alive():
				FlipDetector.get_instance().start()

	def set_pin_status(self, out_pin, out_val=True):
		all_status = { pin: (out_pin == pin) & out_val for pin in ALL_PINS }
		for pin in ALL_PINS:
			GPIO.output(pin, all_status[pin])

if __name__ == '__main__':
	scanner = Scanner.get_instance()
	# RAW_CAPTURE = PiRGBArray(scanner.camera)

	scanner.mode = ScanModes.AUTO_SCAN
	time.sleep(10)
	scanner.mode = ScanModes.NONE