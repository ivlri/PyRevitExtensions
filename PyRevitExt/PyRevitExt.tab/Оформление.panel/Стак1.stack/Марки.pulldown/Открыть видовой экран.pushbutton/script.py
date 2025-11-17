# -*- coding: utf-8 -*- 
__title__ = 'Открыть вид'
from pyrevit import revit
from functions._CustomSelections import CustomSelections
from pyrevit import forms

from Autodesk.Revit.DB import Viewport

# Добавляем логирование использования инструмента
import os
from functions._logger import ToolLogger
ToolLogger(script_path=__file__).log()

doc = revit.doc
uidoc = revit.uidoc

with forms.WarningBar(title='Выберите видовой экран:'):
    sel = CustomSelections.pick_element_by_class(Viewport)
    uidoc.ActiveView = doc.GetElement(sel.ViewId)

