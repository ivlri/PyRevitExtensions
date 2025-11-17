# -*- coding: utf-8 -*-
#==================================================
#IMPORTS
#==================================================

import clr
clr.AddReference("System.Collections")

import System
clr.AddReference("RevitAPI")
import Autodesk

clr.AddReference("RevitAPIUI")

import os
import locale
import codecs
from datetime import datetime

from System.Collections.Generic import List

from pyrevit import forms
from pyrevit import revit, DB, UI
from pyrevit.forms import ProgressBar

from Autodesk.Revit.DB import *
from Autodesk.Revit.Exceptions import OperationCanceledException

doc = revit.doc
uidoc = __revit__.ActiveUIDocument
uiapp   = __revit__ 
app   = __revit__.Application
#==================================================
#FUNCTIONS
#==================================================


def find_rvt_files(directory):
    # Список всех rvt файлов и путей к нем
    rvt_files_name = []
    rvt_files_path = []

    # Создание словаря содержащего пути и имена файлов в папке
    for root, dirs, files in os.walk(directory):
        if len(directory) == len(root):
            for file in files:
                if file.endswith(".rvt"):
                    rvt_files_path.append(os.path.join(root, file))
                    rvt_files_name.append(file)
    
    rvt_files_dict = {
        'file_names': rvt_files_name,
        'file_paths': rvt_files_path
    }
    return rvt_files_dict


def workset_to_open(fpath, parts_of_names):
    workset_config = WorksetConfiguration(WorksetConfigurationOption.CloseAllWorksets)
    #deatach_central = DetachFromCentralOption().DoNotDetach
    options = OpenOptions()

    if parts_of_names.lower() == 'все':
        options.SetOpenWorksetsConfiguration(workset_config)

    else:
        worksets = WorksharingUtils.GetUserWorksetInfo(FilePath(fpath))

        list_worksets_to_open = List[WorksetId]()
        for ws in worksets:
            name = ws.Name
            if all(part not in name for part in parts_of_names.split(',')):
                list_worksets_to_open.Add(ws.Id)

        workset_config.Open(list_worksets_to_open)
        
        options.SetOpenWorksetsConfiguration(workset_config)

    return options

def get_prodloc_path_from_ini():
    ini_file_path = str(app.CurrentUsersDataFolderPath) + '\\Revit.ini'  

    with codecs.open(ini_file_path, 'r', encoding='utf-16-le') as f:
        return next((line.strip().split('=')[1] for line in f if line.startswith('ProjectPath=')), False)
    

def get_date():
    months = {
    1: 'Jan',
    2: 'февраля',
    3: 'марта',
    4: 'апреля',
    5: 'мая',
    6: 'июня',
    7: 'июля',
    8: 'августа',
    9: 'сентября',
    10: 'октября',
    11: 'ноября',
    12: 'декабря'
    }

    now = datetime.now()

    formatted_time = "{}{}{}_{}-{:02}".format(now.day, months[now.month], now.year, now.hour, now.minute)
    # formatted_time = "{}{}{}_{}{:02}{}".format(now.day, months[now.month], now.year, now.hour, now.minute, now.second)
    return formatted_time


#==================================================
#MAIN
#==================================================

path_to_folder = forms.pick_folder()
dir_revit_file_info = find_rvt_files(path_to_folder)

file_names = dir_revit_file_info['file_names']
file_paths = dir_revit_file_info['file_paths']

#Выбор файлов для открытия
select_file_name = forms.SelectFromList.show(sorted(dir_revit_file_info['file_names']),
                                multiselect=True,
                                button_name='Подтвердить выбор файлов')

fpaths = [file_paths[file_names.index(file_name)] for file_name in file_names if file_name in select_file_name]

# Get workset names to close
parts_of_names = forms.ask_for_string(
    default='00_,01_,02_,03_,Связь',
    prompt='Введите часть, что содержится в имени рабочего набора, который нужно закрыть:',
    title='Выбор рабочих наборов для закрытия'
)

for fpath in fpaths:
    model_name = os.path.basename(fpath).split('.rvt')[0] + '_' +  app.Username + '_' +  get_date() + '.rvt'
    locfile_path = get_prodloc_path_from_ini() + '\\' + model_name

    WorksharingUtils.CreateNewLocal(FilePath(fpath),FilePath(locfile_path))
    
    uiapp.OpenAndActivateDocument(FilePath(locfile_path), workset_to_open(locfile_path,parts_of_names), False)

# get_prod_path_from_ini()