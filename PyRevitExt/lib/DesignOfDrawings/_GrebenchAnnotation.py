# -*- coding: utf-8 -*-
__title__   = "Гребенчатая"
__doc__ = """Описание:
Добавляет текстовую выноску по указанной точке сохраняя угол наклона в локте. 
"""
#==================================================
#IMPORTS
#==================================================

import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Collections")

import System

from functions._CustomSelections import CustomSelections
from clr import StrongBox
from System.Collections.Generic import IList
from math import fabs
from pyrevit import forms

from Autodesk.Revit.DB import *

from Autodesk.Revit.DB import Category, BuiltInCategory
from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter, ObjectSnapTypes
from Autodesk.Revit.Exceptions import OperationCanceledException, ArgumentOutOfRangeException

from functions._sketch_plane import set_sketch_plane_to_viewsection


#==================================================
#MAIN
#==================================================
def start():
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

    def vect_cur_view(view):
        v_right = active_view.RightDirection
        v_right = XYZ(fabs(v_right.X), fabs(v_right.Y), fabs(v_right.Z))
        v_up = active_view.UpDirection
        v_up = XYZ(fabs(v_up.X), fabs(v_up.Y), fabs(v_up.Z))
        return (v_right + v_up)

    def SignedDistanceTo(plane, p):
        v = p - plane.Origin
        return plane.Normal.DotProduct(v)

    def project_onto(plane, p):
        d = SignedDistanceTo(plane, p)
        q = p - d * plane.Normal
        return q

    def concat_XYZ(xyz):
        x = str(xyz.X)
        y = str(xyz.Y)
        z = str(xyz.Z)
        return x+y+z


    set_sketch_plane_to_viewsection(doc)
    try:
        mark = CustomSelections.pick_element_by_class(AnnotationSymbol)
        if mark:
            leader = mark.GetLeaders()[0]
            middle = leader.Elbow
            head = leader.Anchor
            point = leader.End

        if mark:
            plane = Plane.CreateByNormalAndOrigin(active_view.ViewDirection, active_view.Origin)

            middle = project_onto(plane, middle)
            head = project_onto(plane, head)
            point = project_onto(plane, point)

            concat_leaders_end = [concat_XYZ(i.End) for i in mark.GetLeaders()]

            while True:
                try:
                    with Transaction(doc, 'Добавить выноску') as t:
                        t.Start()
                        try:
                            selected_point = selection.PickPoint(ObjectSnapTypes.Intersections)

                            vec = (point - middle).Normalize()
                            new_selected_point = project_onto(plane, selected_point)
                            l1 = Line.CreateUnbound(new_selected_point, vec)
                            l2 = Line.CreateUnbound(middle, (head - middle).Normalize())
                            inter = StrongBox[IntersectionResultArray]()
                            l1.Intersect(l2, inter)

                            new_middle = list(inter.Value)[0].XYZPoint

                            added_leader = mark.addLeader()
                            new_leaders = [i for i in mark.GetLeaders()]
                            new_leader = new_leaders[-1]

                            new_leader.End = selected_point 
                            new_leader.Elbow = new_middle
                            #new_leader.End  = selected_point
                        except OperationCanceledException:
                            break
                        t.Commit()

                except ArgumentOutOfRangeException as ex:
                    forms.alert('Некорректно установлена точка локтя. Установите точку локтя вдоль линии полки как паказано на картинке!')
                    break

                except Exception as ex:
                    forms.alert(str(ex))
                    break
                
    except System.ArgumentOutOfRangeException as ex:
        forms.alert('У марки отсутствуют выноски. Установите правильно начальную выноску и попробуйте еще раз.')




