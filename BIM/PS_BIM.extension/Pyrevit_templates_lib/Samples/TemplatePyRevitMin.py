# -*- coding: utf-8 -*-
__title__ = "EF Template.min"
__doc__ = """Version = 1.0"""

#==================================================
#IMPORTS
#==================================================
from Autodesk.Revit.DB import *

from pyrevit import revit, forms

# .NET 
import clr
clr.AddReference("System")
from System.Collections.Generic import List

from functions import f_RevitLinks

#==================================================
#VARIABLES
#==================================================
doc   = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app   = __revit__.Application

#==================================================
#FUNCTIONS
#==================================================



#==================================================
#MAIN
#==================================================

# Получение связанных файлов 
f_RevitLinks(doc, names=True)
