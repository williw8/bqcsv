import os
import wx
import sys
import random
import csvdb
import csvfile
import csvmemory
import traceback
import wx.grid
import wx.lib.agw.flatnotebook as flatbook

from datetime import datetime

LEFT_FISH = '<{{{(<<'
RIGHT_FISH = '>>)}}}>'
MAIN_TITLE = 'bqcsv ' + RIGHT_FISH 
# BOX_SPACER=5

MENU_ID_OPEN = 1001
MENU_ID_SAVEAS = 1002
MENU_ID_EXIT = 1010

MENU_ID_ACTION_BASE = 2000

ACTIONS_PATH = 'actions'

STR_UNKNOWN_LABEL = 'unknown'
STR_NO_DESCRIPTION = 'none'

def getTempFilename():
  now = datetime.now()
  return now.strftime('%Y%m%d%H%M%S') + '_' + str(random.randint(0,0xffff)) + '.tmp'

class ImportedModule(object):

  def __init__(self,mod,parent_frame):
    self.id = -1
    self.python_module = mod
    self.plugin = mod.get_plugin(parent_frame)

  def getLabel(self):
    if self.plugin and hasattr(self.plugin,'get_label'):
      return self.plugin.get_label()
    return STR_UNKNOWN_LABEL


  def getDescription(self):
    if self.plugin and hasattr(self.plugin,'get_description'):
      return self.plugin.get_description()
    return STR_NO_DESCRIPTION

  def getId(self):
    return self.id

  def setId(self,ID):
    self.id = ID

  def doAction(self,table):
    if self.plugin and hasattr(self.plugin,'do_action'):
      self.plugin.do_action(table)
    else:
      wx.MessageBox('Module has no do_action method', 'Info', wx.OK | wx.ICON_INFORMATION) 
  
class JoinDialog(wx.Dialog):

  def __init__(self,parent,table):
    wx.Dialog.__init__(self,parent)
    self.other_table_path = None
    self.join_column = None

    self.initUI()
    self.SetSize((320,240))
    self.SetTitle("Join")


  def initUI(self):
    vbox = wx.BoxSizer(wx.VERTICAL)

    hbox = wx.BoxSizer(wx.HORIZONTAL)
    x = wx.StaticText(self,-1,"Table to Join")
    hbox.Add(x)
    self.other_table = wx.ComboBox(self,style=wx.CB_DROPDOWN,choices=self.table.header)
    self.other_table.SetEditable(False)
    self.other_table.SetStringSelection(self.table.header[0])
    hbox.Add(self.horiz_ctrl)
    vbox.Add(hbox);

    hbox = wx.BoxSizer(wx.HORIZONTAL)
    x = wx.StaticText(self,-1,"Join Column")
    hbox.AddSpacer(BOX_SPACER)
    hbox.Add(x)
    hbox.AddSpacer(BOX_SPACER)
    self.join_column = wx.ComboBox(self,style=wx.CB_DROPDOWN,choices=self.table.header)
    self.join_column.SetEditable(False)
    self.join_column.SetStringSelection(self.table.header[-1])
    hbox.AddSpacer(BOX_SPACER)
    hbox.Add(self.vert_ctrl)
    hbox.AddSpacer(BOX_SPACER)
    vbox.Add(hbox);

    self.ok_button.Bind(wx.EVT_BUTTON,self.onOK)
    self.cancel_button.Bind(wx.EVT_BUTTON,self.onCancel)

    self.SetSizer(vbox)

  def getOtherTablePath(self):
    return self.other_table

  def getJoinColumn(self):
    return self.join_column

  def onOK(self,event):
    idx = self.other_table.GetCurrentSelection()
    self.other_table = self.table.header[idx]
    idx = self.join_column.GetCurrentSelection()
    self.join_column = self.table.header[idx]
    self.EndModal(wx.ID_OK)

  def onCancel(self,event):
    self.EndModal(wx.ID_CANCEL)

class CsvPanel(wx.Panel):

  def __init__(self,path,parent,delete_on_exit):
    wx.Panel.__init__(self,parent=parent)

    self.path = path
    self.main_frame = parent
    self.delete_on_exit = delete_on_exit

    self.reader = csvfile.SingleFileReader(path)
    self.table = self.reader.load()
    self.grid_cols = len(self.table.header)
    self.grid_rows = 0
    sizer = wx.BoxSizer(wx.VERTICAL)
    self.grid = wx.grid.Grid(self)
    self.grid.CreateGrid(self.grid_rows,self.grid_cols)

    vcol = 0
    for label in self.table.header:
      self.grid.SetColLabelValue(vcol,label)
      vcol += 1 
    vrow = 0
    for row in self.table.get_iter():
      self.grid.AppendRows()
      vcol = 0
      for v in row:
        self.grid.SetCellValue(vrow,vcol,v)
        vcol += 1
      vrow += 1
    self.grid.AutoSizeColumns(False)
    sizer.Add(self.grid)
    self.SetSizer(sizer)
    #sizer.Fit(parent)

  def save(self,path):
    store = self.table.get_store()
    if None is not store:
      store.save(path)

  def close(self):
    if self.delete_on_exit:
      if None is not self.table:
        self.table.close()
      os.remove(self.path)

  def action(self,mod):
    mod.doAction(self.table)            

