# -*- coding: utf-8 -*- 
__title__ = 'Открыть вид'
from pyrevit import revit
from functions._CustomSelections import CustomSelections
from pyrevit import forms

from Autodesk.Revit.DB import Viewport

doc = revit.doc
uidoc = revit.uidoc

with forms.WarningBar(title='Выберите видовой экран:'):
    sel = CustomSelections.pick_element_by_class(Viewport)
    uidoc.ActiveView = doc.GetElement(sel.ViewId)

