# -*- coding: utf-8 -*-
__title__   = "Гидроизоляция"
__doc__ = """Описание:
Создает 2D семейство гидроизоляции.
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

# Добавляем логирование использования инструмента
import os
from functions._logger import ToolLogger
ToolLogger(script_path=__file__).log()

doc   = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app   = __revit__.Application
active_view = doc.ActiveView
selection = uidoc.Selection   
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
    fe_symbol = filter(lambda x: x.FamilyName == "PS_Гидроизоляция", famly_symbols)

    if not fe_symbol:
        forms.alert('Загрузите семейство PS_Гидроизоляция или исправьте дубли семейства')
    else:
        fe_symbol = fe_symbol[0]

        #with forms.WarningBar(title='Выберите начальную точку:'):
        point1 = selection.PickPoint(ObjectSnapTypes.Intersections,'Выберите начальную точку:')

        if isinstance(active_view, ViewSection):
            # ------ Разрез перпендикулярно Y ------
            if abs(direction.Y) == 1:
                point1 = XYZ(point1.X,origin.Y,point1.Z)

            # ------ Разрез перпендикулярно X 
            if abs(direction.X) == 1:
                point1 = XYZ(origin.X,point1.Y,point1.Z)

        count = 1
        while True:
            try: 

                #with forms.WarningBar(title='Выберите {n} точку:'.format(n=count)):
                point2 = selection.PickPoint(ObjectSnapTypes.Intersections,'Выберите {n} точку:'.format(n=count))

                if isinstance(active_view, ViewSection):
                    # ------ Разрез перпендикулярно Y ------
                    if abs(direction.Y) == 1:
                        point2 = XYZ(point2.X,origin.Y,point2.Z)

                    # ------ Разрез перпендикулярно X 
                    if abs(direction.X) == 1:
                        point2 = XYZ(origin.X,point2.Y,point2.Z)

                # Создать 2D разрез
                with Transaction(doc, 'Создать гидроизоляцию') as t:
                    t.Start()
                    new_instance = doc.Create.NewFamilyInstance(Line.CreateBound(point1,point2), fe_symbol, doc.ActiveView)
                    t.Commit()

                count += 1
                
                point1 = point2
            except OperationCanceledException:
                break

            except Exception as ex:
                forms.alert(str(ex))
                break
else: 
    forms.alert("Нельзя применять на данном виде")

