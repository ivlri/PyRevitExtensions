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
from pyrevit import forms
from pyrevit import routes

from Autodesk.Revit.UI import IExternalEventHandler
from Autodesk.Revit.DB import Events

from Hooks import auto_rotate


# Set a change triger in a doc
class ExistingDimensionsUpdater_Autorotate(DB.IUpdater):
    def __init__(self, addin_id):
        self.id = DB.UpdaterId(addin_id, Guid("7223be2d-b524-4798-8baf-5b249c2f31c4"))

    def GetUpdaterId(self):
        return self.id

    def GetUpdaterName(self):
        return "Autorotate anatations"

    def GetAdditionalInformation(self):
        return "rotates a anatations after rotating a view"

    def GetChangePriority(self):
        return DB.ChangePriority.Views

    def Execute(self, data):
        doc = data.GetDocument()
        
        for id in data.GetAddedElementIds():
            view = doc.GetElement(id)
            try:
                auto_rotate.start_hook(doc, view)
            except Exception as ex:
                print(ex)


updater = ExistingDimensionsUpdater_Autorotate(__revit__.Application.ActiveAddInId)

if DB.UpdaterRegistry.IsUpdaterRegistered(updater.GetUpdaterId()):
    DB.UpdaterRegistry.UnregisterUpdater(updater.GetUpdaterId())
    
DB.UpdaterRegistry.RegisterUpdater(updater)
dimensions_filter = DB.ElementCategoryFilter(DB.BuiltInCategory.OST_Viewports)
change_type = DB.Element.GetChangeTypeAny()
DB.UpdaterRegistry.AddTrigger(updater.GetUpdaterId(), dimensions_filter, change_type)

