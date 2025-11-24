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


#==================================================
#MAIN
#==================================================

set_sketch_plane_to_viewsection(doc)
try:
    with forms.WarningBar(title='Выберите текстовую аннотацию:'):
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

        with forms.WarningBar(title='Укажите точку сноски:'):
            vec = (point - middle).Normalize()
            head_vec = (head - middle).Normalize()
            l2 = Line.CreateUnbound(middle, head_vec)
    
            while True:
                try:
                    with Transaction(doc, 'Добавить выноску') as t:
                        t.Start()
                        selected_point = selection.PickPoint(ObjectSnapTypes.None)

                        vec = (point - middle).Normalize()
                        new_selected_point = project_onto(plane, selected_point)
                        l1 = Line.CreateUnbound(new_selected_point, vec)
                        l2 = Line.CreateUnbound(middle, (head - middle).Normalize())
                        inter = StrongBox[IntersectionResultArray]()
                        l1.Intersect(l2, inter)

                        new_middle = list(inter.Value)[0].XYZPoint

                        new_leader = mark.addLeader()
                        # new_leaders = [i for i in mark.GetLeaders()]
                        new_leader = list(mark.GetLeaders())[-1]

                        new_leader.End = selected_point 
                        new_leader.Elbow = new_middle

                        t.Commit()
                except OperationCanceledException:
                    break

                except ArgumentOutOfRangeException as ex:
                    forms.alert('Некорректно установлена точка локтя. Установите точку локтя вдоль линии полки как паказано на картинке!')
                    break
            
        
except System.ArgumentOutOfRangeException as ex:
    forms.alert('У марки отсутствуют выноски. Установите правильно начальную выноску и попробуйте еще раз.')




# # -*- coding: utf-8 -*-
# __title__ = "Гребенчатая (оптимизированная)"
# __doc__ = """Добавляет текстовую выноску по указанной точке, сохраняя угол наклона."""

# import clr
# clr.AddReference("System.Windows.Forms")
# clr.AddReference("System.Collections")

# from clr import StrongBox
# from Autodesk.Revit.DB import *
# from Autodesk.Revit.UI.Selection import ObjectSnapTypes
# from Autodesk.Revit.Exceptions import OperationCanceledException, ArgumentOutOfRangeException
# from pyrevit import forms
# from functions._CustomSelections import CustomSelections
# from functions._sketch_plane import set_sketch_plane_to_viewsection
# from functions._logger import ToolLogger
# import System

# # Логирование использования
# ToolLogger(script_path=__file__).log()

# #==================================================
# # VARIABLES
# #==================================================

# uidoc = __revit__.ActiveUIDocument
# doc = uidoc.Document
# active_view = doc.ActiveView
# selection = uidoc.Selection

# #==================================================
# # UTILS
# #==================================================

# def project_onto_plane(plane, p):
#     """Проекция точки на плоскость."""
#     v = p - plane.Origin
#     return p - plane.Normal.DotProduct(v) * plane.Normal

# #==================================================
# # MAIN
# #==================================================

# set_sketch_plane_to_viewsection(doc)

# try:
#     with forms.WarningBar(title='Выберите текстовую аннотацию:'):
#         mark = CustomSelections.pick_element_by_class(AnnotationSymbol)
#     if not mark:
#         raise OperationCanceledException()

#     # --- Кэшируем нужные данные ---
#     leader = mark.GetLeaders()[0]
#     middle, head, point = leader.Elbow, leader.Anchor, leader.End

#     plane = Plane.CreateByNormalAndOrigin(active_view.ViewDirection, active_view.Origin)
#     # Предварительно проецируем точки на плоскость
#     middle = project_onto_plane(plane, middle)
#     head = project_onto_plane(plane, head)
#     point = project_onto_plane(plane, point)

#     # Предвычисляем нормализованные векторы
#     vec = (point - middle).Normalize()
#     head_vec = (head - middle).Normalize()

#     # Линия для пересечения
#     l2 = Line.CreateUnbound(middle, head_vec)

#     with forms.WarningBar(title='Укажите точку сноски:'):
#         while True:
#             try:
#                 selected_point = selection.PickPoint(ObjectSnapTypes.None)
#             except OperationCanceledException:
#                 break

#             new_selected_point = project_onto_plane(plane, selected_point)
#             l1 = Line.CreateUnbound(new_selected_point, vec)

#             inter = StrongBox[IntersectionResultArray]()
#             if l1.Intersect(l2, inter) != SetComparisonResult.Overlap:
#                 forms.alert('Не удалось вычислить пересечение. Попробуйте снова.')
#                 continue

#             new_middle = list(inter.Value)[0].XYZPoint

#             try:
#                 with Transaction(doc, 'Добавить выноску') as t:
#                     t.Start()
#                     new_leader = mark.addLeader()
#                     new_leader = list(mark.GetLeaders())[-1]
#                     new_leader.End = selected_point
#                     new_leader.Elbow = new_middle
#                     t.Commit()
#             except ArgumentOutOfRangeException:
#                 forms.alert('Некорректно установлена точка локтя. Установите вдоль линии полки!')
#                 break

# except System.ArgumentOutOfRangeException:
#     forms.alert('У марки отсутствуют выноски. Добавьте первую выноску и попробуйте снова.')
