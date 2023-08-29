import time
import numpy as np
from threading import Thread
#from collections import deque
from multiprocessing import Process, Queue
from socket_connection import SocketConnection
try:
	from serial_connection import SerialConnection
except ImportError:
	print("Serial Connection is unavailable")

CONN_SERIAL		= 0
CONN_SOCKET		= 1

SYNC_NONE		= 0
SYNC_RISE		= 1
SYNC_FALL		= 2

MODE_CONTINUOUS	= 0
MODE_ONESHOT	= 1

MIN_VOLTAGE		= 0.0
MAX_VOLTAGE		= 6.0
BASE_RATE		= 21720 	# Hz

class Oscilloscope(object):
	def __init__(self, instruction_queue, channel_1_queue, channel_1_dt_queue, channel_2_queue, channel_2_dt_queue, debug=False):
		# port, points_per_graph, rate, mode, sync, trigger_voltage, phase_offset):
		# Thread.__init__(self)

		self.debug 				= debug
		self.instruction_queue	= instruction_queue
		self.channel_1_queue	= channel_1_queue
		self.channel_2_queue	= channel_2_queue
		self.channel_1_dt_queue	= channel_1_dt_queue
		self.channel_2_dt_queue	= channel_2_dt_queue

		self.channel_1_samples	= Queue()
		self.channel_2_samples	= Queue()
		self.paused				= True
		self.running			= False
		self.port				= False
		self.mode				= False
		self.sync				= False
		self.trigger_voltage	= False
		self.rate				= False
		self.points_per_graph	= False
		self.phase_offset		= False
		self.connection			= None
		self.total_num_samples	= 0
		self.last_time			= 0
		self.sample_duration 	= 1

	def pause(self):
		self.paused = True

	def unpause(self):
		self.paused = False
		if not self.connection:
			self.start_connection()

	def set_points_per_graph(self, points):
		self.points_per_graph = points
		#self.channel_1_data 	= -10 * np.ones(points)
		#self.channel_2_data 	= -10 * np.ones(points)
		#self.channel_1_dt 		= np.zeros(points)
		#self.channel_2_dt 		= np.zeros(points)

	def shutdown(self):
		self.running = False
		self.connection.shutdown()
		print("NUMBER OF SAMPLES:{0}".format(self.total_num_samples))

	def process_message(self, message):
		print("Oscilloscope received message: {message}".format(message=message))
		if message[0] == "shutdown":
			self.shutdown()
		elif message[0] == "stop":
			self.stop()
		elif message[0] == "start":
			self.start()
		elif message[0] == "pause":
			self.pause()
		elif message[0] == "unpause":
			self.unpause()
		elif message[0] == "start_connection":
			self.start_connection()
		elif message[0] == "port":
			self.port = message[1]
		elif message[0] == "mode":
			self.mode = message[1]
		elif message[0] == "sync":
			self.sync = message[1]
		elif message[0] == "trigger_voltage":
			self.trigger_voltage = message[1]
		elif message[0] == "rate":
			self.rate = message[1]
		elif message[0] == "points_per_graph":
			self.points_per_graph = message[1]
		elif message[0] == "phase_offset":
			self.phase_offset = message[1]
		else:
			print("Oscilloscope received unknown message: {message}".format(message=message[0]))

	def pop_queue(self, queue):
		try:
			return queue.get_nowait()
		except Exception as e:
			return  False

	def start_connection(self):
		if self.port :
			if ":" in self.port:
				parts = self.port.split(":")
				self.connection = SocketConnection(
					channel_1_samples=self.channel_1_samples,
					channel_2_samples=self.channel_2_samples,
					window_size=self.points_per_graph,
					address=parts[0],
					port=parts[1])
			else:
				self.connection = SerialConnection(
					channel_1_samples=self.channel_1_samples,
					channel_2_samples=self.channel_2_samples,
					port=self.port)
			self.connection.start()

	def start(self):
		self.running = True
		self.run()
		# Thread.start(self)

	def run(self):
		while self.running:
			# print "loop time:", time.time() - self.last_time
			if not self.instruction_queue.empty():
				message = self.pop_queue(self.instruction_queue)
				self.process_message(message)
				continue

			if self.paused:
				time.sleep(.1)
				continue

			self.last_time = time.time()
			if self.debug:
				# Artificial waveforms for debugging FFT code
				bpf = BASE_RATE / self.rate
				t	= np.linspace(0, float(self.points_per_graph / bpf), self.points_per_graph)

				# Sine wave frequency test:
				self.channel_1_data = 1. + np.sin(2 * np.pi * BASE_RATE / 10. * t)

				# Square wave frequency test:
				# self.channel_1_data = 5.*(((t/(27.0/self.BaseRate))%1.0)>0.5)
				continue

			if self.mode == MODE_ONESHOT:
				self.sample()
				self.pause()
				continue

			if self.mode == MODE_CONTINUOUS:
				# if len(self.channel_1_data) != self.points_per_graph:
				# 	self.channel_1_data = -10 * np.ones(self.points_per_graph)
				self.sample()

		self.shutdown()

	def trigger_check(self, cur_voltage, prev_voltage):
		#print self.sync, cur_voltage, prev_voltage, self.trigger_voltage
		if self.sync == SYNC_RISE:
			return (cur_voltage >= self.trigger_voltage) and (prev_voltage < self.trigger_voltage)
		return (cur_voltage <= self.trigger_voltage) and (prev_voltage > self.trigger_voltage)

	# Provide correct initialisation for lastV:
	def trigger_init(self):
		# print"TRIGGER INIT"
		if self.sync == SYNC_RISE:
			return MAX_VOLTAGE
		return MIN_VOLTAGE

	# Acquire full window of data:
	def sample(self):
		if self.channel_1_samples.qsize() > self.points_per_graph:
			if self.sync != SYNC_NONE:
				phase_offset_pos	= max(self.phase_offset * self.points_per_graph / 100, 0)
				phase_offset_neg	= -min(self.phase_offset * self.points_per_graph / 100, 0)
				vbuffer				= np.zeros(phase_offset_neg)

				# Pad out buffer to account for negative phase offset:
				for i in range(phase_offset_neg):
					channel_1_sample = self.channel_1_samples.get()
					self.total_num_samples += 1
					cur_voltage = channel_1_sample[0]
					#__, __ = self.sample_voltage(self.channel_2_samples)
					vbuffer 	= np.roll(vbuffer, 1)
					vbuffer[0]	= cur_voltage

				# Wait for trigger condition:
				prev_voltage = self.trigger_init()

				while True:
					channel_1_sample = self.channel_1_samples.get()
					self.total_num_samples += 1
					cur_voltage = channel_1_sample[0]
					#__, __ = self.sample_voltage(self.channel_2_samples)
					if phase_offset_neg:
						vbuffer 	= np.roll(vbuffer, 1)
						vbuffer[0] 	= cur_voltage
					if self.trigger_check(cur_voltage, prev_voltage) or self.sync == SYNC_NONE:
						break
					prev_voltage = cur_voltage
					if not self.running:
						return

				# Adjust to account for positive phase offset:
				for i in range(phase_offset_pos):
					self.channel_1_samples.get()
					self.total_num_samples += 1
					# self.sample_voltage(self.channel_2_samples)
					if not self.running:
						return

				# Add negative-offset data:
				self.channel_1_data[0:phase_offset_neg] = vbuffer[phase_offset_neg - 1::- 1]
				# self.channel_2_data[0:phase_offset_neg] = vbuffer[phase_offset_neg - 1::- 1]

				# Acquire data to fill remainder of buffer:

				for __ in range(phase_offset_neg, self.points_per_graph):
					channel_1_sample = self.channel_1_samples.get()
					self.total_num_samples += 1
					self.channel_1_queue.put(channel_1_sample[0])
					self.channel_1_dt_queue.put(channel_1_sample[1])
					# self.channel_2_data[i], self.channel_2_dt[i] = self.sample_voltage(self.channel_2_samples)
					if not self.running:
						return
			else:
				# Acquire data:
				for __ in range(self.points_per_graph):
					channel_1_sample = self.channel_1_samples.get()
					self.total_num_samples += 1
					self.channel_1_queue.put(channel_1_sample[0])
					self.channel_1_dt_queue.put(channel_1_sample[1])
					# self.channel_2_data[i], self.channel_2_dt[i] = self.sample_voltage(self.channel_2_samples)
					if not self.running:
						return

	#def sample_voltage(self, samples):  # Acquire single voltage measurement:
		#while len(samples) == 0:
		#	pass
		#self.total_num_samples += 1
		# sample =
		# sample_data	= sample * 0.0032258064516129 		# converts from int to voltage value
		#return samples.get()

		# Sampling frequency divider
		# for i in range(self.rate - 1):
		# 	resp = self.conn.read(8)

	@staticmethod
	def calculate_frequency(data):
		wave = False
		num_peaks = 0
		for v in data:
			if v > 1 and not wave:
				wave = True
				num_peaks += 1
			elif v < 1 and wave:
				wave = False
		return num_peaks
