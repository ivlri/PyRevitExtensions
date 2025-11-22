# -*- coding: utf-8 -*-
__title__   = "Гидроизоляция"
__doc__ = """Описание:
Создает 2D семейство гидроизоляции.
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
        fe_symbol = filter(lambda x: x.FamilyName == "PS_Гидроизоляция", famly_symbols)

        if not fe_symbol:
            forms.alert('Загрузите семейство PS_Гидроизоляция или исправите дубли семейства')
        else:
            fe_symbol = fe_symbol[0]

            #with forms.WarningBar(title='Выберете начальную точку:'):
            point1 = selection.PickPoint(ObjectSnapTypes.Intersections,'Выберете начальную точку:')

            count = 1
            while True:
                try: 

                    with forms.WarningBar(title='Выберете {n} точку:'.format(n=count)):
                        pt2 = selection.PickPoint(ObjectSnapTypes.Intersections)


        # Снять коментарии что бы выравнивать по оси
                    #vec = (pt2 - point1).Normalize()
                    
                    point2 = pt2 # при выпарвнивании - удалить

                    # # Выравниванеи по оси
                    # if abs(vec.X) > abs(vec.Y):
                    #     point2 = XYZ(pt2.X,point1.Y,0)
                    #     loc = False
                    # else: 
                    #     point2 = XYZ(point1.X,pt2.Y,0)
                    #     loc = True

                    # Создать 2D разрез
                    with Transaction(doc, 'Создать гидроизоляцию') as t:
                        t.Start()
                        new_instance = doc.Create.NewFamilyInstance(Line.CreateBound(point1,point2), fe_symbol, doc.ActiveView)
                        t.Commit()

                    count += 1
                    
                    point1 = point2
                except OperationCanceledException:
                    break

                except Exception as ex:
                    forms.alert(str(ex))
                    break
    else: 
        forms.alert("Нельзя применять на данном виде")

