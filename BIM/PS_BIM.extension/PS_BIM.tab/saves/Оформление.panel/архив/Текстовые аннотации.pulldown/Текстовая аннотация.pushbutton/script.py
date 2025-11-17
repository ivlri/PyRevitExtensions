# -*- coding: utf-8 -*-
__title__   = "Текстовая\nаннотация"
__doc__ = """Описание:
Создает стандартное семейство текстовой аннотации ASDK на активном виде по указанной точке.
"""
#==================================================
#IMPORTS
#==================================================


from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ISelectionFilter, Selection, ObjectType
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
set_sketch_plane_to_viewsection(doc)

famly_symbols = FilteredElementCollector(doc).OfClass(FamilySymbol).ToElements()
fe_symbol = filter(lambda x: x.FamilyName == "ADSK_Аннотация_Текст_сВыноской", famly_symbols)[0]

if not fe_symbol:
    forms.alert('Исправите дубли семейства')
else:
    try: 
        with forms.WarningBar(title='Выберете точку вставки:'):
            point = selection.PickPoint()

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


