# -*- coding: utf-8 -*-
#==================================================
#⬇️ IMPORTS
#==================================================
import clr
clr.AddReference('System')
from System import EventHandler

from Autodesk.Revit import UI
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Events import DocumentChangedEventArgs
from Autodesk.Revit.UI import IExternalEventHandler

from pyrevit import EXEC_PARAMS, revit,HOST_APP
from pyrevit import forms, script

import re 
from Hooks import auto_rotate
import time

#==================================================
#VARIABLES
#==================================================
##uiapp = __eventsender__ # UIApplication
#args   = __eventargs__   # Autodesk.Revit.UI.Events.BeforeExecutedEventArgs

args = EXEC_PARAMS.event_args
doc = revit.doc 
uiapp = UI.UIApplication(revit.doc.Application)


#==================================================
#MAIN
#==================================================

# Отслеживение изменений
try:
    #added_elements = list(args.GetAddedElementIds()) 
    modified_elements = list(args.GetModifiedElementIds())
    #print(modified_elements)
except Exception:
    added_elements = []
    modified_elements = []


# Поиск команд, в выполенение которых нужно встроиться
commandId = UI.RevitCommandId.LookupCommandId("ID_EDIT_ROTATE") # поиск нужного события 
#commandId = UI.RevitCommandId.LookupPostableCommandId(POstableCommand.Rorate)

if commandId:
    if (doc.ActiveView.Id in modified_elements):
        try:
            import_binding = uiapp.CreateAddInCommandBinding(commandId) # Получаем событие
            import_binding.Executed += EventHandler[UI.Events.ExecutedEventArgs](auto_rotate.start_hook()) # Внежряем свой функционал в событие
        except Exception as ex:
            pass