# -*- coding: utf-8 -*-
__title__   = "Флажок"
__doc__ = """Описание:
Создает 2D семейство флажок по 2-м точкам на активном виде.
"""
#==================================================
#IMPORTS
#==================================================

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ISelectionFilter, Selection, ObjectType, ObjectSnapTypes
from Autodesk.Revit.Exceptions import OperationCanceledException

from functions._CustomSelections import CustomSelections
from functions._sketch_plane import set_sketch_plane_to_viewsection, get_ref_planes_in_basepoint

from pyrevit import forms

#==================================================
#VARIABLES
#==================================================

doc   = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app   = __revit__.Application
active_view = doc.ActiveView
selection = uidoc.Selection   
scale_views = float(active_view.LookupParameter("Масштаб вида").AsInteger())

#==================================================
#Func
#==================================================

#==================================================
#MAIN
#==================================================
set_sketch_plane_to_viewsection(doc)

direction = active_view.ViewDirection # Ориентация вида



famly_symbols = FilteredElementCollector(doc).OfClass(FamilySymbol).ToElements()
fe_symbol = filter(lambda x: x.FamilyName == "PS_ФлажокПирогаКонструкции", famly_symbols)

if not fe_symbol:
    forms.alert('Загрузите семейство PS_ФлажокПирогаКонструкции отметка или исправите дубли семейства')
else:
    fe_symbol = fe_symbol[0]
    while True:
        try: 
            with forms.WarningBar(title='1) Выберете точку начала выноски:'):
                point1 = selection.PickPoint(ObjectSnapTypes.Intersections)

            with forms.WarningBar(title='2) Выберете точку рсположения отметки:'):
                pt2 = selection.PickPoint(ObjectSnapTypes.Intersections)

            vec = (pt2 - point1).Normalize()
            how_point = False

            if isinstance(active_view, ViewSection):
                # ------ Разрез перпендикулярно Y ------
                if abs(direction.Y) == 1:
                    #Выравниванеи по оси
                    if abs(vec.X) > abs(vec.Z): # By Y
                        point2 = XYZ(pt2.X,point1.Y,point1.Z)
                        leng = abs(point2.X - point1.X)
                        
                        print((point1 - point2).Normalize(), direction)
                        
                        if direction.Y == float(-1):
                            if (point1 - point2).Normalize().X == 1:
                                left_rigth = 1
                                loc_leader = 1
                                check = True
                                how_point = "-X"
                            else:
                                left_rigth = 0
                                loc_leader = 0
                                check = False
                        else:
                            if (point1 - point2).Normalize().X == 1:
                                left_rigth = 0
                                loc_leader = 0
                                check = False
                            else:
                                left_rigth = 1
                                loc_leader = 1
                                check = True
                                how_point = "X"

                    else: # By Z
                        check = False
                        point2 = XYZ(point1.X,point1.Y,pt2.Z)
                        leng = abs(point1.Z - point2.Z)

                        if (point1 - point2).Normalize().Z == 1:
                            left_rigth = 0
                            loc_leader = 2
                        elif (point1 - point2).Normalize().Z == -1:
                            left_rigth = 0
                            loc_leader = 0

                # ------ Разрез перпендикулярно X ------
                if abs(direction.X) == 1:
                    #Выравниванеи по оси
                    if abs(vec.Y) > abs(vec.Z): # By X
                        point2 = XYZ(point1.X,pt2.Y,point1.Z)
                        leng = abs(point2.Y - point1.Y)

                        if direction.X == float(-1):
                            if (point1 - point2).Normalize().Y == 1:
                                left_rigth = 0
                                loc_leader = 0
                                check = False
                            else:
                                left_rigth = 1
                                loc_leader = 1
                                check = True
                                how_point = "-Y"
                        else:
                            if (point1 - point2).Normalize().Y == 1:
                                left_rigth = 1
                                loc_leader = 1
                                check = True
                            else:
                                left_rigth = 0
                                loc_leader = 0
                                check = False
                                how_point = "Y"
                    else: # By Z
                        check = False
                        point2 = XYZ(point1.X,point1.Y,pt2.Z)
                        leng = abs(point2.Z - point1.Z)

                        if (point1 - point2).Normalize().Z == 1:
                            left_rigth = 0
                            loc_leader = 2
                        elif (point1 - point2).Normalize().Z == -1:
                            left_rigth = 0
                            loc_leader = 0
                        
            else:
                if abs(vec.X) > abs(vec.Y):
                    point2 = XYZ(pt2.X,point1.Y,point1.Z)
                    leng = abs(point2.X - point1.X)

                    if (point1 - point2).Normalize().IsAlmostEqualTo(XYZ.BasisX):
                        left_rigth = 1
                        loc_leader = 1
                        check = True
                        how_point = "-X"
                    else: 
                        loc_leader = 0
                        left_rigth = 0
                        check = False
                else: 
                    check = False
                    point2 = XYZ(point1.X,pt2.Y,point1.Z)
                    leng = abs(point2.Y - point1.Y)

                    if (point1 - point2).Normalize().IsAlmostEqualTo(XYZ.BasisY):
                        left_rigth = 0
                        loc_leader = 2
                    else: 
                        loc_leader = 0
                        left_rigth = 0

            # ------ Создать 2D разрез ------
            with Transaction(doc, 'Создать флажок') as t:
                t.Start()
                new_instance = doc.Create.NewFamilyInstance(point2, fe_symbol, doc.ActiveView)

                # ----- Настройка графики ------
                new_instance.LookupParameter("Длина стрелки").Set(leng/scale_views)
                ot = new_instance.LookupParameter("Положение выноски").Set(1)
                print(ot)
                #print(new_instance.LookupParameter("Положение выноски"))
                new_instance.LookupParameter("Правый").Set(left_rigth)
                
                # if check:
                #     new_instance_type = doc.GetElement(new_instance.Symbol.Id)
                #     wigth = float(new_instance_type.LookupParameter("Ширина").AsValueString()) / 304.8
                #     if how_point:
                #         if how_point == "-X":
                #             new_instance.Location.Move(XYZ(point2.X - wigth, point2.Y,point2.Z))
                #             print("-X")
                #         elif how_point == "X":
                #             new_instance.Location.Move(XYZ(point2.X - wigth, point2.Y,point2.Z))
                #             print("X")
                #         elif how_point == "-Y":
                #             new_instance.Location.Move(XYZ(point2.X, point2.Y-wigth,point2.Z))
                #             print("-Y")
                #         elif how_point == "Y":
                #             new_instance.Location.Move(XYZ(point2.X, point2.Y+wigth,point2.Z))
                #             print("-Y")
                #     #print(point2, point2.Multiply(wigth))
                #     print(point1,point2)
                # else:
                #     pass
                t.Commit()

        except OperationCanceledException:
            break

        except Exception as ex:
            forms.alert(str(ex))
            break

