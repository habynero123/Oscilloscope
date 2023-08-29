import time
import serial
from threading import Thread

SERIAL_BAUD	= 19200

class SerialConnection(Thread):

	@staticmethod
	def parse_list(input_list):
		half = (len(input_list) + 1) // 2
		channel_1 = zip(input_list[:half:2], input_list[1:half:2])
		channel_2 = zip(input_list[half::2], input_list[half + 1::2])
		return channel_1, channel_2

	def __init__(self, channel_1_samples, channel_2_samples, port):
		Thread.__init__(self)
		self.channel_1_samples	= channel_1_samples
		self.channel_2_samples	= channel_2_samples
		self.port				= port
		self.connection			= None
		self.running			= False

		# Open BP serial device:
		self.connection = serial.Serial(port=port, baudrate=SERIAL_BAUD)
		self.connection.close()
		self.connection.open()

		# Enter binary scripting mode:
		self.connection.write('\n\n')
		time.sleep(0.1)
		self.connection.write(''.join(['\x00' for i in range(20)]))
		time.sleep(0.1)

		# Start continuous voltage measurement mode:
		self.connection.flushInput()
		self.connection.write('\x15')
		time.sleep(0.1)

	def start(self):
		self.running = True
		Thread.start(self)

	def shutdown(self):
		self.running = False
		self.connection.close()

	def run(self):
		print("starting up the socket listener")
		while self.running:
			self.read(numBytes=100)
		print("shutting down the socket listener")
		self.shutdown()

	def read(self, numBytes=0):
		self.channel_1_samples.append(self.connection.read(numBytes))
