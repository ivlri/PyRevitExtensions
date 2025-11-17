
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

print('----- Активирован скрипт дробления файла FM на отдельные фалы -----\
      \nСейчас вас попросят выюрать путь к дирректории FM файла. Этот файл будет разделен следующим образом: \
      \n\t ..._FM -> 01.Сборка_Общая\
      \n\t ..._FM -> 02.Сборка_Архитектура\
      \n\t ..._FM -> 03.1 Сборка_Конструктив\
      \n\t ..._FM -> 03.3 Сборка_Конструктив и Инженерные сети\
      \n\t ..._FM -> 04.1 Сборка_Коробка здания\
      \n\t ..._FM -> 04.2 Сборка_Коробка здания и Инженерные сети\
      \n\t ..._FM -> 05.Сборка_Отопление и Вентиляция\
      \n\t ..._FM -> 06.Сборка_Водоснабжение и Водоотведение\
      \n\t ..._FM -> 07.Сборка_Общая Инженерные сети\
      \n\t ..._FM -> 99_AS\
      \n\t ..._FM -> 99_SC\n\
      \nПосле равзделения, все скопированные файлы пройдут обработку:\
      \n\t 1. Вид с именем файла будет переименован в Navisworks\
      \n\t 2. Будут удалены связи не относязиеся к данному файлу\
      \n\t 3. Файл будет пересохранен как файл хранилища\n\n\
      -----process-----\n\n')

path_to_folder_CRD = forms.pick_folder()
path_to_folder_NWD =  os.path.join(path_to_folder_CRD, '02_NWD')

#==================================================
#FUNCTIONS
#==================================================


# class FailuresPreprocessor(IFailuresPreprocessor):
#     def PreprocessFailures(self, failuresAccessor):
#         failuresAccessor.DeleteAllWarnings()
#         return FailureProcessingResult.Continue
    
class FailureProcessor(IFailuresPreprocessor):
    def PreprocessFailures(self, failuresAccessor):
        hasFailure = False
        fma = list(failuresAccessor.GetFailureMessages())
        
        for fa in fma:
            try:
                failingElementIds = list(fa.GetFailingElementIds())
                if failingElementIds:
                    hasFailure = True
                    failuresAccessor.DeleteWarning(fa)
            except Exception as ex:
                print("\tОшибка при обработке предупреждения: {}".format(ex))
                continue
        
        if hasFailure:
            print("\tВсе предупреждения были обработаны (удалены сообщения)")
        
        return FailureProcessingResult.Continue

def on_failures(sender, args):
    processor = FailureProcessor()
    result = processor.PreprocessFailures(args.GetFailuresAccessor())
    args.SetProcessingResult(result)

def on_dialog_box(sender, args):
    if isinstance(args, DialogBoxShowingEventArgs):
        dialog = args.Dialog
        if isinstance(dialog, TaskDialog):
            args.OverrideResult(1001)


def read_file_with_names(path):
    f = codecs.open(path, 'r', "UTF-8")
    out = [i.split('\n')[0] for i in f]

    return out


def get_file_for_copy():
    global path_to_folder_CRD

    copy_files = [file_name for file_name in os.listdir(path_to_folder_CRD)
            if ('.rvt' in file_name) and ('_FM' in file_name) and ('ALL' not in file_name)]
    
    return copy_files


def create_NWD_folders(): # будет использоваться если файл > 1
    global path_to_folder_CRD

    out = []
    path = os.path.join(path_to_folder_CRD, '02_NWD')

    for file_name in get_file_for_copy():
        folder_name = file_name.split('_')[-1].split('.')[0]
        folder_path = os.path.join(path, str(folder_name))
        try:
            os.makedirs(folder_path)
            out.append(folder_path)
        except:
            out.append(folder_path)
    return out


def create_folder_02NWD():
    folder_path = os.path.join(path_to_folder_CRD, '02_NWD')
    os.makedirs(folder_path)

    return folder_path


def create_need_CRDfolders():
    global path_to_folder_CRD

    if '02_NWD' not in os.listdir(path_to_folder_CRD):
        out1 = create_folder_02NWD()
    else:
        out1 = os.path.join(path_to_folder_CRD, '02_NWD')
    if len(get_file_for_copy()) > 1:
        out2 = create_NWD_folders()

    return [str(i) for i in out2] if len(get_file_for_copy()) > 1 else [str(out1)]


def copy_file(copy_paths, file_to_copy, new_names):
    count = 0
    what_update = 'all'.lower()

    # Если надо, то модно обновить только одну вложенную папку
    if len(copy_paths) > 1:
        what_update = forms.ask_for_string(
                            default='Введите имя папки сюда',
                            prompt='Какую из папок обновить:',
                            title='Пользовательскй ввод'
                        )
    # Процесс копирования
    for path_to_copy in copy_paths:
        if what_update.lower() == 'all':
            pass
        elif what_update not in str(path_to_copy):
            path_to_copy = ' '
        # try:
        f_name = file_to_copy[count]
        copy_file = os.path.join(path_to_folder_CRD, f_name)
        print('Файл {f_name} копируется в папку {copy_path}:'.format(f_name=f_name, 
                                                                    copy_path=path_to_copy))
        for name in new_names:
            new_file_name = os.path.join(path_to_copy, name)
            print(copy_file) 
            print(new_file_name)
            File.Copy(copy_file, new_file_name, True)
            print('\t##Скопирован: {name}'.format(name=name))
            count += 1
        # except Exception as ex:
        #     print(ex)



