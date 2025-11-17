# -*- coding: utf-8 -*-
__title__   = "Обрыв"
__doc__ = """Описание:
Создает 2D семейство линии обрыва на активном виде.
"""
#==================================================
#IMPORTS
#==================================================

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ISelectionFilter, Selection, ObjectType
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
            with forms.WarningBar(title='1) Выберете начальную точку:'):
                point1 = selection.PickPoint()

            with forms.WarningBar(title='2) Выберете конечную точку:'):
                pt2 = selection.PickPoint()

            with forms.WarningBar(title='3) Укажите глубину обыва:'):
                point3 = selection.PickPoint()

            vec = (pt2 - point1).Normalize()

            # Выравниванеи по оси
            if abs(vec.X) > abs(vec.Y):
                point2 = XYZ(pt2.X,point1.Y,point1.Z)
                loc = abs(point1.Y-point3.Y)
            else: 
                point2 = XYZ(point1.X,pt2.Y,point1.Z)
                loc = abs(point1.X-point3.X)

            # Создать 2D разрез
            with Transaction(doc, 'Создать обрыв') as t:
                t.Start()
                new_instance = doc.Create.NewFamilyInstance(Line.CreateBound(point1,point2), fe_symbol, doc.ActiveView)
                new_instance.LookupParameter(par_name).Set(loc)
                # new_instance.LookupParameter("Номер вида").Set(str(count))
                t.Commit()
        except OperationCanceledException:
            break

        except Exception as ex:
            forms.alert(str(ex))
            break

