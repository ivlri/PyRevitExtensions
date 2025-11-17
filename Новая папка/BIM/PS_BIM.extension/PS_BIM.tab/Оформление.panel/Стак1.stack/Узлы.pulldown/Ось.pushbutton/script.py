# -*- coding: utf-8 -*-
__title__   = "Выстная отметка"
__doc__ = """Описание:
Создает 2D семейство высотной отметки по 2-м точкам на активном виде.
"""
#==================================================
#IMPORTS
#==================================================
import System

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ISelectionFilter, Selection, ObjectType, ObjectSnapTypes
from Autodesk.Revit.Exceptions import OperationCanceledException

from functions._CustomSelections import CustomSelections
from pyrevit import forms

doc   = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app   = __revit__.Application
active_view = doc.ActiveView
selection = uidoc.Selection
#==================================================
#MAIN
#==================================================
   
scale_views = float(active_view.LookupParameter("Масштаб вида").AsInteger())

famly_symbols = FilteredElementCollector(doc).OfClass(FamilySymbol).ToElements()
fe_symbol = filter(lambda x: x.FamilyName == "PS_ЭУ_Ось", famly_symbols)

not_view_section_conditions = (isinstance(active_view, ViewPlan) or 
                        isinstance(active_view, ViewDrafting) or 
                        doc.GetElement(active_view.GetTypeId()).FamilyName == "Легенды" or
                        doc.GetElement(active_view.GetTypeId()).FamilyName == "Легенда")

if not_view_section_conditions:
    if not fe_symbol:
        family_path = "\\\\fs\\public\\Холдинг\\ПоревитД\\ТИМ\01_Библиотека\\01_Рабочие задачи\\ALL_Элементы узлов\\PS_ЭУ_Ось.rfa"
        try:
            with Transaction(doc, "Загрузка семейства") as t:
                t.Start()
                loaded_family = doc.LoadFamily(family_path)
                t.Commit()
            
        except Exception as e:
            forms.alert("Ошибка загрузки семейства: {}".format(e))
        
        famly_symbols = FilteredElementCollector(doc).OfClass(FamilySymbol).ToElements()
        fe_symbol = filter(lambda x: x.FamilyName == "PS_ЭУ_Ось", famly_symbols)

    fe_symbol = fe_symbol[0]
    while True:
        try: 
            #with forms.WarningBar(title='1) Выберите точку начала выноски:'):
            point1 = selection.PickPoint(ObjectSnapTypes.Intersections,'1) Выберете точку начала выноски:')

            #with forms.WarningBar(title='2) Выберите точку рсположения отметки:'):
            pt2 = selection.PickPoint(ObjectSnapTypes.Intersections,'1) Выберете точку вставки отметки:')

            vec = (pt2 - point1).Normalize()

            # Выравниванеи по оси
            if abs(vec.X) > abs(vec.Y):
                point2 = XYZ(pt2.X,point1.Y,point1.Z)
                loc = False
            else: 
                point2 = XYZ(point1.X,pt2.Y,point1.Z)
                loc = True

            # Создать 2D разрез
            with Transaction(doc, 'Создать 2D ось') as t:
                t.Start()
                new_instance = doc.Create.NewFamilyInstance(Line.CreateBound(point1,point2), fe_symbol, doc.ActiveView)
                new_instance.LookupParameter("Имя оси 1").Set(' ')
                t.Commit()
        except OperationCanceledException:
            break

        except Exception as ex:
            forms.alert(str(ex))
            break
else:
    forms.alert("Нельзя применять на данном виде")
