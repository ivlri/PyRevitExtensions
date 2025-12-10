# -*- coding: utf-8 -*-
#==================================================
#IMPORTS
#==================================================

import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Collections")

import System
clr.AddReference("RevitAPI")
import Autodesk

clr.AddReference("RevitAPIUI")

import re
import sys
import System.Windows.Forms
from clr import StrongBox
from System.Collections.Generic import IList
from math import fabs
from pyrevit import forms

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Structure import Rebar
from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter, ObjectSnapTypes
from Autodesk.Revit.Exceptions import OperationCanceledException

from functions._CustomSelections import CustomSelections

# Добавляем логирование использования инструмента
import os
from functions._logger import ToolLogger
ToolLogger(script_path=__file__).log()

#==================================================
#VARIABLES
#==================================================

uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document
active_view = doc.ActiveView

#==================================================
#MAIN
#==================================================

with forms.WarningBar(title="1) Выберите марку по который произвести выравнивание"):     
    mark = CustomSelections.pick_element_by_class(IndependentTag, status="1) Выберите марку по который произвести выравнивание")

if mark:
    el = doc.GetElement(mark.TaggedElementId.HostElementId).Category

    try:
        middle = mark.LeaderElbow
    except:
        middle = False

    head = mark.TagHeadPosition
    point = mark.LeaderEnd
with forms.WarningBar(title="2) Выберите марки которые нужно перенести"):
    taggets = CustomSelections.pick_elements_by_class(IndependentTag, status="2) Выберите марки которые нужно перенести")

    with Transaction(doc, "Выровнять марки") as t:
        t.Start()
        for tag in taggets:
            tag.TagHeadPosition = head

            if middle:
                tag.LeaderElbow = middle
        t.Commit()
