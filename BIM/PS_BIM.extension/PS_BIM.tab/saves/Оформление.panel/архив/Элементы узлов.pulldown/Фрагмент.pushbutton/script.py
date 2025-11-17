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

famly_symbols = FilteredElementCollector(doc).OfClass(FamilySymbol).ToElements()
fe_symbol = filter(lambda x: x.FamilyName == "PS_ЭУ_Узел_Фрагмент", famly_symbols)

if not fe_symbol:
    forms.alert('Загрузите семейство PS_ЭУ_Узел_Фрагмент или исправите дубли семейства')
else:
    fe_symbol = fe_symbol[0]
    try: 
        with forms.WarningBar(title='Выберете точку вставки:'):
            point = selection.PickPoint(ObjectSnapTypes.Intersections)

        # Создать 
        with Transaction(doc, 'Создать 2D фразмент') as t:
            t.Start()
            new_instance = doc.Create.NewFamilyInstance(point, fe_symbol, doc.ActiveView)
            t.Commit()
    except OperationCanceledException:
        pass

    except Exception as ex:
        forms.alert(str(ex))


