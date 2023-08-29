import socket
import struct
from threading import Thread

class SocketConnection(Thread):

	@staticmethod
	def parse_list(input_list):
		half = (len(input_list) + 1) // 2
		channel_1 = zip(input_list[:half:2], input_list[1:half:2])
		channel_2 = zip(input_list[half::2], input_list[half + 1::2])
		return channel_1, channel_2

	def __init__(self, channel_1_samples, channel_2_samples, address=None, port=5005):
		Thread.__init__(self)
		self.channel_1_samples	= channel_1_samples
		self.channel_2_samples	= channel_2_samples
		self.address			= address
		self.port				= port
		self.connection			= None
		self.running			= False

		self.connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.connection.bind(("0.0.0.0", 8182))
		self.connection.sendto("--register", (self.address, int(self.port)))

	def start(self):
		self.running = True
		Thread.start(self)

	def shutdown(self):
		self.running = False
		self.connection.close()

	def run(self):
		print "starting up the socket listener"
		while self.running:
			self.read(numBytes=100)
		print "shutting down the socket listener"
		self.shutdown()

	def read(self, numBytes=0):
		numElements = numBytes * 4
		data = self.connection.recv(numElements * 4)
		try:
			unpackedData = (struct.unpack_from('I' * numElements, data))
			if len(unpackedData) == numElements:
				(channel_1_samples, channel_2_samples) = self.parse_list(unpackedData)
				self.channel_1_samples.extend(channel_1_samples)
				self.channel_2_samples.extend(channel_2_samples)
			else:
				print "incorrect size datagram received"
		except Exception as e:
			print "error reading from socket", e

