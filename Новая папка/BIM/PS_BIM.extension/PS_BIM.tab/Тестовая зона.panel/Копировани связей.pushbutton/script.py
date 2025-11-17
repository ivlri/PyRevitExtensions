
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
import math

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter
from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter
from Autodesk.Revit.Exceptions import OperationCanceledException

# .NET Imports
import clr
clr.AddReference("System")
from System.Collections.Generic import List
from functions._CustomSelections import CustomSelections

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
	link = CustomSelections.pick_elements_by_class(RevitLinkInstance)[0]

# Получение связанного документа
LinkDoc = link.GetLinkDocument()

# Получение базовых точек проекта 
doc_base_point_pos = BasePoint.GetProjectBasePoint(doc).Position
link_basepoint_pos = BasePoint.GetProjectBasePoint(LinkDoc).Position

# Полученее списков положений проекта
id_DocSiteLocation = doc.SiteLocation.Id
id_LinkSiteLocation = LinkDoc.SiteLocation.Id

doc_loc_name = get_DocProjectLocationsNames()

elementsToCopy = List[ElementId]([link.Id])
vector = XYZ(100,0,0)

# Стартовый вектор с учетом угла поворота
start_loc = [LinkDoc_ProjectLocation for LinkDoc_ProjectLocation in LinkDoc.ProjectLocations if LinkDoc_ProjectLocation.Name in link.Name][0]
start_vector = XYZ(start_loc.GetProjectPosition(link_basepoint_pos).EastWest, 
                   start_loc.GetProjectPosition(link_basepoint_pos).NorthSouth, 
                   0)
#print(start_vector, '-----')
def rotare_vector_loc(vectort):
    angle_doc = BasePoint.GetProjectBasePoint(doc).LookupParameter('Угол от истинного севера').AsDouble() * 304

    x = vectort.X
    y = vectort.Y

    rotatedX = x * math.cos(angle_doc) - y * math.sin(angle_doc)
    rotatedY = x * math.sin(angle_doc) + y * math.cos(angle_doc)

    vector = XYZ(rotatedX,
                rotatedY,
                0)
    return vector
#print(start_vector, '-----')


for LinkDoc_ProjectLocation in LinkDoc.ProjectLocations:	
    pos_name = LinkDoc_ProjectLocation.Name
    if not 'побочная' in pos_name.lower() and start_loc.Name not in pos_name:
        second_vector_loc = XYZ(LinkDoc_ProjectLocation.GetProjectPosition(link_basepoint_pos).EastWest, LinkDoc_ProjectLocation.GetProjectPosition(link_basepoint_pos).NorthSouth,0)
        #print(second_vector_loc)
        vector_to_copy = second_vector_loc.Subtract(start_vector)
        print(vector_to_copy.X * 304.8,vector_to_copy.Y * 304.8)
        try:
            t = Transaction(doc, 'Копировать секцию')
            t.Start()
            ElementTransformUtils.CopyElements(doc, elementsToCopy, rotare_vector_loc(vector_to_copy))
            t.Commit()
        except Exception as ex:
            forms.alert(str(ex))
        #print("------", vector_to_copy)
# Запуск
#Create_DocProjectLocation(LinkDoc,doc_loc_name,doc_base_point_pos)