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

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Structure import Rebar
from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter, ObjectSnapTypes
from Autodesk.Revit.Exceptions import OperationCanceledException

from functions._CustomSelections import CustomSelections


#==================================================
#FUNCTIONS
#==================================================



#==================================================
#MAIN
#==================================================

#set_sketch_plane_to_viewsection(doc)
def start():
    uidoc = __revit__.ActiveUIDocument
    doc = uidoc.Document
    active_view = doc.ActiveView
    
    def concat_XYZ(xyz):
        x = str(xyz.X)
        y = str(xyz.Y)
        z = str(xyz.Z)
        return x+y+z


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
    
    mark = CustomSelections.pick_element_by_class(IndependentTag)

    if mark:
        # Получение начальныйх данных
        el = doc.GetElement(mark.TaggedLocalElementId)
        el_category = el.Category

        try:
            elbow_loc = mark.LeaderElbow
        except:
            elbow_loc = False

        head = mark.TagHeadPosition
        leader_end = mark.LeaderEnd

        tagget = True
        # Если таргет is Rebar
        while tagget:
            tagget = CustomSelections.pick_element_by_category(el_category)

            if tagget:
                if tagget.Id == el.Id: # Проверека выбранного элемента
                    pos = get_coordinate()
                    ref = Reference(tagget)

                    with Transaction(doc, 'Добавить выноску марки') as t:
                        t.Start()
                        new_mark = IndependentTag.Create(doc, mark.GetTypeId(), doc.ActiveView.Id, ref, True, mark.TagOrientation, pos)
                        
                        new_mark.TagHeadPosition  = head
                        new_mark.LeaderEndCondition  = mark.LeaderEndCondition
                        new_mark.LeaderEnd  = pos

                        if elbow_loc:
                            new_mark.LeaderElbow = elbow_loc

                        if new_mark.TagText != mark.TagText:
                            doc.Delete(new_mark.Id)
                        t.Commit()
                else:# Все остальные таргеты
                    #pos = get_coordinate()
                    ref = Reference(tagget)
                    refList = List[Reference]()
                    refList.Add(ref)

                    with Transaction(doc, 'Добавить выноску марки') as t:
                        t.Start()
                        mark.AddReferences(refList) # Создание марки
                        if elbow_loc:
                            mark.SetLeaderElbow(ref, elbow_loc)
                        t.Commit()




    # # Если таргет is Rebar
    # if isinstance(el, Rebar):
    #     while tagget:
    #         tagget = CustomSelections.pick_element_by_category(el_category)

    #         if tagget:
    #             pos = get_coordinate()
    #             ref = Reference(tagget)

    #             with Transaction(doc, 'Добавить выноску марки') as t:
    #                 t.Start()
    #                 new_mark = IndependentTag.Create(doc, mark.GetTypeId(), doc.ActiveView.Id, ref, True, mark.TagOrientation, pos)
                    
    #                 new_mark.TagHeadPosition  = head
    #                 new_mark.LeaderEndCondition  = mark.LeaderEndCondition
    #                 new_mark.LeaderEnd  = pos

    #                 if elbow_loc:
    #                     new_mark.LeaderElbow = elbow_loc

    #                 if new_mark.TagText != mark.TagText:
    #                     doc.Delete(new_mark.Id)
    #                 t.Commit()
    # else:# Все остальные таргеты
    #     while tagget:
    #         # try:
    #         tagget = CustomSelections.pick_element_by_category(el_category)
    #         if tagget:
    #             #pos = get_coordinate()
    #             ref = Reference(tagget)
    #             refList = List[Reference]()
    #             refList.Add(ref)

    #             with Transaction(doc, 'Добавить выноску марки') as t:
    #                 t.Start()
    #                 mark.AddReferences(refList) # Создание марки
    #                 if elbow_loc:
    #                     mark.SetLeaderElbow(ref, elbow_loc)
    #                 t.Commit()

    #         # except OperationCanceledException:
    #         #     break
    #         # except Exception as ex:
    #         #     print(ex)
    #         #     break


        
