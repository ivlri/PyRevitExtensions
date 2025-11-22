
# -*- coding: utf-8 -*-
__title__   = "Площадки из связи"
__doc__ = """Описание:
Скрипт предназначен для копирования площадок напрямую из связанного файла, где нужные площадки уже есть.  
При коприровании переносятся имена, а так же местоположение в соответстии с генплааном.
________________________________________________________________
Как использовать:
1. Файл откуда копировать и файл куда копировать - должны быть в одной системе кооринат
2. Запустить скрипт и следовать дальнейшим указаниям. 
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


class Selections:
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
    def pick_element_by_class(cls, class_type):
        """Выбор одного элемента по категории."""
        try:
            return cls.doc.GetElement(cls.selection.PickObject(ObjectType.Element, Pick_by_class(class_type)))
        except OperationCanceledException:
            return

    @classmethod
    def pick_elements_by_class(cls, class_type):
        """Выбор одного элемента по категории."""
        try:
            return [cls.doc.GetElement(i) for i in cls.selection.PickObjects(ObjectType.Element, Pick_by_class(class_type))]
        except OperationCanceledException:
            return


#==================================================
#FUNCTIONS
#==================================================


# Получение имен полощадок связи 
def get_DocProjectLocationsNames():
	lst = []
	for ProjectLocation in doc.ProjectLocations:
		lst.append(ProjectLocation.Name)
	return lst


def Create_DocProjectLocation(LinkDoc, names,doc_base_p = XYZ(0,0,0)):
    global link_basepoint_pos
    global id_DocSiteLocation

    with Transaction(doc, 'Копирование полощадок') as t:
        t.Start()
        #  Сбор  данных
        max_value = 0
        used_names = []
        for LinkDoc_ProjectLocation in LinkDoc.ProjectLocations:
            if LinkDoc_ProjectLocation.Name not in names:
                max_value += 1
                used_names.append(LinkDoc_ProjectLocation.Name)
        
        # Список для выбора 
        res = forms.SelectFromList.show(sorted(used_names),
                                multiselect=True,
                                button_name='Подтвердить выбор площадок для копирования')
        
        # Процесс создания плошадки и изменения ее координат
        with ProgressBar(title='Процесс копирования... ({value} of {max_value}))') as pb:                         
            counter = 0             
            for LinkDoc_ProjectLocation in LinkDoc.ProjectLocations:						 
                if LinkDoc_ProjectLocation.Name in res:
                    o_pos = LinkDoc_ProjectLocation.GetProjectPosition(link_basepoint_pos)
                    n_pos = ProjectPosition(o_pos)
                    loc = ProjectLocation.Create(doc,id_DocSiteLocation,LinkDoc_ProjectLocation.Name)
                    set_pos = loc.SetProjectPosition(doc_base_p,n_pos)
                    counter += 1
                    pb.update_progress(counter, max_value)
        t.Commit()


#==================================================
#MAIN
#==================================================


with forms.WarningBar(title='Выберете  связь:'):
	link = Selections.pick_elements_by_class(RevitLinkInstance)[0]

# Получение связанного документа
LinkDoc = link.GetLinkDocument()

# Получение базовых точек проекта 
doc_base_point_pos = BasePoint.GetProjectBasePoint(doc).Position
link_basepoint_pos = BasePoint.GetProjectBasePoint(LinkDoc).Position

# Полученее списков положений проекта
id_DocSiteLocation = doc.SiteLocation.Id
id_LinkSiteLocation = LinkDoc.SiteLocation.Id

doc_loc_name = get_DocProjectLocationsNames()

# Запуск
Create_DocProjectLocation(LinkDoc,doc_loc_name,doc_base_point_pos)