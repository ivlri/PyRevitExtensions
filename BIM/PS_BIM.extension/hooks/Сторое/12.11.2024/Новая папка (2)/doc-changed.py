# -*- coding: utf-8 -*-
#==================================================
#⬇️ IMPORTS
#==================================================
import clr
clr.AddReference('System')
import System
from System import EventHandler

from Autodesk.Revit import UI
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Events import DocumentChangedEventArgs
from pyrevit import EXEC_PARAMS, revit,HOST_APP, DB

import re 
from Hooks import auto_rotate
import time


class ExistingDimensionsUpdater(DB.IUpdater):
    def __init__(self, addin_id):
        self.id = DB.UpdaterId(addin_id, System.Guid("7223be2d-b524-4798-8baf-5b249c2f31c4"))
        matchPattern = "^E-"
        self.reMatcher = re.compile(matchPattern, re.IGNORECASE)

    def GetUpdaterId(self):
        return self.id

    def GetUpdaterName(self):
        return "Existing Dimensions Updater"

    def GetAdditionalInformation(self):
        return "Adds ± character as a suffix for E- dimensions"

    def GetChangePriority(self):
        return DB.ChangePriority.Views

    def Execute(self, data):
        auto_rotate.start_hook()

updater = ExistingDimensionsUpdater(__revit__.ActiveAddInId)

if DB.UpdaterRegistry.IsUpdaterRegistered(updater.GetUpdaterId()):
    DB.UpdaterRegistry.UnregisterUpdater(updater.GetUpdaterId())
    
DB.UpdaterRegistry.RegisterUpdater(updater)
dimensions_filter = DB.ElementCategoryFilter(DB.BuiltInCategory.OST_Grids)
change_type = DB.Element.GetChangeTypeElementAddition()
DB.UpdaterRegistry.AddTrigger(updater.GetUpdaterId(), dimensions_filter, change_type)
#==================================================
#VARIABLES
#==================================================

# args = EXEC_PARAMS.event_args
# print(args.Operation)
# UIAPP = __revit__
# #UIDOC = UIAPP.ActiveUIDocument
# #DOC = UIDOC.Document

# doc = revit.doc 
# uiapp = UI.UIApplication(revit.doc.Application)
# transaction_names = list(args.GetTransactionNames())

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

# updater_id = UpdaterId(UIAPP.ActiveAddInId, SymbolUpdater.uuid())
# print(updater_id)
# СОБЫТИЕ - поворт вида -> РЕЗУЛЬТАТ - поворот элементов оформления
'''При внедрении, во внедряемой функции не должна открываться транзакция !!!'''
# if 'Повернуть' in transaction_names:
#     print(0)
#     if (doc.ActiveView.Id in modified_elements):
#         print(0)
#         try:
#             commandId = UI.RevitCommandId.LookupCommandId("ID_EDIT_ROTATE") # поиск нужного события
#             #commandId = UI.RevitCommandId.LookupPostableCommandId(POstableCommand.Rorate) 
#             import_binding = uiapp.CreateAddInCommandBinding(commandId) # Получаем само событие
#             __revit__.DocumentChanged += EventHandler[DocumentChangedEventArgs](auto_rotate.start_hook()) # Внедряем свой функционал в событие
#         except Exception as ex:
#             print(ex)