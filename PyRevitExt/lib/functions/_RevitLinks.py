# -*- coding: utf-8 -*-
#==================================================
#IMPORTS
#==================================================
from Autodesk.Revit.DB import *

from pyrevit import revit, forms

# .NET 
import clr
clr.AddReference("System")
from System.Collections.Generic import List

#==================================================
#VARIABLES
#==================================================
rvt_doc   = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app   = __revit__.Application

#==================================================
#FUNCTIONS
#==================================================

def doc_link_types(rvt_doc, names=False):
    """Get RevitLink types in a document or they names.
    revt_doc - Revit documents

    names=False -> list(DB.RevitLink type) 
    names=True -> dictionary('types':list(DB.RevitLink type) , 'names':list(DB.RevitLink.Name))
    """

    # get rvtlinks  
    linked_docs = FilteredElementCollector(rvt_doc).OfClass(RevitLinkInstance).ToElements()
    linked_types = linked_docs.GetType()
    linked_names = [i.Name for i in linked_docs]

    select_link_name = forms.SelectFromList.show(sorted(set(i.split(':')[0] for i in linked_names)),
                                    multiselect=True,
                                    button_name='Подтвердить выбор связей')

    #Т.К. linked_docs gets all revit links that have lacate in project
    filt_linked_docs = []
    check_appended_names = []
    for linked_name in linked_names:
        name = linked_name.split(':')[0] 
        if (name in select_link_name) and (name not in check_appended_names): # нет в выбраных и в уже обработаных
            check_appended_names.append(name) # имена которые далее будут игнорироваться
            filt_linked_docs.append(linked_docs[linked_names.index(linked_name)].GetLinkDocument())
    if names:
        return {
            'types': filt_linked_docs,
            'names': check_appended_names
        }
    else: 
        return filt_linked_docs


def get_link_elements_by_phase(l_doc, bt_category_for_use, isPhase, phase_name):
    """
    l_doc-
    category_for_use-
    isPhase-
    phase_name-

    """
    if isinstance(bt_category_for_use, list):
        category_list = bt_category_for_use
    else:
        category_list = [bt_category_for_use]
    phase_number = phase_name

    out=[]

    if isPhase:
        #Все стадии в связанном файле
        phases=FilteredElementCollector(l_doc).OfCategory(BuiltInCategory.OST_Phases).ToElements()

        #Отбор по стадии, введенной пользователем
        for phase in phases:
            if phase.Name in phase_number:
                phase_id = phase.Id
                
        #Фильтры по стадиям
        filter_Existing = ElementPhaseStatusFilter(phase_id, ElementOnPhaseStatus.Existing)
        filter_New = ElementPhaseStatusFilter(phase_id, ElementOnPhaseStatus.New)
        phases_or_filter = LogicalOrFilter([filter_Existing, filter_New])

        for category in category_list:
            elements = FilteredElementCollector(l_doc).OfClass(category).WhereElementIsNotElementType().WherePasses(phases_or_filter).ToElements()
            out.append(elements)
    else:
        for category in category_list:
            elements = FilteredElementCollector(l_doc).OfClass(category).WhereElementIsNotElementType().ToElements()
            out.append(elements)

    return out