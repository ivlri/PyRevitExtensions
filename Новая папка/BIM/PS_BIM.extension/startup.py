# -*- coding: utf-8 -*- 
#pylint: disable=import-error,invalid-name,broad-except,superfluous-parens
#pylint: disable=unused-import,wrong-import-position,unused-argument
#pylint: disable=missing-docstring
import sys
import time
import os.path as op

from System import Guid

from pyrevit import HOST_APP, framework
from pyrevit import revit, DB, UI
from pyrevit import forms, script
from pyrevit import routes

from Autodesk.Revit.UI import IExternalEventHandler, UIApplication
from Autodesk.Revit.DB import Events

#Activate DockablePanel
class DockableExample(forms.WPFPanel):
    panel_title = "pyRevit Dockable Panel Title"
    panel_id = "3110e336-f81c-4927-87da-4e0d30d4d64a"
    panel_source = op.join(op.dirname(__file__), "DockableExample.xaml")

    def do_something(self, sender, args):
        forms.alert("Voila!!!")


if not forms.is_registered_dockable_panel(DockableExample):
    forms.register_dockable_panel(DockableExample)
else:
    pass
    #print("Skipped registering dockable pane. Already exists.")

