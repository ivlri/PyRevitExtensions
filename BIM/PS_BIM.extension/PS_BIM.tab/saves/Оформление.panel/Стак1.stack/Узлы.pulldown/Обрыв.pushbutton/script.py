# -*- coding: utf-8 -*-
__title__   = "Обрыв"
__doc__ = """Описание:
Создает 2D семейство линии обрыва на активном виде.
"""
#==================================================
#IMPORTS
#==================================================

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ISelectionFilter, Selection, ObjectType, ObjectSnapTypes
from Autodesk.Revit.Exceptions import OperationCanceledException

from functions._CustomSelections import CustomSelections
from functions._sketch_plane import set_sketch_plane_to_viewsection
from pyrevit import forms

#==================================================
#VARIABLES
#==================================================

doc   = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app   = __revit__.Application
active_view = doc.ActiveView
selection = uidoc.Selection

#==================================================
#Func
#==================================================

#==================================================
#MAIN
#==================================================

not_view_section_conditions = (isinstance(active_view, ViewPlan) or 
                        isinstance(active_view, ViewDrafting) or 
                        isinstance(active_view, ViewSection) or 
                        doc.GetElement(active_view.GetTypeId()).FamilyName == "Легенды" or
                        doc.GetElement(active_view.GetTypeId()).FamilyName == "Легенда")


if not_view_section_conditions:
    set_sketch_plane_to_viewsection(doc)

    direction = active_view.ViewDirection # Ориентация вида
    origin = active_view.Origin


    famly_symbols = FilteredElementCollector(doc).OfClass(FamilySymbol).ToElements()

    fe_symbol = filter(lambda x: x.FamilyName == "ADSK_Обрыв_Линия" or x.FamilyName == "ADSK_ЭУ_Узел_Линии разрыва" , 
                    famly_symbols)

    if not fe_symbol:
        forms.alert('Загрузите семейство ADSK_Обрыв_Линия или исправьте дубли семейства')

    else:
        fe_symbol = fe_symbol[0]

        # костыль№2. Т.К. в шаблонах АР и КЖ разные семейства 
        par_name = 'Глубина' if fe_symbol.FamilyName == "ADSK_Обрыв_Линия" else 'Глубина маскировки'
        while True:
            try: 
                #with forms.WarningBar(title='1) Выберите начальную точку:'):
                point1 = selection.PickPoint(ObjectSnapTypes.Intersections,'1) Выберите начальную точку:')

                #with forms.WarningBar(title='2) Выберите конечную точку:'):
                pt2 = selection.PickPoint(ObjectSnapTypes.Intersections,'2) Выберите конечную точку:')


                if isinstance(active_view, ViewSection):
                    # ------ Разрез перпендикулярно Y ------
                    if abs(direction.Y) == 1:
                        point1 = XYZ(point1.X,origin.Y,point1.Z)
                        vec = (pt2 - point1).Normalize()

                        #Выравниванеи по оси
                        if abs(vec.X) > abs(vec.Z): # By X
                            point2 = XYZ(pt2.X,point1.Y,point1.Z)

                        else: # By Z
                            point2 = XYZ(point1.X,point1.Y,pt2.Z)

                    # ------ Разрез перпендикулярно X 
                    if abs(direction.X) == 1:
                        point1 = XYZ(origin.X,point1.Y,point1.Z)
                        vec = (pt2 - point1).Normalize()

                        #Выравниванеи по оси
                        if abs(vec.Y) > abs(vec.Z): # By X
                            point2 = XYZ(point1.X,pt2.Y,point1.Z)
                        else: # By Z
                            point2 = XYZ(point1.X,point1.Y,pt2.Z)
                else:
                    vec = (pt2 - point1).Normalize()

                    if abs(vec.X) > abs(vec.Y):
                        point2 = XYZ(pt2.X,point1.Y,point1.Z)
                    else: 
                        point2 = XYZ(point1.X,pt2.Y,point1.Z)

                # Создать 2D разрез
                with Transaction(doc, 'Создать обрыв') as t:
                    t.Start()
                    new_instance = doc.Create.NewFamilyInstance(Line.CreateBound(point1,point2), fe_symbol, doc.ActiveView)
                    new_instance.LookupParameter(par_name).Set(200/304.8)
                    t.Commit()
            except OperationCanceledException:
                break

            except Exception as ex:
                forms.alert(str(ex))
                break
else:
    forms.alert("Нельзя применять на данном виде")

