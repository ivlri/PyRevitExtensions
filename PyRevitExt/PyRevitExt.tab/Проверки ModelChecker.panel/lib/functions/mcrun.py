# -*- coding: utf-8 -*-
#==================================================
#IMPORTS
#==================================================
import clr
import sys
import os

from pyrevit import revit
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from pyrevit import forms
from System import String

#ModelCrecker api
mc_path = r"C:\Program Files (x86)\Autodesk\AIT\2022"
sys.path.append(mc_path)
clr.AddReference("AIT.ModelChecker.API")
clr.AddReference("AIT.ModelChecker.RevitAPI")

from ADSK.AIT.ModelChecker.API import *
from ADSK.AIT.ModelChecker.API.Services.Implementation import PreBuiltOptionsService
from ADSK.AIT.ModelChecker.API.Services.Implementation import CheckSetService
from ADSK.AIT.ModelChecker.Revit.API.Services.Implementation import CheckSetLocationRepository
from ADSK.AIT.ModelChecker.Revit.API.Services.Implementation import RunStateRepository
from ADSK.AIT.ModelChecker.Revit.API.Services.Implementation import ReportRunRepository
from ADSK.AIT.ModelChecker.Revit.API.Services.Implementation import DocumentCheckRunner


class MCRunner():
    modes = {
        'ALL':'Общая проверка файла',
        'AR':'Проверка файла AR для Архитектора',
        'AR_Rooms':'Проверка файла Rooms',
        'AR_ПГС':'Проверка файла AR для ПГС',
        'SC':'Проверка файла SC',
        'AS':'Проверка файла AS',
        'MEP':'Проверка файла MEP'
    }
    def __init__(self, doc, uiapp, mode):
        self.doc = doc
        self.uiapp = uiapp
        self.mode = mode
        self.folder = r'\\fs\public\Холдинг\ПоревитД\ТИМ\01_Библиотека\01_Рабочие задачи\ALL_Общие проверки файлов'
        self.button_id = "CustomCtrl_%CustomCtrl_%совместимость%Проверка модели%MCXR_ViewReport"

    def _set_mode(self):
        for file in os.listdir(self.folder):
            if self.modes[self.mode] in file:
                return os.path.join(self.folder,file)
            
        forms.alert('Не найден файл проверок!')
        sys.exit()

    def rvt_ribbon_structure(self):
        """
        Функция для поиска Id кнопки Revti что бы ее можно было запустить через api
        """
        ribbon = aw.ComponentManager.Ribbon
        print("===Структура ленты REVIT ===")
        
        for tab in ribbon.Tabs:
            
            if tab.Title =='совместимость':
                print("\nВкладка: '{}'".format(tab.Title))
                for panel in tab.Panels: # хз как получить имя панели
                    for item in panel.Source.Items: # Перебор по всем кнопкам
                        button_name = item.Text
                        button_name = button_name if isinstance(button_name,str) else ''
                        print("Кнопка: '{}'\n ID:".format(button_name,item.Id))

    def _launch_specific_button(self):
        """Запуск конкретной кнопки по известному ID"""    
        try:
            command_id = RevitCommandId.LookupCommandId(self.button_id)
            self.uiapp.PostCommand(command_id)
        except Exception as e:
            print("Ошибка: {}".format(str(e)))

    def run(self):
        selected_path = self._set_mode()
        """Запуск проверки"""
        #=== Changing repo in file
        location_repo = CheckSetLocationRepository(self.doc)
        path = location_repo.SaveCheckSetLocation(selected_path)
        checkset_path = location_repo.GetCurrentCheckSetLocation()

        #=== Check config
        prebuilt_service = PreBuiltOptionsService()
        service = CheckSetService(prebuilt_service)
        checkset = service.GetCheckSet(checkset_path)

        #=== Run check
        check_runner = DocumentCheckRunner(self.doc)
        report_run = check_runner.RunChecks(False, checkset)

        repo = ReportRunRepository(self.doc, service)
        repo.SaveRun(report_run)

        #=== Report
        self._launch_specific_button()


