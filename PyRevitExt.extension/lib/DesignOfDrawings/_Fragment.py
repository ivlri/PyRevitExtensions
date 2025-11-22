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
#MAIN
#==================================================
def start():
    doc   = __revit__.ActiveUIDocument.Document
    uidoc = __revit__.ActiveUIDocument
    app   = __revit__.Application
    active_view = doc.ActiveView
    selection = uidoc.Selection  

    not_view_section_conditions = (isinstance(active_view, ViewPlan) or 
                            isinstance(active_view, ViewDrafting) or 
                            doc.GetElement(active_view.GetTypeId()).FamilyName == "Легенды")
    
    if not_view_section_conditions:
        famly_symbols = FilteredElementCollector(doc).OfClass(FamilySymbol).ToElements()
        fe_symbol = filter(lambda x: x.FamilyName == "PS_ЭУ_Узел_Фрагмент", famly_symbols)

        if not fe_symbol:
            forms.alert('Загрузите семейство PS_ЭУ_Узел_Фрагмент или исправите дубли семейства')
        else:
            fe_symbol = fe_symbol[0]
            try: 
                #with forms.WarningBar(title='Выберете точку вставки:'):
                point1 = selection.PickPoint(ObjectSnapTypes.Intersections,'Выберете точку вставки:')

                point2 = selection.PickPoint(ObjectSnapTypes.Intersections,'Укажите высоту фрагмента:')

                # Создать 
                with Transaction(doc, 'Создать 2D фразмент') as t:
                    t.Start()
                    new_instance = doc.Create.NewFamilyInstance(point1, fe_symbol, doc.ActiveView)
                    value = point1.DistanceTo(point2)
                    new_instance.LookupParameter("Высота").Set(value)
                    new_instance.LookupParameter("Ширина").Set(value)
                    t.Commit()
            except OperationCanceledException:
                pass

            except Exception as ex:
                forms.alert(str(ex))
    else:
        forms.alert("Нельзя применять на данном виде")

