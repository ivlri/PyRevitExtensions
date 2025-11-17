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
from Autodesk.Revit.UI import TaskDialog

from Autodesk.Revit.DB import (
    ModelPathUtils,
    WorksharingUtils,
    WorksetConfiguration,
    WorksetConfigurationOption,
    OpenOptions,
    BasicFileInfo,
    IFailuresPreprocessor,
    FailureProcessingResult
)
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

# Оформить подписку
app.FailuresProcessing += EventHandler[FailuresProcessingEventArgs](on_failures)
uiapp.DialogBoxShowing += EventHandler[DialogBoxShowingEventArgs](on_dialog_box)

try:
    openFileDialog = WinForms.OpenFileDialog()
    openFileDialog.Title = "Выберите файлы Revit для открытия"
    openFileDialog.Filter = "Revit Files (*.rvt)|*.rvt"
    openFileDialog.InitialDirectory = os.path.join(os.environ["USERPROFILE"], "Рабочий сто")
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
    # 🕓 Выбор времени запуска
    # -----------------------------
    dt_form = WinForms.Form()
    dt_form.Text = "Выбор времени открытия"
    dt_form.Width = 350
    dt_form.Height = 160
    dt_form.StartPosition = WinForms.FormStartPosition.CenterScreen
    dt_form.FormBorderStyle = WinForms.FormBorderStyle.FixedDialog
    dt_form.MaximizeBox = False
    dt_form.MinimizeBox = False
        

    label = WinForms.Label()
    label.Text = "Выберите дату и время открытия:"
    label.Height = 50
    label.Dock = WinForms.DockStyle.Top
    label.TextAlign = Drawing.ContentAlignment.MiddleCenter
    label.Font = Font("Arial", Single(12), Drawing.FontStyle.Bold)
    label.Padding = WinForms.Padding(0, 10, 0, 5)
    dt_form.Controls.Add(label)

    dt_picker = WinForms.DateTimePicker()
    dt_picker.Format = WinForms.DateTimePickerFormat.Custom
    dt_picker.CustomFormat = "dd.MM.yyyy    HH:mm"
    dt_picker.Width = 150
    dt_picker.Value = DateTime(DateTime.Now.AddDays(1).Year,
                           DateTime.Now.AddDays(1).Month,
                           DateTime.Now.AddDays(1).Day,
                           8, 0, 0)

    dt_picker.Location = Drawing.Point(95, 55)

    ok_button = WinForms.Button()
    ok_button.Text = "ОК"
    ok_button.Dock = WinForms.DockStyle.Bottom
    ok_button.DialogResult = WinForms.DialogResult.OK

    dt_form.Controls.Add(label)
    dt_form.Controls.Add(dt_picker)
    dt_form.Controls.Add(ok_button)
    dt_form.AcceptButton = ok_button

    if dt_form.ShowDialog() != WinForms.DialogResult.OK:
        show_error("Время не выбрано, операция прервана.")
        sys.exit()

    def net_to_py_datetime(net_dt):
        return datetime(
            net_dt.Year,
            net_dt.Month,
            net_dt.Day,
            net_dt.Hour,
            net_dt.Minute,
            net_dt.Second
        )

    target_time = net_to_py_datetime(dt_picker.Value)
   
   
    # -----------------------------
    # ⏳ Окно таймера с полем ключевых слов
    # -----------------------------
    form = WinForms.Form()
    form.Text = "Отсчет до открытия"
    form.Width = 350
    form.Height = 260
    form.StartPosition = WinForms.FormStartPosition.CenterScreen
    form.FormBorderStyle = WinForms.FormBorderStyle.FixedDialog
    form.MaximizeBox = False
    form.MinimizeBox = False

    # Метка обратного отсчета
    label = WinForms.Label()
    label.Font = Font("Arial", Single(12), Drawing.FontStyle.Bold)
    label.Dock = WinForms.DockStyle.Top
    label.Height = 40
    label.TextAlign = Drawing.ContentAlignment.MiddleCenter
    form.Controls.Add(label)

    # Метка для поля ключевых слов
    keywords_label = WinForms.Label()
    keywords_label.Text = "Укажите рабочие наборы которые следует закрыть \nПеречислите их через запятую. Регистр не учитывается"
    keywords_label.Location = Drawing.Point(10, 40)
    keywords_label.AutoSize = True
    form.Controls.Add(keywords_label)

    # Поле ввода ключевых слов
    keywords_box = WinForms.TextBox()
    keywords_box.Text = ""
    keywords_box.Width = 310
    keywords_box.Height = 60
    keywords_box.Multiline = True
    keywords_box.Location = Drawing.Point(10, 80)
    form.Controls.Add(keywords_box)

    # Функция для добавления ключевых слов
    def append_keyword(text):
        current = keywords_box.Text.strip()
        if current:
            # Удаляем лишние пробелы, чтобы избежать дублирования
            items = [i.strip().lower() for i in current.split(',')]
            if text.lower() not in items:
                keywords_box.Text = current + ", " + text
        else:
            keywords_box.Text = text

    # Кнопка "Связи"
    button_sv = WinForms.Button()
    button_sv.Text = "Связи"
    button_sv.Width = 70
    button_sv.Location = Drawing.Point(10, 150)
    button_sv.Click += lambda s, e: append_keyword("Связь")
    form.Controls.Add(button_sv)

    # Кнопка "Арх"
    button_arh = WinForms.Button()
    button_arh.Text = "MEP"
    button_arh.Width = 70
    button_arh.Location = Drawing.Point(90, 150)
    button_arh.Click += lambda s, e: append_keyword("MEP")
    form.Controls.Add(button_arh)

    # Кнопка "ОВ"
    button_ov = WinForms.Button()
    button_ov.Text = "ОВ"
    button_ov.Width = 70
    button_ov.Location = Drawing.Point(170, 150)
    button_ov.Click += lambda s, e: append_keyword("HVAC")
    form.Controls.Add(button_ov)

    # Кнопка "СК"
    button_sk = WinForms.Button()
    button_sk.Text = "ВК"
    button_sk.Width = 70
    button_sk.Location = Drawing.Point(250, 150)
    button_sk.Click += lambda s, e: append_keyword("WSS")
    form.Controls.Add(button_sk)


    # Кнопка "Открыть сейчас"
    open_now_button = WinForms.Button()
    open_now_button.Text = "Открыть сейчас"
    open_now_button.Height = 30
    open_now_button.Dock = WinForms.DockStyle.Bottom

    opened_now = [False]
    cancelled = [False]

    def open_now(sender, event):
        opened_now[0] = True
        cancelled[0] = False
        timer.Stop()
        form.Close()

    open_now_button.Click += open_now
    form.Controls.Add(open_now_button)

    # Закрытие формы
    def on_form_closing(sender, args, target=target_time):
        if (target - datetime.now()).total_seconds() > 0 and not opened_now[0]:
            cancelled[0] = True
        timer.Stop()

    form.FormClosing += on_form_closing

    # Обновление метки времени
    def update_label(target=target_time):
        remaining = int((target - datetime.now()).total_seconds())
        if remaining > 0:
            days, rem = divmod(remaining, 86400)
            hours, rem = divmod(rem, 3600)
            minutes, seconds = divmod(rem, 60)

            parts = []
            if days > 0:
                parts.append("{0} дн.".format(days))
            if hours > 0 or days > 0:
                parts.append("{0} ч.".format(hours))
            if minutes > 0 or hours > 0 or days > 0:
                parts.append("{0} мин.".format(minutes))
            parts.append("{0} сек.".format(seconds))

            label.Text = "Открытие через " + " ".join(parts)
        else:
            label.Text = "Открытие..."

    # Таймер
    def timer_tick(sender, event, target=target_time):
        remaining = (target - datetime.now()).total_seconds()
        if remaining > 0:
            update_label(target)
        else:
            timer.Stop()
            form.Close()

    timer = WinForms.Timer()
    timer.Interval = 1000
    timer.Tick += timer_tick
    update_label()
    timer.Start()
    form.ShowDialog()

    if cancelled[0]:
        show_error("Открытие отменено пользователем.")
        sys.exit()

    # -----------------------------
    # 📂 Продолжение открытия
    # -----------------------------
    for central_path in central_paths:
        basic_info = BasicFileInfo.Extract(central_path)
        if not basic_info.IsCentral:
            show_warning("Пропущен нецентральный файл:\n{0}".format(central_path))
            continue

        if central_path in open_central_paths:
            show_warning("Файл уже открыт: {0}".format(central_path))
            continue

        # === Создание локальной копии ===
        now = datetime.now()
        timestamp = now.strftime("%d%b%Y_%H%M%S")

        central_model_path = ModelPathUtils.ConvertUserVisiblePathToModelPath(central_path)

        local_folder = os.path.join(os.environ["USERPROFILE"], "Documents")
        central_filename = os.path.basename(central_path)
        local_filename = central_filename.replace(".rvt", "_открытие по таймеру_{0}.rvt".format(timestamp))
        local_path_full = os.path.join(local_folder, local_filename)
        local_model_path = ModelPathUtils.ConvertUserVisiblePathToModelPath(local_path_full)

        WorksharingUtils.CreateNewLocal(central_model_path, local_model_path)

        # === Фильтрация по ключевым словам ===
        keywords_raw = keywords_box.Text.strip()
        if keywords_raw:
            hidden_keywords = [kw.strip().lower() for kw in keywords_raw.split(",")]
        else:
            hidden_keywords = []

        worksets_info = WorksharingUtils.GetUserWorksetInfo(local_model_path)

        worksets_to_open = []
        if '7250' not in hidden_keywords:
            for ws in worksets_info:
                ws_name_lower = ws.Name.lower()
                if not any(kw in ws_name_lower for kw in hidden_keywords):
                    worksets_to_open.append(ws.Id)
        

        workset_config = WorksetConfiguration(WorksetConfigurationOption.CloseAllWorksets)
        workset_config.Open(worksets_to_open)

        open_options = OpenOptions()
        open_options.SetOpenWorksetsConfiguration(workset_config)

        # === Открытие файла ===
        uidoc = uiapp.OpenAndActivateDocument(local_model_path, open_options, False)


except Exception:
    import traceback
    err_msg = traceback.format_exc()
    show_error("Ошибка:\n{0}".format(err_msg))
    sys.exit()

finally:
    # Дизлайк отписка 
    app.FailuresProcessing -= EventHandler[FailuresProcessingEventArgs](on_failures)
    uiapp.DialogBoxShowing -= EventHandler[DialogBoxShowingEventArgs](on_dialog_box)