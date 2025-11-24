# -*- coding: utf-8 -*-
__title__   = "Стрелка"
__doc__ = """Описание:
Создает 2D семейство стрелки.
"""
#==================================================
#IMPORTS
#==================================================

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ISelectionFilter, Selection, ObjectType, ObjectSnapTypes
from Autodesk.Revit.Exceptions import OperationCanceledException

from functions._CustomSelections import CustomSelections
from pyrevit import forms

# Добавляем логирование использования инструмента
import os
from functions._logger import ToolLogger
ToolLogger(script_path=__file__).log()

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
                            doc.GetElement(active_view.GetTypeId()).FamilyName == "Легенды"or
                        doc.GetElement(active_view.GetTypeId()).FamilyName == "Легенда")

if not_view_section_conditions:
    famly_symbols = FilteredElementCollector(doc).OfClass(FamilySymbol).ToElements()
    fe_symbol = filter(lambda x: x.FamilyName == "PS_ЭУ_Стрелка", famly_symbols)

    if not fe_symbol:
        forms.alert('Загрузите семейство PS_ЭУ_Стрелка или исправьте дубли семейства')
    else:
        fe_symbol = fe_symbol[0]
        while True:
            try: 
                #with forms.WarningBar(title='1) Выберите начальную точку:'):
                point1 = selection.PickPoint(ObjectSnapTypes.Intersections,'1) Выберете начальную точку:')

                #with forms.WarningBar(title='2) Выберите конечную точку:'):
                pt2 = selection.PickPoint(ObjectSnapTypes.Intersections,'2) Выберете конечную точку:')


    # Снять коментарии что бы выравнивать по оси
                #vec = (pt2 - point1).Normalize()
                
                point2 = pt2 # при выпарвнивании - удалить

                # # Выравниванеи по оси
                # if abs(vec.X) > abs(vec.Y):
                #     point2 = XYZ(pt2.X,point1.Y,0)
                #     loc = False
                # else: 
                #     point2 = XYZ(point1.X,pt2.Y,0)
                #     loc = True

                # Создать 2D разрез
                with Transaction(doc, 'Создать 2D стрелки') as t:
                    t.Start()
                    new_instance = doc.Create.NewFamilyInstance(Line.CreateBound(point1,point2), fe_symbol, doc.ActiveView)
                    t.Commit()
            except OperationCanceledException:
                break

            except Exception as ex:
                forms.alert(str(ex))
                break
else:
    forms.alert("Нельзя применять на данном виде")
