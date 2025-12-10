
# -*- coding: utf-8 -*-
__title__   = "Копированние моделей в фоне"

#IMPORTS
#==================================================

import os
import codecs

from Autodesk.Revit.DB import OpenOptions, WorksetConfiguration, WorksetConfigurationOption,\
    ModelPathUtils, FilteredElementCollector, View,Transaction, RevitLinkInstance, SaveAsOptions, Document
#from Autodesk.Revit.UI.Selection import *

# .NET Imports
import clr
clr.AddReference("System")
from System.Collections.Generic import List

#==================================================
#VARIABLES
#==================================================

uidoc = __revit__.ActiveUIDocument
app   = __revit__.Application

#==================================================
#FUNCTIONS
#==================================================
def find_rvt_files(directory):
    #Список всех rvt файлов и путей к нем
    rvt_files_name = []
    rvt_files_path = []

    for root, dirs, files in os.walk(directory):
        #print(root,files)
        for file in files:
            if file.endswith(".rvt"):
                rvt_files_path.append(os.path.join(root, file))
                rvt_files_name.append(file)
    
    rvt_files_dict = {
        'file_names': rvt_files_name,
        'file_paths': rvt_files_path
    }
    return rvt_files_dict

def open_model(file_copy_path):
    # Настройка опций открытия - отключение РБ
    options = OpenOptions()
    wokset_config = WorksetConfiguration(WorksetConfigurationOption.CloseAllWorksets)
    options.SetOpenWorksetsConfiguration(wokset_config)

    # Попытка открыть файл
    try:
        ModelPath = ModelPathUtils.ConvertUserVisiblePathToModelPath(file_copy_path)
        document = app.OpenDocumentFile(ModelPath, options)
        print('\nФайл {name_doc} открыт'.format(name_doc = document.Title))
        return document
    except Exception as ex:
        False
        print('\nНе удалось открыть файл: {eror}'.format(eror = ex))

def rename_view_to_navisworks(doc):
    try:
        # Получаем все виды в документе
        collector = FilteredElementCollector(doc)
        views = collector.OfClass(View).ToElements()

        # Удаляем вид Navisworks если он есть в файле 
        #view_to_delete = filter(lambda x : x.Name == "Navisworks", views)
        view_to_delete = next((view for view in views if view.Name == "Navisworks"), None)
        if view_to_delete:
            #with Transaction(doc, "Выровнять марки") as t:
                #t.Start()

            doc.Delete(view_to_delete.Id)

               # t.Commit()

            print('Был удален 1 вид Navisworks')
            
                # Ищем вид с таким же именем, как имя файла
            file_name = doc.Title
            for view in views:
                if view.Name == file_name:
                    view.Name = 'Navisworks'
                    break
            return True
        else: 
            print('При открытии файла вид Navisworks не был найден')
    except Exception as ex:
        print('Не удалось удалить вид Navisworks: {eror}'.format(eror = ex)) 
        return False

def remove_linked_files(doc):
    file_name = doc.Title
    rvtLinks = FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements()
    
    # Удаление не нужных связей
    try:
       # with Transaction(doc, "Удаление связей") as t:
            #t.Start()

        for rvtLink in rvtLinks:
            link_file_name = rvtLink.Name
            #link_id = rvtLink.GetLinkDocument()
            link_id = rvtLink.Id
            if not any(item in link_file_name for item in dictionary_match[file_name]):
                doc.Delete(link_id)

            #t.Commit()
        print('Ненужные связи удалены')
        return True
    except Exception as ex:
        print('Не удалось удалить связи: {eror}'.format(eror = ex)) 
        return False
    
def doc_save_as(doc,path,name):
    # Создаем полное имя файла
    try:
        full_path_save = path + '\\' + name
       # with Transaction(doc, "Сохранение файла") as t:
            #t.Start()

        # Сохраняем файл через "Сохранить как"
        save_as_options = SaveAsOptions()
        save_as_options.OverwriteExistingFile = True  # Перезаписать существующий файл
        doc.SaveAs(full_path_save, save_as_options)

            #t.Commit()
            
        doc.Close()
        print('\n Файл пересохранен')
    except Exception as ex:
        print('Не удалось сохранить файл: {eror}'.format(eror = ex)) 
        return False
#==================================================
#MAIN
#==================================================

dictionary_match = {
'01.Сборка_Общая':['_AR','_SC','_AS','_HVAC','_WSS'],
'02.Сборка Архитектура':['_AR'],
'03.1 Сборка_Конструктив':['_SC','_AS'],
'03.3 Сборка_Конструктив и Инженерные сети':['_SC','_AS','_HVAC','_WSS'],
'04.1 Сборка_Коробка здания':['_AR','_SC','_AS'],
'04.2 Сборка_Коробка здания и Инженерные сети':['_AR','_SC','_AS','_HVAC','_WSS'],
'05.Сборка_Отопление и Вентиляция':['_HVAC'],
'06.Сборка_Водоснабжение и Водоотведение':['_WSS'],
'07.Сборка_Общая Инженерные сети':['_HVAC','_WSS']
}
file_names_path = r'\\fs\bim\Projects\00.BIM_Export\Export_nwd\Имена файлов.txt'
#path_dir = r'\\fs\bim\Projects\EKB_SVK\PD\KV33\98.CRD\02_NWD\GP01'




try:
    count = 0
    #print(rvt_name)
    file_copy_path = r'\\fs\bim\Projects\OMSK_PKN\PD\GP1.2\98.CRD\02_NWD\01.Сборка_Общая.rvt'
    #copy_path = r'\\fs\bim\Projects\OMSK_PKN\PD\GP1.2\98.CRD\02_NWD'
    file_doc = open_model(file_copy_path) 
    file_name = file_doc.Title
    with Transaction(file_doc, "Пересохранение фалов") as t:
        t.Start()
        if file_doc:
            reme_bool = rename_view_to_navisworks(file_doc)
            if reme_bool:
                remove_linke_bool = remove_linked_files(file_doc)
                #print(remove_linke_bool)
                if remove_linke_bool:
                        # with Transaction(doc, "Сохранение файла") as t:
                #t.Start()
                    doc_save_as(file_doc,file_copy_path,file_name)
        #t.Commit()
        t.Dispose()
        count +=1 
except Exception as ex:
    print(ex) 

#f = codecs.open(file_name_path, 'r', "UTF-8")


