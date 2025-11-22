from dckpanels.workset_panel import WorksetsDockablePanel
from pyrevit import forms, revit, HOST_APP
import clr
clr.AddReference('System')
from System import Guid
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *

WorksetsDockablePanel.panel_doc = HOST_APP.doc
panel_instance = WorksetsDockablePanel.panel_instance
panel_instance.setup_panel() 

# forms.open_dockable_panel(WorksetsDockablePanel.panel_id)
# print(WorksetsDockablePanel.panel_doc)
