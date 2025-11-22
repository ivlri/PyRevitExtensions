# -*- coding: utf-8 -*-
import clr
import sys
import os
from datetime import datetime
import time

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
clr.AddReference("RevitServices")
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

clr.AddReference("System")
from System import EventHandler
from Autodesk.Revit.DB.Events import FailuresProcessingEventArgs
from Autodesk.Revit.UI.Events import DialogBoxShowingEventArgs, TaskDialogShowingEventArgs
from Autodesk.Revit.UI import TaskDialog, UIApplication

from Autodesk.Revit.DB import *
from pyrevit import script, HOST_APP
import System.Windows.Forms as WinForms
import System.Drawing as Drawing
from System.Drawing import Font, Color
from System import Single, DateTime

# Добавляем логирование использования инструмента
# import os
# from functions._logger import ToolLogger
# ToolLogger(script_path=__file__).log()


output = script.get_output()
output.set_title("Открытие локальной копии с фильтрацией рабочих наборов")

# --- Функции для системных окон сообщений ---
def show_error(message, title="Ошибка"):
    WinForms.MessageBox.Show(message, title, 
                            WinForms.MessageBoxButtons.OK, 
                            WinForms.MessageBoxIcon.Error)

def show_warning(message, title="Внимание"):
    WinForms.MessageBox.Show(message, title, 
                            WinForms.MessageBoxButtons.OK, 
                            WinForms.MessageBoxIcon.Warning)

def show_info(message, title="Информация"):
    WinForms.MessageBox.Show(message, title, 
                            WinForms.MessageBoxButtons.OK, 
                            WinForms.MessageBoxIcon.Information)
    
# --- Обработчик сообщений ---
class FailureProcessor(IFailuresPreprocessor):
    def PreprocessFailures(self, failuresAccessor):
        hasFailure = False
        fma = list(failuresAccessor.GetFailureMessages())
        
        for fa in fma:
            try:
                failingElementIds = list(fa.GetFailingElementIds())
                if failingElementIds:
                    hasFailure = True
                    failuresAccessor.DeleteWarning(fa) # Удаление предупреждения из файла. ТОлько в текушей транзакции
            except Exception as ex:
                # print("\tОшибка при обработке предупреждения: {}".format(ex))
                continue
        
        # if hasFailure:
        #     print("\tВсе предупреждения были обработаны (удалены сообщения)")
        
        return FailureProcessingResult.Continue # Если не нужны логи, то оставить только эту строку

# Закрытие системных предепреждений
def on_failures(sender, args):
    processor = FailureProcessor()
    result = processor.PreprocessFailures(args.GetFailuresAccessor())
    args.SetProcessingResult(result)


# Esc/close при появлении окна
def on_dialog_box(sender, args):
    args.OverrideResult(2)


uiapp = HOST_APP.uiapp
app = uiapp.Application

#=== Исправления потери контекста после открытия окна - Начало части 1
import pyrevit
from pyrevit import DB, UI
from pyrevit import revit, forms, script
import wpf
from System import EventHandler
from Autodesk.Revit.DB.Events import FailuresProcessingEventArgs

original_uiapp_property = pyrevit._HostApplication.uiapp
ui_app = UIApplication(__revit__.Application)  
@property
def custom_uiapp(self):
    """Return UIApplication provided to the running command."""
    return ui_app

pyrevit._HostApplication.uiapp = custom_uiapp
#=== Исправления потери контекста после открытия окна - Конец части 1

