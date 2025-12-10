
# -*- coding: utf-8 -*-
__title__   = "Копированние моделей в фоне"

#IMPORTS
#==================================================

import os
import codecs

from Autodesk.Revit.DB import *
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
    deatach_central = DetachFromCentralOption().DetachAndPreserveWorksets

    wokset_config = WorksetConfiguration(WorksetConfigurationOption.CloseAllWorksets)
    options = OpenOptions()
    options.SetOpenWorksetsConfiguration(wokset_config)
    options.DetachFromCentralOption = deatach_central

    # Попытка открыть файл
    try:
        ModelPath = ModelPathUtils.ConvertUserVisiblePathToModelPath(file_copy_path)
        document = app.OpenDocumentFile(ModelPath, options)
        
        print('\nФайл {name_doc} открыт'.format(name_doc = document.Title))
        return document
    
    except Exception as ex:
        print('\n Не удалось открыть файл: {eror}'.format(eror = ex))
        return False
    

def rename_view_to_navisworks(doc):
    try:
        # Получаем все виды в документе
        collector = FilteredElementCollector(doc)
        views = collector.OfClass(View).ToElements()

        # Удаляем вид Navisworks если он есть в файле 
        #view_to_delete = filter(lambda x : x.Name == "Navisworks", views)
        view_to_delete = next((view for view in views if view.Name == "Navisworks"), None)
        if view_to_delete is not None:
            with Transaction(doc, "Удалить вид") as t:
                t.Start()

                doc.Delete(view_to_delete.Id)

                t.Commit()
        else: 
            print('\t При открытии файла вид Navisworks не был найден')

        # Ищем вид с таким же именем, как имя файла
        file_name = doc.Title
        spl = file_name.split('_')
        view_name = '_'.join(spl[0:len(spl) - 1])

        with Transaction(doc, "Удалить вид") as t:
            t.Start()
            for view in views:
                if view.Name == view_name:
                    view.Name = 'Navisworks'
                    break
            t.Commit()

        print('\t Вид {name} был переименован в Navisworks'.format(name=view_name))
        return True
    
    except Exception as ex:
        print('\t Не удалось удалить вид Navisworks: {eror}'.format(eror = ex)) 
        return False
    
def get_link(doc):
    coll = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_RvtLinks).\
        WhereElementIsNotElementType().ToElements()

    insts, types = [], []

    for c in coll:
        insts.append(c.ToDSType(True))
        types.append(doc.GetElement(c.GetTypeId()))

    return [insts,types]


def remove_linked_files(doc):
    # Получение ключа для словаря имен
    file_name = doc.Title
    spl = file_name.split('_')
    key_match = '_'.join(spl[0:len(spl) - 1])

    rvtLinks = FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements()
    
    # Удаление не нужных связей
    try:
        with Transaction(doc, "Удаление связей") as t:
            t.Start()

            delets = []
            for rvtLink in rvtLinks:
                link_file_name = rvtLink.Name
                #link_id = rvtLink.GetLinkDocument()
                link_id = rvtLink.Id
                if not any(item in link_file_name for item in dictionary_match[key_match]):
                    #delets.append(doc.Delete(link_id))
                    del_id = doc.Delete(link_id)

            t.Commit()
        print(del_id)
        print('\t Ненужные связи удалены')
        return True
    
    except Exception as ex:
        print('\t Не удалось удалить связи: {eror}'.format(eror = ex)) 
        return False
    
    
def doc_save_as(doc,path,name):
    # Создаем полное имя файла
    try:
        #with Transaction(doc, "Сохранение файла") as t:
            #t.Start()

        # Настройка опций сохранения
        worksharing_options = WorksharingSaveAsOptions()
        worksharing_options.SaveAsCentral = True

        save_as_options = SaveAsOptions() 
        save_as_options.SetWorksharingOptions(worksharing_options)
        save_as_options.OverwriteExistingFile = True

        # Сохраняем файл через "Сохранить как"
        doc.SaveAs(path, save_as_options)   
        doc.Close()

        print('\t Файл {name} пересохранен'.format(name = name))
    except Exception as ex:
        print('\t Не удалось сохранить файл: {eror}'.format(eror = ex)) 
    
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
path_dir = r'\\fs\bim\Projects\EKB_SVK\PD\KV33\98.CRD\02_NWD\GP01'

all_rvt_files = find_rvt_files(path_dir)
count = 0
for rvt_path in all_rvt_files['file_paths']:
    file_name = all_rvt_files['file_names'][0]
    file_doc = open_model(rvt_path)
    if file_doc:
        reme_bool = rename_view_to_navisworks(file_doc)
        if reme_bool:
            remove_linke_bool = remove_linked_files(file_doc)
            if remove_linke_bool:
                doc_save_as(file_doc,rvt_path,file_name)
    
    count +=1 




