import wx
import usb


class DeviceDialog(wx.Dialog):

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent=parent, title="Choose Device")

        self.panel_device_type = wx.Panel(self, -1)
        self.panel_device_type_staticbox = wx.StaticBox(self.panel_device_type, -1, "Device Type")
        self.checkbox_device_type_network = wx.CheckBox(self.panel_device_type, -1, "network")
        self.checkbox_usb = wx.CheckBox(self.panel_device_type, -1, "usb")

        self.panel_usb = wx.Panel(self, -1)
        self.sizer_usb_staticbox = wx.StaticBox(self.panel_usb, -1, "USB Devices")
        self.combo_box_devices = wx.ComboBox(self.panel_usb, -1, choices=self.get_usb_devices(), style=wx.CB_DROPDOWN)

        self.panel_network = wx.Panel(self, -1)
        self.sizer_network_staticbox = wx.StaticBox(self.panel_network, -1, "Network Selection")
        self.text_ctrl_network_address = wx.TextCtrl(self.panel_network, -1, "")
        self.text_ctrl_network_port = wx.TextCtrl(self.panel_network, -1, "")
        self.text_ctrl_network_address.SetHint("address")
        self.text_ctrl_network_port.SetHint("port")
        self.button_ok = wx.Button(self, wx.ID_OK, "")
        self.button_cancel = wx.Button(self, wx.ID_CANCEL, "")
        self.button_usb_rescan = wx.Button(self.panel_usb, wx.ID_HELP_SEARCH, label="Rescan")
        self.button_ok.SetDefault()
        # self.panel_network.Hide()
        self.panel_device_type.SetBackgroundColour = (240, 220, 200)
        self.panel_usb.SetBackgroundColour = (120, 220, 120)
        self.panel_network.SetBackgroundColour = (20, 20, 200)
        self.init()
        self.attach_handlers()

    def attach_handlers(self):
        self.checkbox_usb.Bind(wx.EVT_CHECKBOX, self.on_usb_select)
        self.checkbox_device_type_network.Bind(wx.EVT_CHECKBOX, self.on_network_select)
        self.button_usb_rescan.Bind(wx.EVT_BUTTON, self.on_usb_rescan)

    def on_usb_rescan(self, event):
        print("RESCANNING")
        # btn = event.GetEventObject()
        devices = self.get_usb_devices()
        self.combo_box_devices.Clear()
        for device in devices:
            self.combo_box_devices.Append(device)

    def on_usb_select(self, event):
        if self.checkbox_usb.IsChecked():
            print("Checked")
            self.checkbox_device_type_network.SetValue(0)
            self.panel_network.Hide()
            self.panel_usb.Show()
            self.Layout()
        else:
            print("UNCHECKED")

    def on_network_select(self, event):
        if self.checkbox_device_type_network.IsChecked():
            print("Checked")
            self.checkbox_usb.SetValue(0)
            self.panel_usb.Hide()
            self.panel_network.Show()
            self.Layout()
        else:
            print("UNCHECKED")

    def init(self):
        # sizer_1 = wx.StaticBoxSizer(self.sizer_1_staticbox, wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)

        sizer_device_type = wx.StaticBoxSizer(self.panel_device_type_staticbox, wx.HORIZONTAL)
        sizer_device_type.Add(self.checkbox_device_type_network, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)
        sizer_device_type.Add(self.checkbox_usb, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)
        sizer_device_type.Add((10, 10), 1, wx.EXPAND, 0)
        self.panel_device_type.SetSizer(sizer_device_type)

        # sizer_2.Add(sizer_1, 0, wx.EXPAND, 0)
        sizer_2.Add(self.panel_device_type, 0, wx.EXPAND, 0)

        sizer_usb = wx.StaticBoxSizer(self.sizer_usb_staticbox, wx.HORIZONTAL)
        sizer_usb.Add(self.combo_box_devices, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)
        sizer_usb.Add(self.button_usb_rescan, 0, 0, 0)
        sizer_usb.Add((10, 10), 1, wx.EXPAND, 0)
        self.panel_usb.SetSizer(sizer_usb)

        sizer_network = wx.StaticBoxSizer(self.sizer_network_staticbox, wx.HORIZONTAL)
        sizer_network.Add(self.text_ctrl_network_address, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)
        sizer_network.Add(self.text_ctrl_network_port, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)
        sizer_network.Add((10, 10), 1, wx.EXPAND, 0)
        self.panel_network.SetSizer(sizer_network)

        sizer_3.Add(self.button_ok, 0, 0, 0)
        sizer_3.Add(self.button_cancel, 0, 0, 0)

        sizer_2.Add(self.panel_usb, 0, wx.EXPAND, 0)
        sizer_2.Add(self.panel_network, 0, wx.EXPAND, 0)
        sizer_2.Add(sizer_3, 0, wx.ALL | wx.ALIGN_RIGHT, 4)

        self.SetSizer(sizer_2)
        sizer_2.Fit(self)
        self.checkbox_usb.SetValue(1)
        self.Layout()

    @staticmethod
    def get_usb_devices():
        devices = []
        try:
            for config in usb.core.find(find_all=True):
                devices.append((config.idVendor, config.idProduct))
        except Exception as e:
            pass
        return devices
