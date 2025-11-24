
# -*- coding: utf-8 -*-
__title__   = "Поворот\nаннотаций"
__doc__ = """Описание:

Используется для оформления типовых секций с поворотом в одном файле. 
После оформления исходного вида -> этот вид копируется и поворачивается на нужный угол -> после запуска, 
скрипт определит этот угол и проведет поворот всех аннотаций, для которых это технически возможно.
"""
#==================================================
#IMPORTS
#==================================================

import os
import codecs
import time
import math

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from Autodesk.Revit.Exceptions import InvalidOperationException

# .NET Imports
import clr
clr.AddReference("System")
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Collections")
import System
from System.Collections.Generic import List
import System.Windows.Forms

from pyrevit import forms
from pyrevit import revit, DB, UI
from pyrevit.forms import ProgressBar
from functions._CustomSelections import CustomSelections

#==================================================
#VARIABLES
#==================================================

doc = revit.doc
uidoc = __revit__.ActiveUIDocument
active_view = doc.ActiveView
app = __revit__.Application

#==================================================
#DEFS
#==================================================
def GetBBox(el, doc):
    bounding_box = el.get_BoundingBox(doc.ActiveView)
    min_point = bounding_box.Min
    max_point = bounding_box.Max

    center_x = (min_point.X + max_point.X) / 2
    center_y = (min_point.Y + max_point.Y) / 2
    center_z = (min_point.Z + max_point.Z) / 2

    return XYZ(center_x, center_y, center_z)


def GetAngle(view):
    uv_X = view.RightDirection
    uv_Y = view.UpDirection

    basis_X = XYZ.BasisX
    basis_Y = XYZ.BasisY

    if basis_X.IsAlmostEqualTo(uv_Y):
        return (-math.pi/2)
    else: 
        return basis_X.AngleTo(uv_X)


def SwitchGridExtent(doc, view, ang):
    all_grids = FilteredElementCollector(doc, view.Id).OfClass(Grid).ToElements()
    if all_grids:
        #all_grids = filter(lambda x: "8мм" in x.LookupParameter("Тип").AsValueString(), all_grids)

        def SetDatumExtent(uv_grids, desired_type):
            ds_t = DatumExtentType.Model if desired_type == "3d" else DatumExtentType.ViewSpecific
            for grid in uv_grids:
                grid.SetDatumExtentType(DatumEnds.End0,view, ds_t)
                grid.SetDatumExtentType(DatumEnds.End1,view, ds_t)          

        uv_grids_X = filter(lambda x: abs(x.Curve.Direction.X) == abs(1), all_grids)

        uv_grids_Y = filter(lambda x: abs(x.Curve.Direction.Y) == abs(1), all_grids)

        angle_degrees = round(math.degrees(ang))

        # Предполагается что все оси обозначены с одной стороны и никто не смещал 3D расположение
        """Сброс 2d и перенос обозначения на другую сторону"""
        if angle_degrees == float(90): # Поворот на 90
            
            SetDatumExtent(uv_grids_X, "3d")
            SetDatumExtent(uv_grids_X, "2d")
            for uv_grid in uv_grids_X:
                uv_grid.HideBubbleInView(DatumEnds.End0, view)
                uv_grid.ShowBubbleInView(DatumEnds.End1, view)

            uv_bbox = view.Outline

        elif angle_degrees == float(180):# Поворот на 180

            SetDatumExtent(uv_grids_Y, "3d")
            SetDatumExtent(uv_grids_Y, "2d")
            for uv_grid in uv_grids_Y:
                uv_grid.HideBubbleInView(DatumEnds.End0, view)
                uv_grid.ShowBubbleInView(DatumEnds.End1, view)

            SetDatumExtent(uv_grids_X, "3d")
            SetDatumExtent(uv_grids_X, "2d")
            for uv_grid in uv_grids_X:
                uv_grid.HideBubbleInView(DatumEnds.End0, view)
                uv_grid.ShowBubbleInView(DatumEnds.End1, view)         

        elif angle_degrees == float(-90): # Поворот на -90

            SetDatumExtent(uv_grids_Y, "3d")
            SetDatumExtent(uv_grids_Y, "2d")
            for uv_grid in uv_grids_Y:
                uv_grid.HideBubbleInView(DatumEnds.End0, view)
                uv_grid.ShowBubbleInView(DatumEnds.End1, view)
 

