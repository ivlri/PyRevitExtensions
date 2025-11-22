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
from System.Collections.Generic import List
from math import fabs
from pyrevit import forms

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter
from Autodesk.Revit.Exceptions import OperationCanceledException, ArgumentOutOfRangeException

from functions._CustomSelections import CustomSelections
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

#==================================================
#FUNCTIONS
#==================================================

def vect_cur_view(view):
    v_right = active_view.RightDirection
    v_right = XYZ(fabs(v_right.X), fabs(v_right.Y), fabs(v_right.Z))
    v_up = active_view.UpDirection
    v_up = XYZ(fabs(v_up.X), fabs(v_up.Y), fabs(v_up.Z))
    return (v_right + v_up)

def get_active_ui_view(uidoc):
    doc = uidoc.Document
    view = doc.ActiveView
    uiviews = uidoc.GetOpenUIViews()
    uiview = None
    for uv in uiviews:
        if uv.ViewId.Equals(view.Id):
            uiview = uv
            break
    return uiview


def get_coordinate():
    uiview = get_active_ui_view(uidoc)
    rect = uiview.GetWindowRectangle()
    p = System.Windows.Forms.Cursor.Position
    dx = float(p.X - rect.Left) / float(rect.Right - rect.Left)
    dy = float(p.Y - rect.Bottom) / float(rect.Top - rect.Bottom)
    v_right = active_view.RightDirection
    v_right = XYZ(fabs(v_right.X), fabs(v_right.Y), fabs(v_right.Z))
    v_up = active_view.UpDirection
    v_up = XYZ(fabs(v_up.X), fabs(v_up.Y), fabs(v_up.Z))
    dxyz = dx * v_right + dy * v_up

    corners = uiview.GetZoomCorners()

    a = corners[0]
    b = corners[1]
    v = b - a

    q = a + dxyz.X * v.X * XYZ.BasisX + dxyz.Y * v.Y * XYZ.BasisY + dxyz.Z * XYZ.BasisZ * v.Z
    return q

def SignedDistanceTo(plane, p):
    v = p - plane.Origin
    return plane.Normal.DotProduct(v)

def project_onto(plane, p):
    d = SignedDistanceTo(plane, p)
    q = p - d * plane.Normal
    return q

#==================================================
#MAIN
#==================================================

with forms.WarningBar(title='Выберите текстовую аннотацию:'):
    mark = CustomSelections.pick_element_by_class(IndependentTag)
try:
    if mark:
        # Получение начальныйх данных
        el = doc.GetElement(mark.TaggedLocalElementId)
        el_category = el.Category

        middle = mark.LeaderElbow
        head = mark.TagHeadPosition
        point = mark.LeaderEnd

        plane = Plane.CreateByNormalAndOrigin(active_view.ViewDirection, active_view.Origin)
        middle = project_onto(plane, middle)
        head = project_onto(plane, head)
        point = project_onto(plane, point)

        tagget = True

        with forms.WarningBar(title='Выберите следующий элемент для привязки (Следите за положением курсора!!!):'):
            while tagget:
                tagget = CustomSelections.pick_element_by_category(el_category)
                if tagget:
                    pos = get_coordinate()
                    ref = Reference(tagget)
                    if tagget.Id == el.Id: # Проверека выбранного элемента

                        with Transaction(doc, 'Добавить выноску') as t:
                            t.Start()
                            vec = (point - middle).Normalize()
                            n_pos = project_onto(plane, pos)
                            l1 = Line.CreateUnbound(n_pos, vec)
                            l2 = Line.CreateUnbound(middle, (head - middle).Normalize())
                            inter = StrongBox[IntersectionResultArray]()
                            l1.Intersect(l2, inter)
                            new_middle = list(inter.Value)[0].XYZPoint
                            new_mark = IndependentTag.Create(doc, mark.GetTypeId(), doc.ActiveView.Id, ref, True, mark.TagOrientation, head)
                            new_mark.TagHeadPosition  = head
                            new_mark.LeaderEndCondition  = mark.LeaderEndCondition
                            new_mark.LeaderElbow = new_middle
                            # new_pos = pos - middle
                            new_mark.LeaderEnd  = pos
                            if new_mark.TagText != mark.TagText:
                                doc.Delete(new_mark.Id)
                            t.Commit()

                    else:
                        refList = List[Reference]()
                        refList.Add(ref)

                        with Transaction(doc, 'Добавить выноску марки') as t:
                            t.Start()
                            vec = (point - middle).Normalize()
                            n_pos = project_onto(plane, pos)
                            l1 = Line.CreateUnbound(n_pos, vec)
                            l2 = Line.CreateUnbound(middle, (head - middle).Normalize())
                            inter = StrongBox[IntersectionResultArray]()
                            l1.Intersect(l2, inter)
                            new_middle = list(inter.Value)[0].XYZPoint

                            mark.AddReferences(refList) # Создание марки
                            mark.SetLeaderElbow(ref, new_middle)
                            mark.SetLeaderEnd(ref, pos)
                            t.Commit()

except ArgumentOutOfRangeException as ex:
    forms.alert('Некорректно установлена точка локтя. Установите точку локтя вдоль линии полки как паказано на картинке!')

except Exception as ex:
    forms.alert(str(ex))
        
except System.ArgumentOutOfRangeException as ex:
    forms.alert('У марки отсутствуют выноски. Установите правильно начальную выноску и попробуйте еще раз.')



