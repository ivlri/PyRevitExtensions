# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ISelectionFilter, Selection, ObjectType, ObjectSnapTypes
from Autodesk.Revit.Exceptions import OperationCanceledException

from functions._CustomSelections import CustomSelections
from pyrevit import forms

#==================================================
#VARIABLES
#==================================================

#==================================================
#Func
#==================================================

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
        family_symbols = FilteredElementCollector(doc).OfClass(FamilySymbol).ToElements()
        fe_symbol = filter(lambda x: x.FamilyName == "PS_ЭУ_Разрез", family_symbols)

        if not fe_symbol:
            forms.alert('Загрузите семейство PS_ЭУ_Разрез или исправьте дубли семейства')
        else:
            fe_symbol = fe_symbol[0]
            count = 1
            while True:
                try:        
                    #with forms.WarningBar(title='1) Выберете начальную точку:'):
                    point1 = selection.PickPoint(ObjectSnapTypes.Intersections,'1) Выберете начальную точку:')

                    #with forms.WarningBar(title='2) Выберете конечную точку:'):
                    pt2 = selection.PickPoint(ObjectSnapTypes.Intersections,'2) Выберете конечную точку:')

                    vec = (pt2 - point1).Normalize()

                    # Выравниванеи по оси
                    if abs(vec.X) > abs(vec.Y):
                        point2 = XYZ(pt2.X,point1.Y,point1.Z)
                        loc = False
                    else: 
                        point2 = XYZ(point1.X,pt2.Y,point1.Z)
                        loc = True

                    # Создать 2D разрез
                    with Transaction(doc, 'Создать 2D разрез') as t:
                        t.Start()
                        new_instance = doc.Create.NewFamilyInstance(Line.CreateBound(point1,point2), fe_symbol, doc.ActiveView)
                        new_instance.LookupParameter("Вертикально").Set(loc)
                        new_instance.LookupParameter("Номер вида").Set(str(count))
                        t.Commit()
                    count += 1
                except OperationCanceledException:
                    break

                except Exception as ex:
                    forms.alert(str(ex))
                    break
    else:
        forms.alert("Нельзя применять на данном виде")