def RotateGenericAnnotation(doc, ang):
    gen_anatations = FilteredElementCollector(doc, active_view.Id).OfCategory(BuiltInCategory.OST_GenericAnnotation).ToElements()

    for gen_anatation in gen_anatations:
        
        # Если есть leader
        try:
            start_leader_end = gen_anatation.GetLeaders()[0].End
            trans=gen_anatation.GetTotalTransform()
            loc = trans.Origin
            #rot = -trans.BasisX.AngleOnPlaneTo(XYZ.BasisX, XYZ.BasisZ)
            line = Line.CreateBound(loc, XYZ(loc.X,loc.Y,loc.Z+1))
            
            ElementTransformUtils.RotateElement(doc, gen_anatation.Id, line, ang)
            gen_anatation.GetLeaders()[0].End = start_leader_end
        
        # Если нет leader
        except:
            rotation_point = GetBBox(gen_anatation, doc)

            ElementTransformUtils.RotateElement(doc, 
                        gen_anatation.Id, 
                        Line.CreateBound(rotation_point,rotation_point + XYZ.BasisZ), 
                        ang)


def RorateDetailComponents(doc, ang):
    try:
        angle_degrees = round(math.degrees(ang))
        DetailComponents = FilteredElementCollector(doc, active_view.Id).OfCategory(BuiltInCategory.OST_DetailComponents).ToElements()
        DetailComponents_for_flip = filter(lambda x: "Обрыв_Л" not in x.LookupParameter("Семейство").AsValueString(),
                                        DetailComponents)
        
        if angle_degrees == float(180):
            [i.flipFacing() for i in DetailComponents_for_flip]

            #Поворот обозначения провемов(Только при 180)
            DetailComponents = FilteredElementCollector(doc, active_view.Id).OfCategory(BuiltInCategory.OST_DetailComponents).ToElements()
            DCHole_DetailComponents = filter(lambda x: "ЭУ_Проем_" in x.LookupParameter("Семейство").AsValueString(),DetailComponents_for_flip)

            for DCHole_DetailComponent in DCHole_DetailComponents:

                rotation_point = GetBBox(DCHole_DetailComponent, doc)

                ElementTransformUtils.RotateElement(doc, 
                            DCHole_DetailComponent.Id, 
                            Line.CreateBound(rotation_point,rotation_point + XYZ.BasisZ), 
                            ang)
                
        # Поворт фрагментов узла
        fragment_DetailComponents = filter(lambda x: "Узел_Фрагмент" in x.LookupParameter("Семейство").AsValueString(),DetailComponents_for_flip)
        if fragment_DetailComponents:
                for fragment_node in fragment_DetailComponents:
                    fragment_node.flipHand()
                    if ang != math.pi:
                        coord_rotate = XYZ(
                            fragment_node.Location.Point.X,
                            fragment_node.Location.Point.Y + fragment_node.LookupParameter("Высота").AsDouble()/2,
                            fragment_node.Location.Point.Z)
                    else:
                        coord_rotate = fragment_node.Location.Point      

                    ElementTransformUtils.RotateElement(
                        doc, 
                        fragment_node.Id, 
                        Line.CreateBound(coord_rotate,coord_rotate + XYZ.BasisZ), 
                        ang)
    except Exception as ex:
        pass

# Принудительный сброс локтя марок и поворот марок перемычек при повороте на 90
def ChangeTags(doc, view, ang):
    angle_degrees = round(math.degrees(ang))

    # SwitchTagElbow
    if angle_degrees == float(90) or angle_degrees == float(-90):
        tags = FilteredElementCollector(doc, view.Id).OfClass(IndependentTag).ToElements()
        f_tags = filter(lambda x: x.HasLeader,tags)

        if f_tags:
            for tag in f_tags:
                try:
                    tag.LeaderEndCondition = LeaderEndCondition.Free
                    tag.HasLeader = False
                    tag.HasLeader = True
                except InvalidOperationException:
                    continue

        # Принудительный поворот морок перемычек
        constr_tags = filter(lambda x: "Марка_Перемычка" in x.LookupParameter("Семейство").AsValueString(),tags)
        if constr_tags:
            for tag in constr_tags:
                    if tag.TagOrientation == TagOrientation.Horizontal:
                        tag.TagOrientation = TagOrientation.Vertical
                    elif tag.TagOrientation == TagOrientation.Vertical:
                        tag.TagOrientation = TagOrientation.Horizontal


