# -*- coding: utf-8 -*-
__title__   = "Мультианотация"
__doc__ = """Описание:
Добавляет текстовую выноску по указанной точке
"""
#==================================================
#IMPORTS
#==================================================

import sys
import System
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ISelectionFilter, Selection, ObjectType, ObjectSnapTypes
from Autodesk.Revit.Exceptions import OperationCanceledException
from pyrevit import forms

from functions._CustomSelections import CustomSelections
from functions._sketch_plane import set_sketch_plane_to_viewsection

#==================================================
#VARIABLES
#==================================================

uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document
active_view = doc.ActiveView
selection = uidoc.Selection  

#==================================================
#FUNCTIONS
#==================================================

def concat_XYZ(xyz):
    x = str(xyz.X)
    y = str(xyz.Y)
    z = str(xyz.Z)
    return x+y+z

def approximate_gostcommon_string_width(st):
    if len(st) == 0:
        size = 1
    else:
        size = 0
        
    for s in st:
        if s:
            if s in 'qwertyuiuopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNMйцукенгшщзхъфывапролджэячсмитьёЁЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬ1234567890-=+#$^&*?/~"№': size += 2
            elif s in  ';:,.`()[]{}!': size += 1
            elif s in  "'": size += 1
        else: 
            size = 1
    return size

#==================================================
#MAIN
#==================================================

set_sketch_plane_to_viewsection(doc)

with forms.WarningBar(title='Выберите марку:'):
    mark = CustomSelections.pick_element_by_class(AnnotationSymbol)

if mark:
    with forms.WarningBar(title='Выберите точку на виде.:'):
        while True:
            try:
                with Transaction(doc, 'Добавить выноску') as t:
                    t.Start()
                    selected_pt = selection.PickPoint(ObjectSnapTypes.Intersections)

                    mark.addLeader()
                    new_leaders = [i for i in mark.GetLeaders()]
                    new_leaders[-1].End = selected_pt
                    t.Commit()
            except OperationCanceledException:
                break

            except Exception as ex:
                forms.alert(str(ex))
                break
            finally: 1==1

