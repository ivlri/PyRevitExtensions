# # -*- coding: utf-8 -*-
# #==================================================
# #⬇️ IMPORTS
# #==================================================
# import clr
# clr.AddReference('System')
# from System import EventHandler
# import System.Windows.Forms as WinForms

# from Autodesk.Revit import UI
# from Autodesk.Revit.DB import *
# from Autodesk.Revit.DB.Events import DocumentChangedEventArgs
# from Autodesk.Revit.UI import IExternalEventHandler

# from pyrevit import EXEC_PARAMS, revit,HOST_APP
# from pyrevit import forms, script

# import re 
# from Hooks import auto_rotate
# import time

# #==================================================
# #VARIABLES
# #==================================================
# ##uiapp = __eventsender__ # UIApplication
# #args   = __eventargs__   # Autodesk.Revit.UI.Events.BeforeExecutedEventArgs

# #uiapp = __eventsender__
# args   = __eventargs__
# doc    = args.GetDocument()

# uiapp = UI.UIApplication(revit.doc.Application)

# from Autodesk.Revit.DB import IUpdater, UpdaterId, ElementId, UpdaterRegistry
# from Autodesk.Revit.DB import Element, ElementCategoryFilter, BuiltInCategory, ChangePriority,Element, ElementId, ElementParameterFilter, ParameterValueProvider, FilterStringEquals, BuiltInParameter
# from Autodesk.Revit.UI import TaskDialog,TaskDialogCommonButtons,TaskDialogResult
# from Autodesk.Revit.DB import Transaction
# from System import Guid


# #==================================================
# #CLASSES
# #==================================================
# current_user = doc.Application.Username
# allowed_users = ["legostaev", "chernova.a"]

# transaction_names = args.GetTransactionNames()
# #forms.alert(''.join(transaction_names))

# try:
#     #added_elements = list(args.GetAddedElementIds()) 
#     id_modified_elements = list(args.GetModifiedElementIds())
#     #print(id_modified_elements)\
#     for Id in id_modified_elements:
#         print(Id)
#         print(GeometryElement(Id).Name)
#     # names_modified_elements = [GeometryElement(Id) for Id in id_modified_elements]
#     # print(names_modified_elements)
# except Exception:
#     #added_elements = []
#     modified_elements = []

# # if (any(transaction_name == 'Выгрузить связь' for transaction_name in transaction_names)) and ("_BS" in names_modified_elements):
# #     print(type(transaction_names))
# #     WinForms.MessageBox.Show("Выгрузка BS связей запрещена!!!", "Предупреждение", WinForms.MessageBoxButtons.OK, WinForms.MessageBoxIcon.Warning)



# #==================================================
# #MAIN
# #==================================================