def RegenSpotDimentions(doc,view,ang):
    angle_degrees = round(math.degrees(ang))

    sp_dims = FilteredElementCollector(doc, view.Id).OfClass(SpotDimension).ToElements()


    # Получение данных
    for sp_dim in sp_dims: 

        try:
            origin = sp_dim.Origin
            txt_pos = sp_dim.TextPosition
            shouler_pos = sp_dim.LeaderShoulderPosition

            if angle_degrees == float(180):# Поворот на 180 
                sp_dim.LeaderHasShoulder = False
                sp_dim.LeaderHasShoulder = True
                # Обработка отметок
                if txt_pos.Y > origin.Y and "Вверх" in sp_dim.LookupParameter("Тип").AsValueString():
                    sp_dim.LeaderShoulderPosition = XYZ(shouler_pos.X,
                                                        origin.Y - 1,
                                                        shouler_pos.Z)

                elif txt_pos.Y < origin.Y and "Вниз" in sp_dim.LookupParameter("Тип").AsValueString():
                    sp_dim.LeaderShoulderPosition = XYZ(shouler_pos.X,
                                                        origin.Y + 1,
                                                        shouler_pos.Z)
                    
            elif angle_degrees == float(90):# Поворот на 90
                # Обработка отметок
                if txt_pos.Y > origin.Y and "Вверх" in sp_dim.LookupParameter("Тип").AsValueString():
                    sp_dim.LeaderShoulderPosition = XYZ(origin.X - 1,
                                                        shouler_pos.Y,
                                                        shouler_pos.Z)

                elif txt_pos.Y < origin.Y and "Вниз" in sp_dim.LookupParameter("Тип").AsValueString():
                    sp_dim.LeaderShoulderPosition = XYZ(origin.X + 1,
                                                        shouler_pos.Y,
                                                        shouler_pos.Z)
                    
            elif angle_degrees == float(-90):# Поворот на -90
                # Обработка отметок
                if txt_pos.Y > origin.Y and "Вверх" in sp_dim.LookupParameter("Тип").AsValueString():
                    sp_dim.LeaderShoulderPosition = XYZ(origin.X + 1,
                                                        shouler_pos.Y,
                                                        shouler_pos.Z)

                elif txt_pos.Y < origin.Y and "Вниз" in sp_dim.LookupParameter("Тип").AsValueString():
                    sp_dim.LeaderShoulderPosition = XYZ(origin.X - 1,
                                                        shouler_pos.Y,
                                                        shouler_pos.Z)
        except Exception as ex:
            continue


def ChangeCropBox(view,ang):
    crop_box = view.CropBox
    max_point = crop_box.Max
    min_point = crop_box.Min

    a = max_point.Y - min_point.Y # длина
    b = max_point.X - min_point.X# ширина

    angle_degrees = round(math.degrees(ang))

    delta = a - b # разница
    
    new_box = BoundingBoxXYZ()
    
    if (angle_degrees == float(90) or angle_degrees == float(-90)) and a>b:# Поворот на 90
 
        new_box.Min = XYZ(min_point.X - delta, min_point.Y, min_point.Z)
        new_box.Max = XYZ(max_point.X + delta, max_point.Y, max_point.Z)

        view.CropBox = new_box
 
    elif (angle_degrees == float(90) or angle_degrees == float(-90)) and a<b:# Поворот на 90

        new_box.Min = XYZ(min_point.X, min_point.Y + delta, min_point.Z)
        new_box.Max = XYZ(max_point.X, max_point.Y - delta, max_point.Z)

        view.CropBox = new_box

#==================================================
#MAIN
#==================================================

def start_hook():
    angle = GetAngle(active_view)
    with Transaction(doc, "Автоповорот аннотаций") as t:
        t.Start()
        ChangeCropBox(active_view, angle)
        RotateGenericAnnotation(doc, angle)
        RorateDetailComponents(doc, angle)
        SwitchGridExtent(doc, active_view, angle)
        ChangeTags(doc, active_view, angle)
        RegenSpotDimentions(doc, active_view, angle)
        t.Commit()

start_hook()
