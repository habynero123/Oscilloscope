import socket
import struct
import json
from threading import Thread

class SocketConnection(Thread):

	# @staticmethod
	# def parse_list(input_list):
	# 	half = (len(input_list) + 1) // 2
	# 	channel_1 = zip(input_list[:half:2], input_list[1:half:2])
	# 	channel_2 = zip(input_list[half::2], input_list[half + 1::2])
	# 	return channel_1, channel_2
	#

	@staticmethod
	def parse_list(input_list):
		channel_1 = zip(input_list[::2], input_list[1::2])
		return channel_1

	def __init__(self, channel_1_samples, channel_2_samples, window_size, address=None, port=5005):
		Thread.__init__(self)
		self.window_size		= window_size
		self.channel_1_samples	= channel_1_samples
		self.channel_2_samples	= channel_2_samples
		self.address			= address
		self.port				= port
		self.running			= False
		self.num_samples		= 0
		self.num_packets		= 0
		self.tx_socket = None
		self.rx_socket = None



	def start(self):
		self.running = True
		Thread.start(self)

	def shutdown(self):
		try:
			self.tx_socket.sendto("shutdown", (self.address, int(self.port)))
		except Exception as e:
			pass
		self.running = False
		self.rx_socket.close()
		self.tx_socket.close()

	def init_adc(self):
		self.tx_socket.sendto("register", (self.address, int(self.port)))
		self.tx_socket.sendto("size={window_size}".format(window_size=self.window_size), (self.address, int(self.port)))
		self.tx_socket.sendto("method with_dt", (self.address, int(self.port)))
		# self.tx_socket.sendto("method raw", (self.address, int(self.port)))
		self.tx_socket.sendto("channels 1", (self.address, int(self.port)))
		self.tx_socket.sendto("start", (self.address, int(self.port)))
		print "size={window_size}".format(window_size=self.window_size), (self.address, int(self.port))

	def run(self):
		print "starting up the socket listener"
		self.tx_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		self.rx_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		self.init_adc()
		#self.rx_socket.settimeout(1)
		self.rx_socket.bind(("0.0.0.0", 8182))
		self.rx_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 112640)
		while self.running:
			self.read(numBytes=40960)
			#print len(self.channel_1_samples), self.num_samples
		print "shutting down the socket listener"
		self.shutdown()

	def read(self, numBytes=0):
		# numElements = numBytes
		# data = self.sock.recv(numElements * 4)
		# try:
		# 	unpackedData = (struct.unpack_from('I' * numElements, data))
		# 	if len(unpackedData) == numElements:
		# 		# (channel_1_samples, channel_2_samples) = self.parse_list(unpackedData)
		# 		self.channel_1_samples.extend(unpackedData)
		# 		# self.channel_2_samples.extend(channel_2_samples)
		# 	else:
		# 		print "incorrect size datagram received"
		# except Exception as e:
		# 	print "error reading from socket", e

		#====================================================#
		# THIS IS THE FORMAT OF THE MESSAGE WE ARE RECEIVING #
		# '(1, 0.0), (1, 0.0), (1, 0.0),
		#====================================================#
		data = self.rx_socket.recv(numBytes)
		self.num_packets += 1
		# print data
		json_obj = json.loads(data)
		#if self.num_packets % 100 == 0:
			#print json_obj["data"]
		try:
			for sample in json_obj["data"]:
				sample = eval(sample)
				if sample:
					# print sample, sample[0], type(sample[0])
					if sample[0] == 1:
						self.num_samples += 1
						self.channel_1_samples.put((float(sample[1]), sample[2]))
						#self.channel_1_samples.put(float(sample[1]))
					elif sample[0] == 2:
						self.channel_2_samples.put(float(sample[1]))
					else:
						continue
						#print "oh no!", element
		except Exception as e:
			print e
