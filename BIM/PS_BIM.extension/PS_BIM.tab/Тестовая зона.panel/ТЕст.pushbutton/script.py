# -*- coding: utf-8 -*-
__title__   = "Test"
__doc__ = """Кнопка для быстрого тестирования функций."""

#==================================================
#IMPORTS
#==================================================
import os
import clr
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
import sys
import re
from System.Collections.Generic import List
clr.AddReference('System.IO')
from pyrevit import forms
import json
import codecs

doc   = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app   = __revit__.Application
uiapp   = __revit__
act_view = doc.ActiveView

#--- Освободить все элементы
relinquish = RelinquishOptions(doc)
relinquish.CheckedOutElements = True
relinquish.FamilyWorksets = True
relinquish.StandardWorksets = True
relinquish.UserWorksets = True 

transact_options = TransactWithCentralOptions()

WorksharingUtils.RelinquishOwnership(doc, relinquish, transact_options)
    
    # t.Commit()

# import clr
# clr.AddReference('RevitAPI')
# from Autodesk.Revit.DB import *


# worksets = FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset)

# # Освобождаем каждый рабочий набор
# with Transaction(doc, "Release Worksets") as trans:
#     trans.Start()
    
#     for workset in worksets:
#         if workset.IsEditable:

#             print(workset)
#             print(workset.Name)

#             WorksetTable.ReleaseWorkset(doc, workset.Id)
    
#     trans.Commit()

