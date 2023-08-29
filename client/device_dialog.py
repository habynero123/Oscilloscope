import wx
#from ..config import CONN_SOCKET, CONN_SERIAL

class DeviceDialog(wx.Dialog):
	"""
		This is the dialog that appears when you choose select device from the main menu
	"""
	def __init__(self):
		"""Constructor"""
		self.method	= 0
		wx.Dialog.__init__(self, None, title="Dialog")

		rbLocalSelect = wx.RadioButton(self, wx.ID_ANY, 'Local')
		rbRemoteSelect = wx.RadioButton(self, wx.ID_ANY, 'Remote')

		self.Bind(wx.EVT_RADIOBUTTON, self.onRbSelect, rbLocalSelect)
		self.Bind(wx.EVT_RADIOBUTTON, self.onRbSelect, rbRemoteSelect)

		#self.comboBox1 = wx.ComboBox(self, choices=['test1', 'test2'], value="")
		okBtn = wx.Button(self, wx.ID_OK)

		sizer = wx.BoxSizer(wx.VERTICAL)
		#sizer.Add(self.comboBox1, 0, wx.ALL | wx.CENTER, 5)
		self.stDeviceAddress = wx.StaticText(self, label="Please enter full path of Bus Pirate serial device:")
		self.etDeviceAddress = wx.TextCtrl(self)

		sizer.Add(rbLocalSelect, 0, wx.ALL | wx.CENTER, 5)
		sizer.Add(rbRemoteSelect, 0, wx.ALL | wx.CENTER, 5)
		sizer.Add(self.stDeviceAddress, 0, wx.ALL | wx.CENTER, 5)
		sizer.Add(self.etDeviceAddress, 0, wx.ALL | wx.CENTER, 5)
		sizer.Add(okBtn, 0, wx.ALL | wx.CENTER, 5)

		self.SetSizer(sizer)

	def onRbSelect(self, event):
		self.method = not self.method
		print self.method
		self.stDeviceAddress.label = str(self.method)
		self.stDeviceAddress.Update()# = str(self.method)
		self.Update()