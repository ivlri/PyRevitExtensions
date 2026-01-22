# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import *
from pyrevit import forms

def get_ref_planes_in_basepoint(doc):
    ref_planes = FilteredElementCollector(doc).OfClass(ReferencePlane).ToElements()
    west_east_plane = filter(lambda x: x.Name == "запад-восток",ref_planes)
    north_south_plane = filter(lambda x: x.Name == "север-юг",ref_planes)

    return west_east_plane, north_south_plane



def create_refplanes_in_basepoint(doc):
    doc_base_point_pos = BasePoint.GetProjectBasePoint(doc).Position

    # Генерация точек опорных плоскостей
    up_point = XYZ(doc_base_point_pos.X,doc_base_point_pos.Y + 2000/34.08,doc_base_point_pos.Z)
    down_point = XYZ(doc_base_point_pos.X,doc_base_point_pos.Y - 2000/34.08,doc_base_point_pos.Z)
    rigth_point = XYZ(doc_base_point_pos.X + 2000/34.08,doc_base_point_pos.Y,doc_base_point_pos.Z)
    left_point = XYZ(doc_base_point_pos.X - 2000/34.08,doc_base_point_pos.Y,doc_base_point_pos.Z)

    view_plane = FilteredElementCollector(doc).OfClass(ViewPlan).ToElements()[0] # Любой план надо передать в метод

    try:
        north_south= doc.Create.NewReferencePlane(up_point, down_point, XYZ.BasisZ, view_plane) # создание линии 
        north_south.Name = "север-юг"
        west_east = doc.Create.NewReferencePlane(rigth_point, left_point, XYZ.BasisZ, view_plane) # создание линии 
        west_east.Name = "запад-восток"
    except Exception as ex:
        forms.alert(ex)

    return [west_east], [north_south]


def set_sketch_plane_to_viewsection(doc):
    active_view = doc.ActiveView
    if not active_view.SketchPlane and isinstance(active_view, ViewSection):
        direction = active_view.ViewDirection # Ориентация вектора

        ref_planes = FilteredElementCollector(doc).OfClass(ReferencePlane).ToElements()
        west_east_plane = filter(lambda x: x.Name == "запад-восток",ref_planes)
        north_south_plane = filter(lambda x: x.Name == "север-юг",ref_planes)

        with Transaction(doc, "Назначить рабочую плоскость сечению") as t:
            t.Start()
            # Если не нашлись нудные плоскости их нужно создать
            try:
                if not west_east_plane or not north_south_plane: 
                    refs = create_refplanes_in_basepoint(doc)
                    west_east_plane = refs[0]
                    north_south_plane = refs[1]

                # Разрез вдоль оси X
                if abs(direction.Y) == 1: 
                    active_view.SketchPlane = SketchPlane.Create(doc, west_east_plane[0].GetPlane())

                # Разрез вдоль оси Y
                if abs(direction.X) == 1: 
                    active_view.SketchPlane = SketchPlane.Create(doc, north_south_plane[0].GetPlane())

            except Exception as ex:
                forms.alert(str(ex))
            t.Commit()