#--- ОТписка от всех уведомлений
app.FailuresProcessing += EventHandler[FailuresProcessingEventArgs](on_failures)
uiapp.DialogBoxShowing += EventHandler[DialogBoxShowingEventArgs](on_dialog_box)
try:
    openFileDialog = WinForms.OpenFileDialog()
    openFileDialog.Title = "Выберите файлы Revit для пересохранения"
    openFileDialog.Filter = "Revit Files (*.rvt)|*.rvt"
    openFileDialog.InitialDirectory = os.path.join(os.environ["USERPROFILE"], "Рабочий стол")
    openFileDialog.Multiselect = True

    if openFileDialog.ShowDialog() != WinForms.DialogResult.OK or len(openFileDialog.FileNames) == 0:
        sys.exit()

    selected_paths = openFileDialog.FileNames
    valid_paths = []
    error_messages = []

    # Получаем пути уже открытых центральных моделей
    open_central_paths = []
    for doc in app.Documents:
        if doc.IsWorkshared:
            mp = doc.GetWorksharingCentralModelPath()
            if mp:
                user_path = ModelPathUtils.ConvertModelPathToUserVisiblePath(mp)
                open_central_paths.append(user_path)

    # Проверка каждого файла
    for path in selected_paths:
        # Фильтрация по расширению .rvt (без учета регистра)
        if not path.lower().endswith('.rvt'):
            # Можно добавить предупреждение, если нужно:
            # error_messages.append("Пропущен файл с неподходящим расширением:\n" + os.path.basename(path))
            continue

        if not os.path.isfile(path):
            error_messages.append("Файл не найден:\n" + os.path.basename(path))
            continue

        basic_info = BasicFileInfo.Extract(path)
        if not basic_info.IsCentral:
            error_messages.append("Не является файлом хранилищем:\n" + os.path.basename(path))
            continue

        if path in open_central_paths:
            error_messages.append("Файл уже открыт:\n" + os.path.basename(path))
            continue

        # Если всё прошло — добавляем к валидным
        valid_paths.append(path)

    # Если есть ошибки — показываем сообщение
    if error_messages:
        show_warning("Некоторые файлы были пропущены:\n\n" + "\n\n".join(error_messages))

    # Если не осталось ни одного валидного файла — выходим
    if not valid_paths:
        show_error("Нет подходящих файлов для открытия.")
        sys.exit()

    # Иначе продолжаем работу с valid_paths
    central_paths = valid_paths


    # -----------------------------
    # 📂 Продолжение открытия
    # -----------------------------
    deatach_central = DetachFromCentralOption().DetachAndPreserveWorksets

    wokset_config = WorksetConfiguration(WorksetConfigurationOption.CloseAllWorksets)

    options = OpenOptions()
    options.SetOpenWorksetsConfiguration(wokset_config)
    options.DetachFromCentralOption = deatach_central
    with forms.ProgressBar(title='Пересохранение файлов ({value} из {max_value})', cancellable=True) as pb:
        total = len(central_paths)
        idx = 0
        for central_path in central_paths:
            idx += 1
            pb.update_progress(idx, total)

            # Попытка открыть файл
            ModelPath = ModelPathUtils.ConvertUserVisiblePathToModelPath(central_path)

            # === Открытие файла ===
            document = app.OpenDocumentFile(ModelPath, options)

            worksharing_options = WorksharingSaveAsOptions()
            worksharing_options.SaveAsCentral = True

            save_as_options = SaveAsOptions() 
            save_as_options.SetWorksharingOptions(worksharing_options)
            save_as_options.OverwriteExistingFile = True

            # Сохраняем файл через "Сохранить как"
            document.SaveAs(central_path, save_as_options)   

            #--- Освободить все элементы
            relinquish = RelinquishOptions(document)
            relinquish.CheckedOutElements = True
            relinquish.FamilyWorksets = True
            relinquish.StandardWorksets = True
            relinquish.UserWorksets = True 

            transact_options = TransactWithCentralOptions()

            WorksharingUtils.RelinquishOwnership(document, relinquish, transact_options)

            document.Close()


except Exception:
    import traceback
    err_msg = traceback.format_exc()
    if document:
        document.Close()
    show_error("Ошибка:\n{0}".format(err_msg))
    sys.exit()

finally:
    # Дизлайк отписка 
    app.FailuresProcessing -= EventHandler[FailuresProcessingEventArgs](on_failures)
    uiapp.DialogBoxShowing -= EventHandler[DialogBoxShowingEventArgs](on_dialog_box)

    #=== Исправления потери контекста после открытия окна - Часть 2
    pyrevit._HostApplication.uiapp = original_uiapp_property