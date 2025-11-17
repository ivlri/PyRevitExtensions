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

import math
import re 
from Hooks import auto_rotate
import time


#==================================================
#VARIABLES
#==================================================
##uiapp = __eventsender__ # UIApplication
#args   = __eventargs__   # Autodesk.Revit.UI.Events.BeforeExecutedEventArgs

#uiapp = __eventsender__
args   = __eventargs__
doc    = args.GetDocument()

uiapp = UI.UIApplication(revit.doc.Application)

#==================================================
#CLASSES
#==================================================

# class App_DocumentChanged(DocumentChangedEventArgs):

#     def __init__(self) -> None:
#         self.
#==================================================
#MAIN
#==================================================

#Отслеживение изменений
try:
    #added_elements = list(args.GetAddedElementIds()) 
    modified_elements = args.GetModifiedElementIds()
    modified_elements_name = [doc.GetElement(i).Name for i in modified_elements]
    #print('Id doc: {}'.format(doc.ActiveView.Id))
    #for i in modified_elements:
        #print('Mod_El_ID: {a} {b}'.format(a=doc.GetElement(i).Name,b=i))
except Exception:
    added_elements = []
    modified_elements = []


# Поиск команд, в выполенение которых нужно встроиться
#commandId = UI.RevitCommandId.LookupPostableCommandId(POstableCommand.Rorate)

def CheckAngleView(view):
    uv_X = view.RightDirection
    uv_Y = view.UpDirection

    basis_X = XYZ.BasisX
    basis_Y = XYZ.BasisY

    if basis_X.IsAlmostEqualTo(uv_X) and basis_Y.IsAlmostEqualTo(uv_Y):
        print(True)
        return True
    else: 
         return False

# if CheckAngleView(doc.ActiveView):
try:
    if ('Без названия' in modified_elements_name) and (doc.ActiveView.Id in modified_elements):
            commandId = UI.RevitCommandId.LookupCommandId("ID_EDIT_ROTATE") # поиск нужного события 
            import_binding = uiapp.CreateAddInCommandBinding(commandId) # Получаем событие поворота
            import_binding.Executed += EventHandler[UI.Events.ExecutedEventArgs](auto_rotate.start_hook()) # Внежряем свой функционал в событие поворота
except Exception as ex:
    pass