# -*- coding: utf-8 -*-
__title__   = "Фрагмент"
__doc__ = """Описание:
Создает стандартное семейство текстовой аннотации ASDK на активном виде по указанной точке.
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
                        doc.GetElement(active_view.GetTypeId()).FamilyName == "Легенды" or
                        doc.GetElement(active_view.GetTypeId()).FamilyName == "Легенда")

if not_view_section_conditions:
    famly_symbols = FilteredElementCollector(doc).OfClass(FamilySymbol).ToElements()
    fe_symbol = filter(lambda x: x.FamilyName == "PS_ЭУ_Узел_Фрагмент", famly_symbols)

    if not fe_symbol:
        forms.alert('Загрузите семейство PS_ЭУ_Узел_Фрагмент или исправьте дубли семейства')
    else:
        fe_symbol = fe_symbol[0]
        try:
            while True:
                #with forms.WarningBar(title='Выберите точку вставки:'):
                point1 = selection.PickPoint(ObjectSnapTypes.None, ' 1) Укажите левый нижний угол:')

                #with forms.WarningBar(title='Укажите высоту фрагмента:'):
                point2 = selection.PickPoint(ObjectSnapTypes.None, ' 2) Укажите правый верхний:')

                point_to_create = XYZ(((point2 + point1)/2).X, point1.Y, point1.Z)

                #print(point1, point2, point_to_create)

                # Создать 
                with Transaction(doc, 'Создать 2D фрагмент') as t:
                    t.Start()
                    new_instance = doc.Create.NewFamilyInstance(point_to_create, fe_symbol, doc.ActiveView)
                    #value = point1.DistanceTo(point2)
                    new_instance.LookupParameter("Высота").Set(point1.DistanceTo(XYZ(point1.X, point2.Y,point1.Z)))
                    new_instance.LookupParameter("Ширина").Set(point1.DistanceTo(XYZ(point2.X, point1.Y,point1.Z)))
                    t.Commit()
        except OperationCanceledException:
            pass

        except Exception as ex:
            forms.alert(str(ex))
else:
    forms.alert("Нельзя применять на данном виде")

