
# -*- coding: utf-8 -*-
__title__   = "Копированние моделей в фоне(Временно не работает)"

#==================================================
#IMPORTS
#==================================================

import os
import codecs

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import TaskDialog
from Autodesk.Revit.Exceptions import OperationCanceledException, InvalidObjectException

# .NET
import clr
clr.AddReference("System")
from System import EventHandler
from Autodesk.Revit.DB.Events import FailuresProcessingEventArgs
from System.Collections.Generic import List
from System.IO import File

# pyrevit
from pyrevit import forms
from pyrevit import script


#==================================================
#VARIABLES
#==================================================

#uidoc = __revit__.ActiveUIDocument
app   = __revit__.Application

pt_file_names = r"\\fs\bim\Projects\00.BIM_Export\Export_nwd\Имена файлов.txt"

print('----- Активирован скрипт на создание локальных копий FM_Tangle файла-----\
      \nСейчас вас попросят выбрать FM файл, после чего начнется копирование. \
      \nПосле равзделения, все скопированные файлы пройдут обработку:\
      \n-----process-----\n\n')

central_path = forms.pick_file(file_ext='rvt')

#==================================================
#FUNCTIONS
#==================================================


#==================================================
#MAIN
#==================================================
try:
    # Прогрессбар
    output = script.get_output()
    output.indeterminate_progress(True)

    f_names = [
        "Укрупненный",
        'Ниже отм. 0,000',
        'Коробка',
        'Кровля',
        'Фасады',
        'Внутренняя отделка',
        'Металл',
        'ОВ',
        'ВК'
    ]

    patch, central_filename = os.path.split(central_path)
    for name in f_names:
        central_model_path = ModelPathUtils.ConvertUserVisiblePathToModelPath(central_path)
        # new_name = r'\01_Tangl\{}_{}.rvt'.format(central_filename.split('.rvt')[0], name)
        new_name = r'\{}_{}.rvt'.format(central_filename.split('.rvt')[0], name)
        local_model_path = ModelPathUtils.ConvertUserVisiblePathToModelPath(patch + new_name)
        WorksharingUtils.CreateNewLocal(central_model_path, local_model_path)
        print("Создан файл:{}".format(new_name))
finally:
    # uiapp.DialogBoxShowing -= EventHandler[DialogBoxShowingEventArgs](on_dialog_box)
    output.indeterminate_progress(False)



