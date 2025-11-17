# -*- coding: utf-8 -*-
#==================================================
#IMPORTS
#==================================================
import clr

import sys

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from pyrevit import forms
from System import String
import os
import Autodesk.Windows as aw
from pyrevit import revit
#ModelCrecker api
mc_path = r"C:\Program Files (x86)\Autodesk\AIT\2022"
sys.path.append(mc_path)
clr.AddReference("AIT.ModelChecker.API")
clr.AddReference("AIT.ModelChecker.RevitAPI")
# clr.AddReference("AIT.Common.API")  # может потребоваться
from ADSK.AIT.ModelChecker.API import *
from ADSK.AIT.ModelChecker.API.Services.Implementation import PreBuiltOptionsService
from ADSK.AIT.ModelChecker.API.Services.Implementation import CheckSetService
from ADSK.AIT.ModelChecker.Revit.API.Services.Implementation import CheckSetLocationRepository
from ADSK.AIT.ModelChecker.Revit.API.Services.Implementation import RunStateRepository
from ADSK.AIT.ModelChecker.Revit.API.Services.Implementation import ReportRunRepository
from ADSK.AIT.ModelChecker.Revit.API.Services.Implementation import DocumentCheckRunner

doc   = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
uiapp = uidoc.Application
app   = __revit__.Application

#==================================================
#FUNCTIONS
#==================================================


def get_user_group(username):
    username_clean = username.lower()
    if any(name in username_clean for name in AR):
        return 'AR'
    if any(name in username_clean for name in SC):
        return 'SC'
    if any(name in username_clean for name in WSS):
        return 'WSS'
    if any(name in username_clean for name in HWAC):
        return 'HWAC'
    if any(name in username_clean for name in ESS):
        return 'ESS'
    return None


def get_check_path(doc_name, user_group):
    doc_name_upper = doc_name.upper()

    if user_group in ['AR', 'SC']:
        path_dict = paths[user_group]
        for key in sorted(path_dict.keys(), key=lambda x: -len(x)):
            if key.upper() in doc_name_upper:
                return path_dict[key]
        return next(iter(path_dict.values()))
    
    return paths.get(user_group)


def rvt_ribbon_structure():
    """
    Функция для поиска Id кнопки Revti что бы ее можно было запустить через api
    """
    ribbon = aw.ComponentManager.Ribbon
    print("===Структура ленты REVIT ===")
    
    for tab in ribbon.Tabs:
        
        if tab.Title =='совместимость':
            # print("\nВКЛАДКА: '{}'".format(tab.Title))
            for panel in tab.Panels: # хз как получить имя панели
                for item in panel.Source.Items: # Перебор по всем кнопкам
                    button_name = item.Text
                    button_name = button_name if isinstance(button_name,str) else ''
                    print("Кнопка: '{}'".format(button_name))
                    print(item.Id)


def launch_specific_button(button_id):
    """Запуск конкретной кнопки по известному ID"""    
    try:
        command_id = RevitCommandId.LookupCommandId(button_id)
        uiapp.PostCommand(command_id)
    except Exception as e:
        print("Ошибка: {}".format(str(e)))


#==================================================
#MAIN
#==================================================
#=== Return file patch by doc.Title and username
AR = ['chernova', 'stepanova','sidelnikova','mitchishnina','pitkina','legostaev1']
SC = ['vasilkovskaya', 
      'karnauhova_av', 
      'neustroeva',
      'gavrilovskaya',
      'vashchenko_sa',
      'polyakov',
      'chelovyan',
      'stradova',
      'vakarina',
      'vashchenko',
      'ushakov',
      'rybakov',
      'lobov'
      ]
WSS = ['gribacheva','krotenko','shkavro','medvedev']
HWAC = ['strelbitskaya','shahtarin','turusheva']
ESS = ['mansurova']

paths = {
    'AR': {
        '_AR_': r"\\fs\public\Холдинг\ПоревитД\ТИМ\01_Библиотека\01_Рабочие задачи\ALL_Общие проверки файлов\MC_01_Проверка файла AR для Архитектора_V1.0.xml",
        '_AR_Rooms': r"\\fs\public\Холдинг\ПоревитД\ТИМ\01_Библиотека\01_Рабочие задачи\ALL_Общие проверки файлов\MC_06_Проверка файла Rooms_V1.1.xml"
    },
    'SC': {
        '_AR_': r"\\fs\public\Холдинг\ПоревитД\ТИМ\01_Библиотека\01_Рабочие задачи\ALL_Общие проверки файлов\MC_02_Проверка файла AR для ПГС_V1.1.xml",
        '_SC_': r"\\fs\public\Холдинг\ПоревитД\ТИМ\01_Библиотека\01_Рабочие задачи\ALL_Общие проверки файлов\MC_03_Проверка файла SC_V1.2.xml",
        '_AS_': r"\\fs\public\Холдинг\ПоревитД\ТИМ\01_Библиотека\01_Рабочие задачи\ALL_Общие проверки файлов\MC_04_Проверка файла AS_V1.0.xml"
    },
    'WSS': r"\\fs\public\Холдинг\ПоревитД\ТИМ\01_Библиотека\01_Рабочие задачи\ALL_Общие проверки файлов\MC_05_Проверка файла MEP_V1.1.xml",
    'HWAC': r"\\fs\public\Холдинг\ПоревитД\ТИМ\01_Библиотека\01_Рабочие задачи\ALL_Общие проверки файлов\MC_05_Проверка файла MEP_V1.1.xml",
    'ESS': r"\\fs\public\Холдинг\ПоревитД\ТИМ\01_Библиотека\01_Рабочие задачи\ALL_Общие проверки файлов\MC_01_Проверка файла AR для Архитектора_V1.0.xml"
}
doc_name = doc.Title
username = app.Username.lower().strip()

user_group = get_user_group(username)
if not user_group:
    forms.alert("Пользователь {} - не найден в списках. Назначение правила по умолчанию.".format(username))
    selected_path = paths['AR']['_AR_'] 
else:
    selected_path = get_check_path(doc_name, user_group)
with forms.ProgressBar(indeterminate=True, cancellable=True) as pb:
    # pb._title = 'Подготовка модели'
    #=== Changing repo in file
    location_repo = CheckSetLocationRepository(doc)
    path = location_repo.SaveCheckSetLocation(selected_path)
    checkset_path = location_repo.GetCurrentCheckSetLocation()

    #=== Check config
    prebuilt_service = PreBuiltOptionsService()
    service = CheckSetService(prebuilt_service)
    checkset = service.GetCheckSet(checkset_path)

    #=== Run check
    check_runner = DocumentCheckRunner(doc)
    report_run = check_runner.RunChecks(False, checkset)

    repo = ReportRunRepository(doc, service)
    repo.SaveRun(report_run)

    #=== Report
    button_id = "CustomCtrl_%CustomCtrl_%совместимость%Проверка модели%MCXR_ViewReport"
    launch_specific_button(button_id)


