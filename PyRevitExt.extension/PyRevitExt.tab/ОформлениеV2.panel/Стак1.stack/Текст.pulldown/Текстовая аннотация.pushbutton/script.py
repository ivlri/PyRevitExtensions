# -*- coding: utf-8 -*-
__title__   = "Текстовая\nаннотация"
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
from functions._sketch_plane import set_sketch_plane_to_viewsection
from pyrevit import forms,revit

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


set_sketch_plane_to_viewsection(doc)

famly_symbols = FilteredElementCollector(doc).OfClass(FamilySymbol).ToElements()
fe_symbol = filter(lambda x:  x.FamilyName == "ADSK_Аннотация_Текст_сВыноской" or x.FamilyName == "ADSK_A_Текст с выноской", 
                   famly_symbols)

if not fe_symbol:
    forms.alert('Загрузите семейство ADSK_Аннотация_Текст_сВыноской или исправите дубли семейства')
else:
    fe_symbol = fe_symbol[0]
    try: 
        with forms.WarningBar(title='Выберите точку вставки:'):
            point = selection.PickPoint(ObjectSnapTypes.None,'Выберите точку вставки:')

        # Создать 
        with Transaction(doc, 'Создать анатацию') as t:
            t.Start()
            new_instance = doc.Create.NewFamilyInstance(point, fe_symbol, doc.ActiveView)
            new_instance.LookupParameter('Текст верх').Set(' ')
            new_instance.LookupParameter('Текст низ').Set(' ')
            t.Commit()
    except OperationCanceledException:
        pass

    except Exception as ex:
        forms.alert(str(ex))


