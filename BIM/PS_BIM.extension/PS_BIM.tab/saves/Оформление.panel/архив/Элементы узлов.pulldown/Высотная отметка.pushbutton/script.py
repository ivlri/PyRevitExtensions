# -*- coding: utf-8 -*-
__title__   = "Выстная отметка"
__doc__ = """Описание:
Создает 2D семейство высотной отметки по 2-м точкам на активном виде.
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
scale_views = float(active_view.LookupParameter("Масштаб вида").AsInteger())

#==================================================
#Func
#==================================================

#==================================================
#MAIN
#==================================================

famly_symbols = FilteredElementCollector(doc).OfClass(FamilySymbol).ToElements()
fe_symbol = filter(lambda x: x.FamilyName == "PS_Аннотации_Высотная отметка_Несколько", famly_symbols)

if not fe_symbol:
    forms.alert('Загрузите семейство PS_Аннотации_Высотная отметка или исправите дубли семейства')
else:
    fe_symbol = fe_symbol[0]
    while True:
        try: 
            with forms.WarningBar(title='1) Выберете точку начала выноски:'):
                point1 = selection.PickPoint(ObjectSnapTypes.Intersections)

            with forms.WarningBar(title='2) Выберете точку рсположения отметки:'):
                pt2 = selection.PickPoint(ObjectSnapTypes.Intersections)

            vec = (pt2 - point1).Normalize()

            #Выравниванеи по оси
            if abs(vec.X) > abs(vec.Y):
                point2 = XYZ(pt2.X,point1.Y,point1.Z)
                leng = abs(point2.X - point1.X)
            else: 
                forms.alert('Это семейство строится только в горизонтальном направлении')

            # Создать 2D разрез
            with Transaction(doc, 'Создать 2D разрез') as t:
                t.Start()
                new_instance = doc.Create.NewFamilyInstance(point2, fe_symbol, doc.ActiveView)
                new_instance.LookupParameter("Длина выноски").Set(leng/scale_views)
                t.Commit()
        except OperationCanceledException:
            break

        except Exception as ex:
            forms.alert(str(ex))
            break