class MainFrame(wx.Frame):

  def __init__(self,parent,title):
    width,height = wx.GetDisplaySize()
    width -= width/4
    height -= height/4
    wx.Frame.__init__(self,parent,title=title,size=(width,height))

    self.notebook = flatbook.FlatNotebook(self,-1)
    self.Bind(flatbook.EVT_FLATNOTEBOOK_PAGE_CHANGING,self.onPageChanging)
    self.Bind(flatbook.EVT_FLATNOTEBOOK_PAGE_CHANGED,self.onPageChanged)

    self.Bind(wx.EVT_CLOSE, self.onCloseWindow)

    self.tabs = list()
    self.current_tab = None

    self.loadModules()

    self.createMenu()

    self.Show(True)

  def loadModules(self):
    self.modules = list()
    for name in os.listdir(ACTIONS_PATH):
      if os.path.isdir(os.path.join(ACTIONS_PATH,name)):
        import_path = ACTIONS_PATH + '.' + name
        try:
          mod = __import__(import_path,fromlist = ["*"])
          if None is not mod:
            new_mod = ImportedModule(mod,self)
            self.modules.append(new_mod)
        except ImportError as ex:
          pass

  def createMenu(self):
    self.menu_bar = wx.MenuBar()
    # File
    self.menu_file = wx.Menu()
    self.menu_file.st1cky = True
    self.menu_file.Append(MENU_ID_OPEN,'Open','Open a .csv file')
    wx.EVT_MENU(self,MENU_ID_OPEN,self.onOpen)
    self.menu_file.Append(MENU_ID_SAVEAS,'Save As','Save to a new file')
    wx.EVT_MENU(self,MENU_ID_SAVEAS,self.onSaveAs)
    self.menu_file.AppendSeparator()
    self.menu_file.Append(MENU_ID_EXIT,'Exit','Quit the program')
    wx.EVT_MENU(self,MENU_ID_EXIT,self.onExit)

    self.menu_bar.Append(self.menu_file,'File') 

    # Action
    self.menu_action = wx.Menu()

    ID = MENU_ID_ACTION_BASE
    for mod in self.modules:
      label = mod.getLabel()
      desc = mod.getDescription()
      self.menu_action.Append(ID,label,desc)
      #wx.EVT_MENU(self,ID,mod.onAction)
      wx.EVT_MENU(self,ID,self.onAction)
      mod.setId(ID)
      ID += 1
    self.menu_bar.Append(self.menu_action,'Action') 
    self.SetMenuBar(self.menu_bar)

  def addPage(self,path,delete_on_exit=False):
    self.delete_on_exit = delete_on_exit
    self.current_tab = CsvPanel(path,self,delete_on_exit)
    self.notebook.AddPage(self.current_tab,os.path.basename(path),select=True)

  def onAction(self,event):
    ID = event.GetId()
    for mod in self.modules:
      if ID == mod.getId():
        self.current_tab.action(mod)
        break

  def onPageChanging(self,event):
    pass

  def onPageChanged(self,event):
    #index = event.GetSelection()
    #title = self.notebook.GetPageText(index)
    window = self.notebook.GetCurrentPage()
    if None is not window:
      self.current_tab = window

  def onOpen(self,event):
    try:
      dialog = wx.FileDialog(self)
      chk = dialog.ShowModal()
      if wx.ID_OK == chk:
        path = dialog.GetPath()
        self.addPage(path)
      dialog.Destroy()
    except Exception as ex:
      self.showInfoMessage('Error opening file',str(ex.message))

  def onSaveAs(self,event):
    try:
      dialog = wx.FileDialog(self,style=wx.FD_SAVE)
      chk = dialog.ShowModal()
      if wx.ID_OK == chk:
        path = dialog.GetPath()
        self.current_tab.save(path)
      dialog.Destroy()
    except Exception as ex:
      self.showInfoMessage('Error saving file',str(ex.message))


  def onCloseWindow(self,event):
    self.closingTime()
    self.Destroy()
    return True

  def onExit(self,event):
    self.Close()

  def closingTime(self):
    tabs = self.notebook.GetChildren()
    for tab in tabs:
      if hasattr(tab,'close'):
        tab.close()

  def onJoin(self,event):
    sfr = csvfile.SingleFileReader(path)

  def showInfoMessage(self,caption,message):
    dlg = wx.MessageDialog(self,message,caption,wx.OK|wx.ICON_INFORMATION)
    dlg.ShowModal()
    dlg.Destroy()

class TheApp(wx.App):

  def OnInit(self):
    sys.excepthook = self.handle_exception
    frame = MainFrame(None,MAIN_TITLE)
    self.SetTopWindow(frame)
    return True

  def handle_exception(self,etype,evalue,trace_back):
    traceback.print_exception(etype,evalue,trace_back)

if '__main__' == __name__:
  random.seed(getTempFilename())
  x = TheApp(False)
  x.MainLoop()
                
