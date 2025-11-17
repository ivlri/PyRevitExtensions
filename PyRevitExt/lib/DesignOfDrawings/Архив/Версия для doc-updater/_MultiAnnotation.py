# -*- coding: utf-8 -*-
__title__   = "Мультианотация"
__doc__ = """Описание:
Добавляет текстовую выноску по указанной точке
"""
#==================================================
#IMPORTS
#==================================================

import sys

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ISelectionFilter, Selection, ObjectType, ObjectSnapTypes
from Autodesk.Revit.Exceptions import OperationCanceledException
from pyrevit import forms

from functions._CustomSelections import CustomSelections
from functions._sketch_plane import set_sketch_plane_to_viewsection

#==================================================
#VARIABLES
#==================================================

 

#==================================================
#FUNCTIONS
#==================================================

def concat_XYZ(xyz):
    x = str(xyz.X)
    y = str(xyz.Y)
    z = str(xyz.Z)
    return x+y+z

#==================================================
#MAIN
#==================================================
def start():
    uidoc = __revit__.ActiveUIDocument
    doc = uidoc.Document
    active_view = doc.ActiveView
    selection = uidoc.Selection  
    
    set_sketch_plane_to_viewsection(doc)

    mark = CustomSelections.pick_element_by_class(AnnotationSymbol)

    if mark:
        concat_leaders_end = [concat_XYZ(i.End) for i in mark.GetLeaders()]
        while True:
            try:
                with Transaction(doc, 'Добавить выноску') as t:
                    t.Start()
                    selected_pt = selection.PickPoint(ObjectSnapTypes.Intersections)
                    added_leader = mark.addLeader()
                    new_leaders = [i for i in mark.GetLeaders()]
                    new_leaders[-1].End = selected_pt
                    t.Commit()
            except OperationCanceledException:
                break

            except Exception as ex:
                forms.alert(str(ex))
                break

