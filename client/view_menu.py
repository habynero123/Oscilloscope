import wx
#from ..config import CONN_SOCKET, CONN_SERIAL

class ViewMenu(wx.Dialog):		# View menu:
	def __init__(self, main_window):
		self.main_window = main_window

	def menu_setup(self):
		menu_bar = wx.MenuBar()
		file_menu = wx.Menu()
		help_menu = wx.Menu()
		view_menu = wx.Menu()

		selection_about = help_menu.Append(wx.ID_ABOUT, "&About", "Information about this program.")
		selection_save_sample = file_menu.Append(wx.ID_ANY, "&Save Sample", "Save sample to file")
		file_menu.AppendSeparator()

		selection_save_graph = file_menu.Append(wx.ID_ANY, "Save &Graph", "Save graph to file")
		selection_set_device = file_menu.Append(wx.ID_ANY, "Set Bus Pirate &Device", "Set Bus Pirate serial device.")
		file_menu.AppendSeparator()

		selection_exit = file_menu.Append(wx.ID_EXIT, "E&xit", "Terminate the program.")
		menu_bar.Append(file_menu, "&File")

		self.selection_view_grid = view_menu.Append(wx.ID_ANY, "&Grid", "Toggle grid", kind=wx.ITEM_CHECK)
		self.selection_trigger_level = view_menu.Append(wx.ID_ANY, "Trigger &Level", "Toggle trigger level visibility", kind=wx.ITEM_CHECK )
		self.selection_trigger_origin = view_menu.Append(wx.ID_ANY, "Trigger &Origin", "Toggle trigger origin visibility", kind=wx.ITEM_CHECK)
		view_menu.AppendSeparator()

		self.selection_view_autoscale = view_menu.Append(wx.ID_ANY, "&Automatic Axis Scaling", kind=wx.ITEM_CHECK)
		menu_bar.Append(view_menu, "&View")
		menu_bar.Append(help_menu, "&Help")

		self.selection_view_grid.Check()
		self.Bind(wx.EVT_MENU, self.main_window.OnFileSaveSample, selection_save_sample)
		self.Bind(wx.EVT_MENU, self.main_window.OnFileSaveGraph, selection_save_graph)
		self.Bind(wx.EVT_MENU, self.main_window.OnFileSetDevice, selection_set_device)
		self.Bind(wx.EVT_MENU, self.main_window.OnFileExit, selection_exit)
		self.Bind(wx.EVT_MENU, self.main_window.OnViewGrid, self.selection_view_grid)
		self.Bind(wx.EVT_MENU, self.main_window.OnViewTrigLev, self.selection_trigger_level)
		self.Bind(wx.EVT_MENU, self.main_window.OnViewTrigOrig, self.selection_trigger_origin)
		self.Bind(wx.EVT_MENU, self.main_window.OnViewAutoscale, self.selection_view_autoscale)
		self.Bind(wx.EVT_MENU, self.main_window.OnHelpAbout, selection_about)
		self.main_window.SetMenuBar(menu_bar)