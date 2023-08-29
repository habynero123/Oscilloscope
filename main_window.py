import time

import wx
import wx.adv
from wx.lib import plot
from wx.lib.wordwrap import wordwrap
from numpy.fft import rfft

from oscilloscope import Oscilloscope, SYNC_NONE, SYNC_RISE, SYNC_FALL, MODE_CONTINUOUS, MODE_ONESHOT, MIN_VOLTAGE, MAX_VOLTAGE, BASE_RATE
from multiprocessing import Process, Queue

# SERIAL_PORT		= "COM3"
SERIAL_PORT		= "192.168.2.48:8181"

class MainWindow(wx.Frame):
	def __init__(self, parent, title):
		wx.Frame.__init__(self, parent, title=title, id=wx.ID_ANY, size=(640, 480))

		self.oscilloscope		= None
		self.port				= SERIAL_PORT

		self.update_delay		= 1
		self.trigger_voltage	= 0
		self.phase_offset 		= 0
		self.rate 				= 1
		self.points_per_graph 	= 50
		self.sampdt				= self.rate / float(BASE_RATE)
		self.point_width 		= self.points_per_graph * self.sampdt
		self.sync 				= SYNC_NONE
		self.sample_mode		= MODE_CONTINUOUS
		self.trigger_level		= False
		self.trigger_origin		= False
		self.auto_scale			= False
		self.show_fft			= False
		self.channel_1_queue	= Queue()
		self.channel_2_queue	= Queue()
		self.channel_1_dt_queue	= Queue()
		self.channel_2_dt_queue	= Queue()
		self.instruction_queue	= Queue()

		p = Oscilloscope(
			instruction_queue=self.instruction_queue,
			channel_1_queue=self.channel_1_queue,
			channel_1_dt_queue=self.channel_1_dt_queue,
			channel_2_queue=self.channel_2_queue,
			channel_2_dt_queue=self.channel_2_dt_queue
		)
		self.oscilloscope = Process(target=p.start, args=())
		self.oscilloscope.start()

		self.instruction_queue.put(("port", self.port))
		self.instruction_queue.put(("points_per_graph", self.points_per_graph))
		self.instruction_queue.put(("rate", self.rate))
		self.instruction_queue.put(("mode", self.sample_mode))
		self.instruction_queue.put(("sync", self.sync))
		self.instruction_queue.put(("trigger_voltage", self.trigger_voltage))
		self.instruction_queue.put(("phase_offset", self.phase_offset))


		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.OnUpdate, self.timer)
		self.create_ui()
		self.update_plot()

	def update_plot(self):
		if not self.show_fft:
			graphics, plotdomain, plotrange = self.plot_raw()
		else:
			graphics, plotdomain, plotrange = self.plot_fft()
		self.plot_canvas.Draw(graphics, xAxis=plotdomain, yAxis=plotrange)

	def plot_raw(self):
		plotrange = (-1, 7)  # Default voltage range
		plotdomain = (0, 1000 * self.point_width)

		if self.channel_1_queue.empty():
			data = [(0, -10), (1000 * self.point_width, -10)]
			plotlist = [plot.PolyLine(data, colour='red', width=2)]
		else:
			# if self.last_point_time > 0:
			# 	cur_point_time = self.oscilloscope.dt
			# 	self.sampdt = (cur_point_time - self.last_point_time) * .001
			# 	self.last_point_time = cur_point_time
			# self.sampdt = 1.0 / (len(self.oscilloscope.channel_1_data) / self.oscilloscope.sample_duration)
			# self.point_width = self.points_per_graph * self.sampdt
			channel_1_vdata 	= [self.channel_1_queue.get() for __ in range(self.points_per_graph)]
			channel_1_dtdata 	= [self.channel_1_dt_queue.get() for __ in range(self.points_per_graph)]
			# channel_2_vdata 	= self.oscilloscope.channel_2_data[:self.points_per_graph]
			# channel_2_dtdata 	= self.oscilloscope.channel_2_dt[:self.points_per_graph]
			# frequency = (self.oscilloscope.countPeaks(vdata) / self.oscilloscope.sample_duration)
			# self.tc_frequency.SetLabel(str(frequency))

			# Swap next two lines for new and old way
			# data = [(dtdata[i], vdata[i]) for i in range(100)]
			# data = [(i * 1000 * self.sampdt, vdata[i]) for i in range(len(vdata))]
			channel_1_data = []
			# channel_2_data = []
			channel_1_dt_total = 0
			# channel_2_dt_total = 0

			for i in range(self.points_per_graph):
				channel_1_data.append((channel_1_dtdata[i] + channel_1_dt_total, channel_1_vdata[i]))
				channel_1_dt_total += channel_1_dtdata[i]

			# channel_2_data.append((channel_2_dtdata[i] + channel_2_dt_total, channel_2_vdata[i]))
			# channel_2_dt_total += channel_2_dtdata[i]

			channel_1_data = [(i * 1000 * self.sampdt, channel_1_vdata[i]) for i in range(len(channel_1_vdata))]
			if self.auto_scale:
				vmax = max(channel_1_vdata)
				if vmax > 0.0:
					plotrange = (0., max(channel_1_vdata))

			plotlist = [
						plot.PolyLine(channel_1_data, colour="red", width=2)
						# plot.PolyLine(channel_2_data, colour="blue", width=2)
			]

		# Plot trigger voltage level
		if self.trigger_level:
			triglev_dat = [(0, self.trigger_voltage), (1000 * self.point_width, self.trigger_voltage)]
			plotlist.append(plot.PolyLine(triglev_dat, colour='red', style=wx.PENSTYLE_LONG_DASH, width=2))

		# Plot trigger origin time
		if self.trigger_origin:
			trigorig_dat = [(-self.phase_offset * 10. * self.point_width, -1), (-self.phase_offset * 10 * self.point_width, 7)]
			plotlist.append(plot.PolyLine(trigorig_dat, colour='blue', style=wx.PENSTYLE_LONG_DASH, width=2))

		graphics = plot.PlotGraphics(plotlist, '', 'Time (ms)', 'Voltage')
		return graphics, plotdomain, plotrange

	def plot_fft(self):
		if self.oscilloscope.is_alive():
			fftresult = abs(rfft(self.oscilloscope.channel_1_data))
			data = [(float(i) / len(self.oscilloscope.channel_1_data) / self.sampdt, fftresult[i]) for i in range(len(fftresult))]

			plotdomain = (0, data[-1][0])
			plotrange = (-0.05 * max(fftresult), max(fftresult))
			if plotrange[1] == 0.:
				plotrange = (-1, 1)
				plotdomain = (0, (self.points_per_graph / 2 - 1) / (self.points_per_graph * self.sampdt))

		else:
			data = [(0, -10), ((self.points_per_graph / 2 - 1) / (self.points_per_graph * self.sampdt), -10)]
			plotdomain = (0, (self.points_per_graph / 2 - 1) / (self.points_per_graph * self.sampdt))
			plotrange = (0, 1)

		plotlist 	= [plot.PolyLine(data, colour='green', width=1)]
		graphics	= plot.PlotGraphics(plotlist, '', 'Frequency (Hz)', 'Amplitude')
		return graphics, plotdomain, plotrange

	def create_ui(self):
		main = wx.Panel(self)
		self.create_menu()
		controls = self.create_control_panel(main)
		self.create_plot_panel(main, controls)

		self.CreateStatusBar()
		self.Show(True)

	# Menu initialization subroutine:
	def create_menu(self):
		help_menu = wx.Menu()
		self._append_to_menu(help_menu, wx.ID_ABOUT, "&About", "Information about this program.", wx.EVT_MENU, self.show_help)

		file_menu = wx.Menu()
		self._append_to_menu(file_menu, wx.ID_ANY, "&Save Sample", "Save sample to file", wx.EVT_MENU, self.save_sample)
		self._append_to_menu(file_menu)
		self._append_to_menu(file_menu, wx.ID_ANY, "Save &Graph", "Save graph to file", wx.EVT_MENU, self.save_graph)
		self._append_to_menu(file_menu, wx.ID_ANY, "Set Bus Pirate &Device", "Set Bus Pirate serial device.", wx.EVT_MENU, self.set_device)
		self._append_to_menu(file_menu)
		self._append_to_menu(file_menu, wx.ID_EXIT, "E&xit", "Terminate the program.", wx.EVT_MENU, self.exit_app)

		view_menu = wx.Menu()
		grid = self._append_to_menu(view_menu, wx.ID_ANY, "&Grid", "Toggle grid", wx.EVT_MENU, self.toggle_view_grid, kind=wx.ITEM_CHECK)
		self._append_to_menu(view_menu, wx.ID_ANY, "Trigger &Level", "Toggle trigger level visibility", wx.EVT_MENU, self.toggle_trigger_level, kind=wx.ITEM_CHECK)
		self._append_to_menu(view_menu, wx.ID_ANY, "Trigger &Origin", "Toggle trigger origin visibility", wx.EVT_MENU, self.toggle_trigger_origin, kind=wx.ITEM_CHECK)
		self._append_to_menu(view_menu)
		self._append_to_menu(view_menu, wx.ID_ANY, "&Automatic Axis Scaling", "Automatically scale axis based on values", wx.EVT_MENU, self.toggle_autoscale, kind=wx.ITEM_CHECK)
		grid.Check()

		menu_bar = wx.MenuBar()
		menu_bar.Append(file_menu, "&File")
		menu_bar.Append(view_menu, "&View")
		menu_bar.Append(help_menu, "&Help")
		self.SetMenuBar(menu_bar)

	def create_control_panel(self, main_panel):
		control_panel 		= self._create_item(wx.Panel, None, None, main_panel, style=wx.BORDER_SUNKEN)
		rad_trigger_off 	= self._create_item(wx.RadioButton, wx.EVT_RADIOBUTTON, self.sync_off, control_panel, wx.ID_ANY, "No sync", style=wx.RB_GROUP)
		rad_trigger_rise 	= self._create_item(wx.RadioButton, wx.EVT_RADIOBUTTON, self.sync_on_rise, control_panel, wx.ID_ANY, "Rising edge")
		rad_trigger_fall	= self._create_item(wx.RadioButton, wx.EVT_RADIOBUTTON, self.sync_on_fall, control_panel, wx.ID_ANY, "Falling edge")
		ch_rate				= self._create_item(wx.Choice, wx.EVT_CHOICE, self.adjust_sample_rate, control_panel, wx.ID_ANY, choices=[str(int(BASE_RATE / float(i))) for i in range(1, 11)])
		cb_fft 				= self._create_item(wx.CheckBox, wx.EVT_CHECKBOX, self.toggle_fft, control_panel, wx.ID_ANY, "Spectrum")
		sc_win_size			= self._create_item(wx.SpinCtrl, wx.EVT_SPINCTRL, self.adjust_window_size, control_panel, wx.ID_ANY, initial=100, min=10, max=1000)
		sc_phase	 		= self._create_item(wx.SpinCtrl, wx.EVT_SPINCTRL, self.adjust_phase, control_panel, wx.ID_ANY, initial=0, min=-10, max=100)
		self.rad_continuous = self._create_item(wx.RadioButton, wx.EVT_RADIOBUTTON, self.set_continuous_sampling, control_panel, wx.ID_ANY, "Continuous", style=wx.RB_GROUP)
		self.rad_one_shot 	= self._create_item(wx.RadioButton, wx.EVT_RADIOBUTTON, self.set_oneshot_sampling, control_panel, wx.ID_ANY, "Single shot")
		self.btn_sample 	= self._create_item(wx.ToggleButton, wx.EVT_TOGGLEBUTTON, self.toggle_sampling, control_panel, wx.ID_ANY, "SAMPLE")

		ch_rate.SetSelection(0)
		self.btn_sample.SetBackgroundColour("red")

		tc_frequency	= wx.TextCtrl(control_panel, wx.ID_ANY)
		st_frequency	= wx.StaticText(control_panel, wx.ID_ANY, "Frequency:")
		st_phase		= wx.StaticText(control_panel, wx.ID_ANY, "Offset (%win):")
		st_win_size		= wx.StaticText(control_panel, wx.ID_ANY, "Samples/win:")
		st_sample_rate	= wx.StaticText(control_panel, wx.ID_ANY, "Hz")

		bs_trigger_2 = wx.BoxSizer(wx.VERTICAL)
		bs_trigger_2.Add(rad_trigger_off, 1)
		bs_trigger_2.Add(rad_trigger_rise, 1)
		bs_trigger_2.Add(rad_trigger_fall, 1)

		bs_trigger_3 = wx.BoxSizer(wx.VERTICAL)
		bs_trigger_3.Add(st_phase)
		bs_trigger_3.Add(sc_phase)
		bs_trigger_3.Add(st_frequency)
		bs_trigger_3.Add(tc_frequency)

		sb_triggering = wx.StaticBox(control_panel, wx.ID_ANY, "Triggering")
		bs_trigger_1 = wx.StaticBoxSizer(sb_triggering, wx.HORIZONTAL)
		bs_trigger_1.Add(bs_trigger_2, 1, wx.EXPAND)
		bs_trigger_1.Add(bs_trigger_3, 0, wx.EXPAND)

		bs_sampling_2 = wx.BoxSizer(wx.VERTICAL)
		bs_sampling_2.Add(self.rad_continuous, 1)
		bs_sampling_2.Add(self.rad_one_shot, 1)
		bs_sampling_2.Add(cb_fft, 1)

		bs_sampling_4 = wx.BoxSizer(wx.HORIZONTAL)
		bs_sampling_4.Add(ch_rate, 1)
		bs_sampling_4.Add(st_sample_rate, 0)

		bs_sampling_3 = wx.BoxSizer(wx.VERTICAL)
		bs_sampling_3.Add(bs_sampling_4)
		bs_sampling_3.Add(st_win_size)
		bs_sampling_3.Add(sc_win_size)

		sb_sampling = wx.StaticBox(control_panel, wx.ID_ANY, "Sampling")
		bs_sampling_1 = wx.StaticBoxSizer(sb_sampling, wx.HORIZONTAL)
		bs_sampling_1.Add(bs_sampling_2, 1, wx.EXPAND)
		bs_sampling_1.Add(bs_sampling_3, 0, wx.EXPAND)

		bs_cont = wx.BoxSizer(wx.HORIZONTAL)
		bs_cont.Add(self.btn_sample, 0, wx.EXPAND | wx.ALL, 20)
		bs_cont.Add(bs_sampling_1, 1, wx.EXPAND | wx.RIGHT, 20)
		bs_cont.Add(bs_trigger_1, 1, wx.EXPAND)

		control_panel.SetSizer(bs_cont)
		return control_panel

	def create_plot_panel(self, main_panel, control_panel):
		plot_panel = wx.Panel(main_panel)
		bs_main = wx.BoxSizer(wx.VERTICAL)
		bs_main.Add(plot_panel, 1, wx.EXPAND)
		bs_main.Add(control_panel, 0, wx.EXPAND)
		main_panel.SetSizer(bs_main)

		slider_trigger_level = wx.Slider(
			plot_panel,
			wx.ID_ANY,
			int(50. * (MAX_VOLTAGE - MIN_VOLTAGE)),
			int(100. * MIN_VOLTAGE),
			int(100. * MAX_VOLTAGE),
			style=wx.SL_VERTICAL | wx.SL_INVERSE
		)

		slider_trigger_level.SetBackgroundColour("black")
		self.Bind(wx.EVT_SLIDER, self.adjust_trigger_level, slider_trigger_level)
		self.plot_canvas = plot.PlotCanvas(plot_panel)
		self.plot_canvas.SetBackgroundColour("black")
		self.plot_canvas.SetForegroundColour("green")
		self.plot_canvas.gridPen = wx.Pen("green")
		self.plot_canvas.enableGrid = True

		plot_sizer = wx.BoxSizer(wx.HORIZONTAL)
		plot_sizer.Add(self.plot_canvas, 1, wx.EXPAND)
		plot_sizer.Add(slider_trigger_level, 0, wx.EXPAND | wx.BOTTOM, 20)
		plot_panel.SetBackgroundColour("black")
		plot_panel.SetSizer(plot_sizer)

	def _append_to_menu(self, menu, id_=None, title=None, desc=None, bind_type=None, callback=None, **kwargs):
		if id_ and title and desc:
			menu_item = menu.Append(id_, title, desc, **kwargs)
			if bind_type and callback:
				self.Bind(bind_type, callback, menu_item)
			return menu_item
		menu.AppendSeparator()

	def _create_item(self, item_type, bind_type=None, callback=None, *args, **kwargs):
		item = item_type(*args, **kwargs)
		if bind_type and callback:
			self.Bind(bind_type, callback, item)
		return item

	def toggle_view_grid(self, event):
		self.plot_canvas.enableGrid = event.IsChecked()

	def toggle_trigger_level(self, event):
		self.trigger_level = event.IsChecked()
		self.update_plot()

	def toggle_trigger_origin(self, event):
		self.trigger_origin = event.IsChecked()
		self.update_plot()

	def toggle_autoscale(self, event):
		self.auto_scale = event.IsChecked()
		self.update_plot()

	def show_help(self, event):
		info 			= wx.adv.AboutDialogInfo()
		info.Name 		= "Oscilloscope"
		info.Copyright 	= "(C) 2010 Tim Vaughan"
		info.License 	= wordwrap(
			"This program is free software: you can redistribute it and/or modify "
			"it under the terms of the GNU General Public License as published by "
			"the Free Software Foundation, either version 3 of the License, or "
			"(at your option) any later version."

			"\n\nThis program is distributed in the hope that it will be useful, "
			"but WITHOUT ANY WARRANTY; without even the implied warranty of "
			"MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the "
			"GNU General Public License for more details."

			"along with this program.  If not, see <http://www.gnu.org/licenses/>.",
			500,
			wx.ClientDC(self))
		info.Description = wordwrap(
			"A small utility which allows one to use the ADC input of a "
			"Bus Pirate as a slow, single-channel oscilloscope.  Triggering "
			"and spectrum analysis are supported.",
			350,
			wx.ClientDC(self))
		wx.adv.AboutBox(info)

	# Set Bus Pirate serial device:
	def set_device(self, event):
		dlg = wx.TextEntryDialog(
			self,
			"Please enter full path of Bus Pirate serial device:",
			"Set Bus Pirate Device",
			self.port)
		if dlg.ShowModal() == wx.ID_OK:
			self.port = dlg.GetValue()
		self.instruction_queue.put(("port", self.port))
		#self.oscilloscope.port = self.port
		dlg.Destroy()

	def OnUpdate(self, event):
		self.update_plot()

		if not self.oscilloscope.is_alive():
			self.timer.Stop()

			self.btn_sample.SetValue(False)
			self.btn_sample.SetBackgroundColour('green')
			self.btn_sample.SetLabel('SAMPLING')

	def toggle_sampling(self, event):
		if not self.oscilloscope.is_alive():
			try:
				# self.oscilloscope.start()
				self.instruction_queue.put(("start", ""))
			except Exception as e:
				msg = "Failed to open Bus Pirate port '{0}'\nCheck connection.\n{1}".format(self.port, e)
				dlg = wx.MessageDialog(self, msg, "Error", wx.OK)
				dlg.ShowModal()
				dlg.Destroy()
				return

		if event.EventObject.GetValue():
			self.instruction_queue.put(("unpause", ""))

			event.EventObject.SetBackgroundColour('red')
			event.EventObject.SetLabel('    STOP\nSAMPLING')

			self.rad_one_shot.Disable()
			self.rad_continuous.Disable()

			# Start plot timer (0.1s intervals):
			self.timer.Start(milliseconds=self.update_delay)

		else:
			#self.oscilloscope.pause()
			self.instruction_queue.put(("pause", ""))
			self.timer.Stop()
			self.update_plot()

			event.EventObject.SetBackgroundColour('green')
			event.EventObject.SetLabel('SAMPLING')

			# Ensure sampling mode radio buttons are enabled:
			self.rad_one_shot.Enable()
			self.rad_continuous.Enable()

	def set_continuous_sampling(self, event):
		self.sample_mode = MODE_CONTINUOUS

	def set_oneshot_sampling(self, event):
		self.sample_mode = MODE_ONESHOT

	def toggle_fft(self, event):
		self.show_fft = event.IsChecked()
		self.update_plot()

	def sync_on_rise(self, event):
		self.sync = SYNC_RISE
		# self.oscilloscope.sync = self.sync
		self.instruction_queue.put(("sync", self.sync))

	def sync_on_fall(self, event):
		self.sync = SYNC_FALL
		# self.oscilloscope.sync = self.sync
		self.instruction_queue.put(("sync", self.sync))

	def sync_off(self, event):
		self.sync = SYNC_NONE
		# self.oscilloscope.sync = self.sync
		self.instruction_queue.put(("sync", self.sync))

	def adjust_trigger_level(self, event):
		self.trigger_voltage = event.EventObject.GetValue() / 100.0
		# if self.btn_sample.GetValue():
		# self.oscilloscope.trigger_voltage = self.trigger_voltage
		self.instruction_queue.put(("trigger_voltage", self.trigger_voltage))
		# elif self.trigger_level:
		self.update_plot()

	def adjust_sample_rate(self, event):
		self.rate 			= event.GetSelection() + 1
		self.sampdt 		= self.rate / float(BASE_RATE)
		self.point_width 	= self.points_per_graph * self.sampdt
		if self.oscilloscope and self.oscilloscope.is_alive():
			# self.oscilloscope.rate = self.rate
			self.instruction_queue.put(("rate", self.rate))
		# else:
		self.update_plot()

	def adjust_window_size(self, event):
		self.points_per_graph 	= wx.SpinEvent(event).GetPosition()
		self.point_width 		= self.points_per_graph * self.sampdt
		if self.oscilloscope and self.oscilloscope.is_alive():
			# self.oscilloscope.points_per_graph = self.points_per_graph
			# self.oscilloscope.set_points_per_graph(self.points_per_graph)
			self.instruction_queue.put(("points_per_graph", self.points_per_graph))
		# else:
		self.update_plot()

	def adjust_phase(self, event):
		self.phase_offset = wx.SpinEvent(event).GetPosition()
		if self.oscilloscope and self.oscilloscope.is_alive():
			#self.oscilloscope.phase_offset = self.phase_offset
			self.instruction_queue.put(("phase_offset", self.phase_offset))
		# elif self.trigger_origin:
		self.update_plot()

	def save_sample(self, event):
		if not self.oscilloscope:
			msg = "No sampled data to write."
			errordlg = wx.MessageDialog(self, msg, "Error", wx.OK)
			errordlg.ShowModal()
			errordlg.Destroy()
			return

		dlg = wx.FileDialog(
			self,
			message="Save sample as...",
			defaultDir=".",
			defaultFile="",
			wildcard="*.txt",
			style=wx.ID_SAVE)

		if dlg.ShowModal() == wx.ID_OK:
			path = dlg.GetPath()

			try:
				with open(path, "w+") as fd:
					fd.write('t V\n')
					for i in range(len(self.oscilloscope.channel_1_data)):
						V = self.oscilloscope.channel_1_data[i]
						t = i * self.sampdt * 1000.
						fd.write('%g %g\n' % (t, V))
			except Exception as e:
				msg = "Error writing data to file\n :{error}".format(error=e)
				errordlg = wx.MessageDialog(self, msg, "Error", wx.OK)
				errordlg.ShowModal()
				errordlg.Destroy()
		dlg.Destroy()

	def save_graph(self, event):
		# Use built-in PyPlot image saving method:
		self.plot_canvas.SaveFile()

	def exit_app(self, event):
		self.timer.Stop()
		if self.oscilloscope:
			#self.oscilloscope.shutdown()
			self.instruction_queue.put(("shutdown", ""))

			time.sleep(0.5)
		self.Close(True)

# Main program loop:
if __name__ == '__main__':
	app = wx.App(False)
	frame = MainWindow(None, 'Oscilloscope')
	app.MainLoop()
