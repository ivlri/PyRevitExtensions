# -*- coding: utf-8 -*-
__title__   = "Узел"
__doc__ = """Описание:
Создает 2D семейство обозначения узла.
"""
#==================================================
#IMPORTS
#==================================================

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
#Func
#==================================================

#==================================================
#MAIN
#==================================================


not_view_section_conditions = (isinstance(active_view, ViewPlan) or 
                    isinstance(active_view, ViewDrafting) or 
                    doc.GetElement(active_view.GetTypeId()).FamilyName == "Легенды" or
                        doc.GetElement(active_view.GetTypeId()).FamilyName == "Легенда")

if not_view_section_conditions:
    famly_symbols = FilteredElementCollector(doc).OfClass(FamilySymbol).ToElements()
    fe_symbol = filter(lambda x: x.FamilyName == "PS_ЭУ_Узел", famly_symbols)

    if not fe_symbol:
        family_path = "\\\\fs\\public\\Холдинг\\ПоревитД\\ТИМ\01_Библиотека\\01_Рабочие задачи\\ALL_Элементы узлов\\PS_ЭУ_Узел.rfa"
        try:
            with Transaction(doc, "Загрузка семейства") as t:
                t.Start()
                loaded_family = doc.LoadFamily(family_path)
                t.Commit()
            
        except Exception as e:
            forms.alert("Ошибка загрузки семейства: {}".format(e))
        
        famly_symbols = FilteredElementCollector(doc).OfClass(FamilySymbol).ToElements()
        fe_symbol = filter(lambda x: x.FamilyName == "PS_ЭУ_Узел", famly_symbols)

    fe_symbol = fe_symbol[0]
    while True:
        try: 
            #with forms.WarningBar(title='1) Выберите начальную точку:'):
            point1 = selection.PickPoint(ObjectSnapTypes.None,'1) Выберите начальную точку:')

            #with forms.WarningBar(title='2) Выберите конечную точку:'):
            pt2 = selection.PickPoint(ObjectSnapTypes.None,'2) Выберите конечную точку:')

            vec = (pt2 - point1).Normalize()

            # Выравниванеи по оси
            if abs(vec.X) > abs(vec.Y):
                point2 = XYZ(pt2.X,point1.Y,point1.Z)
                loc = False
            else: 
                point2 = XYZ(point1.X,pt2.Y,point1.Z)
                loc = True

            # Смещение точки построения
            scale_views = float(active_view.LookupParameter("Масштаб вида").AsInteger())/304.8
            norm = (point2 - point1).Normalize()*4.5*scale_views

            # Создать 2D разрез
            with Transaction(doc, 'Создать 2D разрез') as t:
                t.Start()
                new_instance = doc.Create.NewFamilyInstance(Line.CreateBound(point1+norm,point2), fe_symbol, doc.ActiveView)
                t.Commit()
        except OperationCanceledException:
            break

        except Exception as ex:
            forms.alert(str(ex))
            break
else:
    forms.alert("Нельзя применять на данном виде")

