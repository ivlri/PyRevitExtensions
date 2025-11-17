# -*- coding: utf-8 -*-
#==================================================
#⬇️ IMPORTS
#==================================================
import clr
clr.AddReference('System')
from System import EventHandler

from Autodesk.Revit import UI
from Autodesk.Revit.DB import *

from pyrevit import EXEC_PARAMS, revit,HOST_APP

import re 
from Hooks import auto_rotate
import time

#==================================================
#VARIABLES
#==================================================

args = EXEC_PARAMS.event_args

doc = revit.doc 
uiapp = UI.UIApplication(revit.doc.Application)
transaction_names = list(args.GetTransactionNames())

#==================================================
#MAIN
#==================================================

# Отслеживение изменений
try:
    #added_elements = list(args.GetAddedElementIds()) 
    modified_elements = args.GetModifiedElementIds()
except Exception:
    #added_elements = []
    modified_elements = []

# СОБЫТИЕ - поворт вида -> РЕЗУЛЬТАТ - поворот элементов оформления
#'''При внедрении, во внедряемой функции не должна открываться транзакция !!!'''
if 'Повернуть' in transaction_names:
    print(0)
    if (doc.ActiveView.Id in modified_elements):
        print(0)
        try:
            commandId = UI.RevitCommandId.LookupCommandId("ID_EDIT_ROTATE") # поиск нужного события
            #commandId = UI.RevitCommandId.LookupPostableCommandId(POstableCommand.Rorate) 
            import_binding = uiapp.CreateAddInCommandBinding(commandId) # Получаем само событие
            import_binding.Executed += EventHandler[UI.Events.ExecutedEventArgs](auto_rotate.start_hook()) # Внедряем свой функционал в событие
        except Exception as ex:
            print(ex)