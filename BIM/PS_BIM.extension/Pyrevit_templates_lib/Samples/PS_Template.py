
# -*- coding: utf-8 -*-
__title__   = "Имя"
__doc__ = """Описание:
"""
#==================================================
#IMPORTS
#==================================================

import os
import codecs

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter
from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter
from Autodesk.Revit.Exceptions import OperationCanceledException

# .NET Imports
import clr
clr.AddReference("System")
from System.Collections.Generic import List


from pyrevit import forms
from pyrevit import revit, DB, UI
from pyrevit.forms import ProgressBar
#==================================================
#VARIABLES
#==================================================

doc = revit.doc
uidoc = __revit__.ActiveUIDocument
app   = __revit__.Application

#==================================================
#CLASSES
#==================================================

class Pick_by_category(ISelectionFilter):
    doc = __revit__.ActiveUIDocument.Document
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
    doc = __revit__.ActiveUIDocument.Document
    def __init__(self, class_type):
        self.class_type = class_type

    def AllowElement(self, el):
        if isinstance(el, self.class_type):
            return True
        return False

    def AllowReference(self, refer, xyz):
        return False


class Selections():
    """Класс с реализацией различных методов выбора элементов."""

    selection = __revit__.ActiveUIDocument.Selection
    doc = __revit__.ActiveUIDocument.Document
    @classmethod
    def pick_element_by_category(cls, built_in_category):
        """Выбор одного элемента по BuiltInCategory."""
        try:
            return cls.doc.GetElement(cls.selection.PickObject(ObjectType.Element, Pick_by_category(built_in_category)))
        except OperationCanceledException:
            return
        
    @classmethod
    def pick_elements_by_category(cls, built_in_category):
        """Выбор нескольких элментнов по BuiltInCategory."""
        try:
            return cls.doc.GetElement(cls.doc.GetElement(i) for i in cls.selection.PickObject(ObjectType.Element, Pick_by_category(built_in_category)))
        except OperationCanceledException:
            return

    @classmethod
    def pick_element_by_class(cls, class_type):
        """Выбор одного элемента по Классу."""
        try:
            return cls.doc.GetElement(cls.selection.PickObject(ObjectType.Element, Pick_by_class(class_type)))
        except OperationCanceledException:
            return

    @classmethod
    def pick_elements_by_class(cls, class_type):
        """Выбор нескольких элментнов по Классу."""
        try:
            return [cls.doc.GetElement(i) for i in cls.selection.PickObjects(ObjectType.Element, Pick_by_class(class_type))]
        except OperationCanceledException:
            return

    @classmethod
    def seletc_linkdoc_by_form(csl):
        with forms.WarningBar(title='Выберете  связь:'):
            link = Selections.pick_elements_by_class(RevitLinkInstance)
        
        if len(link) > 1:
            out = []
            for i in link:
                out.append(i.GetLinkDocument())
        else:
            out = link[0].GetLinkDocument()

        return link

#==================================================
#FUNCTIONS
#==================================================


#==================================================
#MAIN
#==================================================