#Функции для пересохранения файлов 

def find_rvt_files(directory):
    # Список всех rvt файлов и путей к нем
    rvt_files_name = []
    rvt_files_path = []

    # Создание словаря содержащего пути и имена файлов в папке
    for root, dirs, files in os.walk(directory):
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
        view_to_delete = next((view for view in views if view.Name == "Navisworks"), None)
        if view_to_delete is not None:
            with Transaction(doc, "Удалить вид") as t:
                t.Start()

                doc.Delete(view_to_delete.Id)

                t.Commit()

            print('\t Был найден и удален вид Navisworks. Проверьте FM файл')
        else:
            pass 
            #print('\t При открытии файла вид Navisworks не был найден')

        # Ищем вид с таким же именем, как имя файла
        file_name = doc.Title
        spl = file_name.split('_')
        view_name = '_'.join(spl[0:len(spl) - 1])
        print(view_name)
        with Transaction(doc, "Переименовать вид") as t:
            t.Start()
            for view in views:
                if view.Name == view_name:
                    view.Name = 'Navisworks'
                    break
            t.Commit()

        print('\t Вид {name} был переименован в Navisworks'.format(name=view_name))
        return True
    
    except Exception as ex:
        print('\t Не удалось переименовать вид Navisworks: {eror}'.format(eror = ex)) 
        return False
    

def unique_item_id(list_elements):
    check_id = []
    lst = []
    for i in list_elements:
        if i.Id not in check_id:
            check_id.append(i.Id)
            lst.append(i)

    return lst
    

def get_link_type(doc):
    coll = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_RvtLinks).\
        WhereElementIsNotElementType().ToElements()

    types = []

    for c in coll:
        types.append(doc.GetElement(c.GetTypeId()))

    return types


def remove_linked_files(doc, dict):
    # Получение ключа для словаря имен
    file_name = doc.Title
    spl = file_name.split('_')
    key_match = '_'.join(spl[0:len(spl) - 1])

    rvtLinks_type = get_link_type(doc)
    uniq_Links_type = unique_item_id(rvtLinks_type)
    
    # Удаление не нужных связей
    try:
        with Transaction(doc, "Удаление связей") as t:
            t.Start()

            for rvtLink_type in uniq_Links_type:
                try:
                    link_name = rvtLink_type.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
                    link_id = rvtLink_type.Id
                    if not any(item in link_name for item in dict[key_match]):
                            #print(link_name)
                            doc.Delete(link_id)
                            continue
                except InvalidObjectException:
                    continue

            t.Commit()

            print('\t Лишние связи удалены')
            return True
    
        
    except Exception as ex:
        print('\t Не удалось удалить связи: {eror}'.format(eror = ex)) 
        return False
    

def doc_save_as(doc,path,name):
    try:
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
app.FailuresProcessing += EventHandler[FailuresProcessingEventArgs](on_failures)
# app.DialogBoxShowing += EventHandler[DialogBoxShowingEventArgs](on_dialog_box)
try:
    # Прогрессбар
    output = script.get_output()
    output.indeterminate_progress(True)

    # 1) Копирование файлов
    copy_file(create_need_CRDfolders(), get_file_for_copy(), read_file_with_names(pt_file_names))


    # 2) Пересохранение файлов

    dictionary_matching = {
    '01.Сборка_Общая':['_AR','_SC','_AS','_ AS','_HVAC','_WSS','_ESS'],
    '02.Сборка_Архитектура':['_AR'],
    '03.1 Сборка_Конструктив':['_SC','_AS','_ AS'],
    '03.3 Сборка_Конструктив и Инженерные сети':['_SC','_AS','_ AS','_HVAC','_WSS', '_ESS'],
    '04.1 Сборка_Коробка здания':['_AR','_SC','_AS','_ AS'],
    '04.2 Сборка_Коробка здания и Инженерные сети':['_AR','_SC','_AS','_ AS','_HVAC','_WSS', '_ESS'],
    '05.Сборка_Отопление и Вентиляция':['_HVAC', '_ESS'],
    '06.Сборка_Водоснабжение и Водоотведение':['_WSS'],
    '07.Сборка_Общая Инженерные сети':['_HVAC','_WSS', '_ESS'],
    '99_AS':['_AS','_ AS'],
    '99_SC':['_SC']
    }

    all_rvt_files = find_rvt_files(path_to_folder_NWD)
    count = 0

    # Проход по файлам
    for rvt_path in all_rvt_files['file_paths']:
        file_name = all_rvt_files['file_names'][count]
        file_doc = open_model(rvt_path)
        try:
            if file_doc:
                reme_bool = rename_view_to_navisworks(file_doc)
                if reme_bool:
                    remove_linke_bool = remove_linked_files(file_doc,dictionary_matching)
                    if remove_linke_bool:
                        doc_save_as(file_doc,rvt_path,file_name)
                        pass
            count +=1
        except:
            file_doc.close()

finally:
    app.FailuresProcessing -= EventHandler[FailuresProcessingEventArgs](on_failures)
    # uiapp.DialogBoxShowing -= EventHandler[DialogBoxShowingEventArgs](on_dialog_box)
    output.indeterminate_progress(False)



