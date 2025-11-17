# -*- coding: utf-8 -*-
#==================================================
#⬇️ IMPORTS
#==================================================

import os
import codecs
import math

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from Autodesk.Revit.Exceptions import InvalidOperationException

# .NET Imports
from System.Collections.Generic import List
import System.Windows.Forms

from pyrevit import forms
from pyrevit import revit, DB, UI
from pyrevit.forms import ProgressBar


#==================================================
#📦 VARIABLES
#==================================================

sender = __eventsender__  # UIApplication
args = __eventargs__      # Autodesk.Revit.UI.Events.BeforeExecutedEventArgs

doc = revit.doc
#uidoc = __revit__.ActiveUIDocument
active_view = doc.ActiveView

#==================================================
#Defs
#==================================================


def GetAngle(view):
    uv_X = view.RightDirection
    uv_Y = view.UpDirection

    basis_X = XYZ.BasisX
    basis_Y = XYZ.BasisY

    if basis_X.IsAlmostEqualTo(uv_Y):
        return (-math.pi/2)
    else: 
        return basis_X.AngleTo(uv_X)


def SwitchGridExtent(doc, ang, view):
    all_grids = FilteredElementCollector(doc, view.Id).OfClass(Grid).ToElements()
    if all_grids:
        #all_grids = filter(lambda x: "8мм" in x.LookupParameter("Тип").AsValueString(), all_grids)

        def SetDatumExtent(uv_grids, desired_type):
            ds_t = DatumExtentType.Model if desired_type == "3d" else DatumExtentType.ViewSpecific
            for grid in uv_grids:
                grid.SetDatumExtentType(DatumEnds.End0,view, ds_t)
                grid.SetDatumExtentType(DatumEnds.End1,view, ds_t)          

        def ShowHideBubbles(uv_grids, angle_degrees):
            for uv_grid in uv_grids:
                uv_grid.HideBubbleInView(DatumEnds.End0, view)
                uv_grid.ShowBubbleInView(DatumEnds.End1, view)


        uv_grids_X = filter(lambda x: abs(x.Curve.Direction.X) == abs(1), all_grids)
        #forms.alert('\n'.join([a.Name for a in uv_grids_X]))
        uv_grids_Y = filter(lambda x: abs(x.Curve.Direction.Y) == abs(1), all_grids)

        angle_degrees = round(math.degrees(ang))

        # Предполагается что все оси обозначены с одной стороны и никто не смещал 3D расположение
        if angle_degrees == float(90): # Поворот на 90
            
            SetDatumExtent(uv_grids_X, "3d")
            SetDatumExtent(uv_grids_X, "2d")
            for uv_grid in uv_grids_X:
                uv_grid.HideBubbleInView(DatumEnds.End0, view)
                uv_grid.ShowBubbleInView(DatumEnds.End1, view)

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
        start_leader_end = gen_anatation.GetLeaders()[0].End
        trans=gen_anatation.GetTotalTransform()
        loc = trans.Origin
        rot = -trans.BasisX.AngleOnPlaneTo(XYZ.BasisX, XYZ.BasisZ)
        line = Line.CreateBound(loc, XYZ(loc.X,loc.Y,loc.Z+1))
        
        #Set Rotation
        ElementTransformUtils.RotateElement(doc, gen_anatation.Id, line, ang)
        gen_anatation.GetLeaders()[0].End = start_leader_end

        #new_els.append(gen_anatation)
  
  
def RorateDetailComponents(doc, ang):
    DetailComponents = FilteredElementCollector(doc, active_view.Id).OfCategory(BuiltInCategory.OST_DetailComponents).ToElements()
    DetailComponents_for_flip = filter(lambda x: "Обрыв_Л" not in x.LookupParameter("Семейство").AsValueString(),
                                       DetailComponents)
    
    if round(math.degrees(ang)) == float(180):
        [i.flipFacing() for i in DetailComponents_for_flip]
        
    # Поворт фрагментов узла
    fragment_DetailComponents = filter(lambda x: "Узел_Фрагмент" in x.LookupParameter("Семейство").AsValueString(),DetailComponents)
    if fragment_DetailComponents:
        try:
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


    # #Поворот обозначения провемов
    # DCHole_DetailComponents = filter(lambda x: "ЭУ_Проем_Прям" in x.LookupParameter("Семейство").AsValueString(),DetailComponents)
    # for DCHole_DetailComponent in DCHole_DetailComponents:
    #     loc = DCHole_DetailComponent.Location
    #     ElementTransformUtils.RotateElement(doc, 
    #                 DCHole_DetailComponent.Id, 
    #                 Line.CreateBound(loc.Point,loc.Point + XYZ.BasisZ), 
    #                 ang)
        

def SwitchTagElbow(doc, view, ang):
    tags = FilteredElementCollector(doc, view.Id).OfClass(IndependentTag).ToElements()
    
    f_tags = filter(lambda x: x.HasLeader,tags)
    # SwitchTagElbow
    if f_tags:
        for tag in f_tags:
            try:
                tag.LeaderEndCondition = LeaderEndCondition.Free
                tag.HasLeader = False
                tag.HasLeader = True
            except InvalidOperationException:
                continue

    # Принудительный поворот морок перемычек
    angle_degrees = round(math.degrees(ang))
    constr_tags = filter(lambda x: "Марка_Перемычка" in x.LookupParameter("Семейство").AsValueString(),tags)

    for tag in constr_tags:
        if angle_degrees == float(90) or angle_degrees == float(-90):
            if tag.TagOrientation == TagOrientation.Horizontal:
                tag.TagOrientation = TagOrientation.Vertical
            elif tag.TagOrientation == TagOrientation.Vertical:
                tag.TagOrientation = TagOrientation.Horizontal


#==================================================
#MAIN
#==================================================

# def start_hook():
angle = GetAngle(active_view)
with Transaction(doc, "Автоповорот аннотаций") as t:
    t.Start()
    RotateGenericAnnotation(doc, angle)
    RorateDetailComponents(doc, angle)
    SwitchGridExtent(doc, angle, active_view)
    SwitchTagElbow(doc, active_view, angle)
    t.Commit()
