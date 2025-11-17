# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ISelectionFilter, Selection, ObjectType
from Autodesk.Revit.Exceptions import OperationCanceledException

from pyrevit import revit, DB, UI

doc   =  revit.doc
uidoc = revit.uidoc

class Pick_by_category(ISelectionFilter):
    global doc
    def __init__(self, built_in_category):
        if isinstance(built_in_category, Category):
            self.built_in_category = [built_in_category.Id]
        else:
            if isinstance(built_in_category, BuiltInCategory):
                built_in_category = [built_in_category]
            self.built_in_category = [Category.GetCategory(self.doc, i).Id for i in built_in_category]

    def AllowElement(self, el):
        if el.Category.Id in self.built_in_category:
            return True
        return False

    def AllowReference(self, refer, xyz):
        return False

class Pick_by_class(ISelectionFilter):
    global doc
    def __init__(self, class_type):
        self.class_type = class_type

    def AllowElement(self, el):
        if isinstance(el, self.class_type):
            return True
        return False

    def AllowReference(self, refer, xyz):
        return False


class CustomSelections():
    """Класс с реализацией различных методов выбора элементов."""

    def __init__(self, doc, uidoc):
        self.doc = doc
        self.uidoc = uidoc
        self.selection = uidoc.Selection
        

    def pick_element_by_category(self, built_in_category, status="Выберете элемент"):
        """Выбор одного элемента по BuiltInCategory."""
        try:
            return self.doc.GetElement(self.selection.PickObject(ObjectType.Element, Pick_by_category(built_in_category),status))
        except OperationCanceledException:
            return


    def pick_element_by_class(self, class_type, status="Выберете элемент"):
        """Выбор одного элемента по категории."""
        try:
            return self.doc.GetElement(self.selection.PickObject(ObjectType.Element, Pick_by_class(class_type),status))
        except OperationCanceledException:
            return


    def pick_elements_by_class(self, class_type, status="Выберете элемент"):
        """Выбор одного элемента по категории."""
        try:
            return [self.doc.GetElement(i) for i in self.selection.PickObjects(ObjectType.Element, Pick_by_class(class_type),status)]
        except OperationCanceledException:
            return
    

    def get_picked(self):
        """Получение всех выбранных элементов ревит
        P.S. Учти, что при использовании ломается получаение активного вида
        """
        select = self.uidoc.Selection.GetElementIds()
        if len(select) == 1:
            return [self.doc.GetElement(id) for id in select][0]
        else:
            return [self.doc.GetElement(id) for id in select]  
        