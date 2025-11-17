
# -*- coding: utf-8 -*-

__title__   = "Проверка сведений\nо проекте"
__doc__ = """Описание: 
По выбранным связям производит проверку, занят ли рабочий набор "Сведения о проетке" или нет. Отчет будет показан в появившемя окне.
"""

#==================================================
#IMPORTS
#==================================================

import os
import codecs


from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter
from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter
from Autodesk.Revit.Exceptions import OperationCanceledException, ArgumentNullException

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
#MAIN
#==================================================
# Получение связанных файлов 
linked_docs = FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements()
linked_types = linked_docs.GetType()
linked_names = [i.Name for i in linked_docs]
# # Выбор файлов для провеки
select_link_name = forms.SelectFromList.show(sorted(set(i.split(':')[0] for i in linked_names)),
                                multiselect=True,
                                button_name='Подтвердить выбор связей')

#Т.К. linked_docs выбирает ВСЕ связи в проекте, что бы не получить одинаковые файлы, нужно убрать лишнее.
filt_linked_docs = []
check_appended_names = []
for linked_name in linked_names:
    name = linked_name.split(':')[0] 
    if (name in select_link_name) and (name not in check_appended_names): # нет в выбраных и в уже обработаных
        check_appended_names.append(name) # имена которые далее будут игнорироваться
        filt_linked_docs.append(linked_docs[linked_names.index(linked_name)].GetLinkDocument())

# Проверка Сведения о проекте
user = doc.Application.Username
names,ids,owner,wsIsOpens, wsIsVis, wsIsDefault, titles=[],[], [], [], [], [], []
try:
    for filt_linked_doc in filt_linked_docs:

        standard_worksets = FilteredWorksetCollector(filt_linked_doc).OfKind(WorksetKind.StandardWorkset).ToWorksets()
        doc_title = filt_linked_doc.Title

        for standard_workset in standard_worksets: # Проваливается в каждый WS документа
            if standard_workset.Name == 'Сведения о проекте':
                ow = standard_workset.Owner
                if ow != '': #and ow != user:
                    owner.append(standard_workset.Owner)
                    titles.append(doc_title)

                    # Еще можно проверить
                    # ids.append(standarWorkset.Id)
                    # wsIsOpens.append(standarWorkset.IsOpen)
                    # wsIsVis.append(standarWorkset.IsVisibleByDefault)
                    # if standarWorkset.IsDefaultWorkset == True:
                    #     wsIsDefault.append(standarWorkset.Name)
    out = '\n'.join([str(a) + '->' + str(b) for a,b in zip(titles,owner)])

    # Вывод отчета
    if owner:
        forms.alert('В файлах:\n{a}\nуказаный пользователь занял рабочий набор "Сведения о проекте".'.format(a = out))
    else:
        forms.alert('Все проверенные файлы свободны.')

except ArgumentNullException:
    forms.alert('Проверить выгруженый файл не возможно. Выберете те файлы, которые загружены в проект.')