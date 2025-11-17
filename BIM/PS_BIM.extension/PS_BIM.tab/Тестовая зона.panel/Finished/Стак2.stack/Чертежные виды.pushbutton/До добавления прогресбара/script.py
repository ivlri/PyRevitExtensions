# -*- coding: utf-8 -*-

import os
import tempfile
import re
import time
import shutil

import wpf
from pyrevit import revit, forms, script

import System.Windows
from System.Windows.Forms import MessageBox, MessageBoxButtons, MessageBoxIcon, DialogResult
from System.Collections.Generic import List
from Autodesk.Revit import DB
from rpw.ui.forms import FlexForm, Label, ComboBox, Button, TaskDialog, CommandLink
from collections import OrderedDict, defaultdict

# Для обновления семейств
from System import EventHandler
from Autodesk.Revit.DB.Events import FailuresProcessingEventArgs


import clr
clr.AddReference("PresentationFramework")
clr.AddReference("WindowsBase")
clr.AddReference('System.Windows.Forms')

from Autodesk.Revit.UI import UIApplication
from System import Uri
from System.Windows import Window
from System.Windows.Media.Imaging import BitmapImage, BitmapCacheOption
from System.Windows.Media import RenderOptions, BitmapScalingMode
from System.Windows import WindowStartupLocation

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application
ui_app = UIApplication(__revit__.Application)  
user_name = ui_app.Application.Username

# Добавляем логирование использования инструмента
"""
import os
from functions._logger import ToolLogger
ToolLogger(script_path=__file__).log()
"""

# пути
script_dir = os.path.dirname(os.path.abspath(__file__))
xaml_file = os.path.join(script_dir, "SelectFromList.xaml")

appdata = os.environ.get('APPDATA')  # Получаем путь к %AppData%
preview_dir = os.path.join(appdata, "PS", "Preview")

if not os.path.exists(preview_dir):
    os.makedirs(preview_dir)

PATH_PREVIEWS = preview_dir


# теги для фильтрации чертежных видов по имени
keywords = []

    
# === Настройки путей
template_dirs = {
    'Шаблон КЖ': r'\\fs\public\Холдинг\ПоревитД\ТИМ\01_Библиотека\01_Рабочие задачи\KR_Арматура и жб',
    'Шаблон КМ': r'\\fs\public\Холдинг\ПоревитД\ТИМ\01_Библиотека\01_Рабочие задачи\ALL_Изделия металлические',
    'Шаблон АР/КР': r'\\fs\public\Холдинг\ПоревитД\ТИМ\01_Библиотека\01_Рабочие задачи\AR, KR_Шаблон',
}

if "_AR_" in doc.Title:
    template_order = ['Шаблон АР/КР', 'Шаблон КЖ', 'Шаблон КМ']
else:
    template_order = ['Шаблон КЖ', 'Шаблон АР/КР', 'Шаблон КМ']

ordered_template_dirs = OrderedDict((k, template_dirs[k]) for k in template_order)

# === UI Выбор шаблона
components = [
    Label('Выберите файл шаблона (где хранятся чертежные виды:'),
    ComboBox('Select_file', ordered_template_dirs, sort=False),
    Button('Подтвердить выбор')
]
form = FlexForm('Выбор файла шаблона', components)
form.show()

if not form.values or not form.values.get('Select_file'):
    forms.alert("Операция отменена.", title="Отмена")
    raise SystemExit()

selected_path = form.values['Select_file']


def find_latest_rvt_file(folder):
    rvt_files = [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.endswith('.rvt') and not re.search(r'\.\d{4}\.rvt$', f)
    ]
    if not rvt_files:
        return None
    return max(rvt_files, key=os.path.getmtime)


if os.path.isdir(selected_path):
    template_path = find_latest_rvt_file(selected_path)
else:
    template_path = selected_path

if not template_path or not os.path.exists(template_path):
    forms.alert("Файл шаблона не найден:\n{}".format(template_path), title="Ошибка")
    raise SystemExit()

# === Открытие файла шаблона
model_path = DB.ModelPathUtils.ConvertUserVisiblePathToModelPath(template_path)
open_opts = DB.OpenOptions()
open_opts.DetachFromCentralOption = DB.DetachFromCentralOption.DoNotDetach
source_doc = app.OpenDocumentFile(model_path, open_opts)


# === подмена символов чтобы привести имена в одинаковый вид
def normalize_name(name):
    for ch in ['.', '"', '*', '/']:
        name = name.replace(ch, '-')
    return name


# === Получение чертежных видов
all_views = DB.FilteredElementCollector(source_doc).OfClass(DB.View).WhereElementIsNotElementType().ToElements()
views = [v for v in all_views if v.ViewType == DB.ViewType.DraftingView and not v.IsTemplate]
normalized_view_dict = {normalize_name(view.Name): view for view in views}


if not views:
    source_doc.Close(False)
    forms.alert("В шаблоне не найдено чертежных видов.", title="Ошибка")
    raise SystemExit()





for view in views:
    export_options = DB.ImageExportOptions()
    export_options.ExportRange = DB.ExportRange.SetOfViews
    export_options.SetViewsAndSheets(List[DB.ElementId]([view.Id]))
    export_options.ImageResolution = DB.ImageResolution.DPI_150
    export_options.ZoomType = DB.ZoomFitType.FitToPage
    export_options.PixelSize = 720
    export_options.HLRandWFViewsFileType = DB.ImageFileType.PNG
    export_options.FitDirection = DB.FitDirectionType.Horizontal

    base_file_name = ""  # базовое имя файла для экспорта
    export_options.FilePath = os.path.join(preview_dir, base_file_name)


    source_doc.ExportImage(export_options)


for filename in os.listdir(preview_dir):
    if filename.endswith(".png"):
        old_path = os.path.join(preview_dir, filename)
        
        # Ищем " чертежные виды -" и всё, что до него, включая
        match = re.search(r'Чертежный вид \s*-\s*(.*)', filename)
        if match:
            new_name = match.group(1).strip()
            new_path = os.path.join(preview_dir, new_name)

            # Переименовываем
            try:
                os.rename(old_path, new_path)
            except Exception as e:
                print("Не удалось переименовать файл:", old_path, "->", new_path)
                print("Ошибка:", e)



class ImageItem(object):
    def __init__(self, filename):
        self.filename = filename          # полное имя файла с расширением
        self.name = os.path.splitext(filename)[0]  # имя без расширения
        self.checked = False


class PreviewForm(Window):

    def ImageContainer_MouseLeftButtonDown(self, sender, e):
        self._isDragging = True
        self._startPoint = e.GetPosition(sender)
        sender.CaptureMouse()

    def ImageContainer_MouseLeftButtonUp(self, sender, e):
        self._isDragging = False
        sender.ReleaseMouseCapture()

    def ImageContainer_MouseMove(self, sender, e):
        if self._isDragging:
            currentPoint = e.GetPosition(sender)
            dx = currentPoint.X - self._startPoint.X
            dy = currentPoint.Y - self._startPoint.Y
            self._startPoint = currentPoint

            self.imageTranslate.X += dx
            self.imageTranslate.Y += dy

    def ImageContainer_MouseWheel(self, sender, e):
        # Коэффициент ускоренного масштабирования
        zoom_speed = 1.2

        min_scale = 1.0
        max_scale = 20.0

        scale = self.imageScale
        translate = self.imageTranslate

        old_scale = scale.ScaleX

        # Получаем "шаг" прокрутки как дробь: e.Delta обычно кратен 120
        delta = e.Delta / 120.0

        # Пропорциональный зум
        if delta > 0:
            new_scale = old_scale * (zoom_speed ** delta)
        else:
            new_scale = old_scale / (zoom_speed ** (-delta))

        # Ограничиваем минимальный и максимальный зум
        new_scale = max(min_scale, min(max_scale, new_scale))

        if new_scale == old_scale:
            return

        # Если достигнут минимальный масштаб, сбрасываем сдвиг (центрируем)
        if abs(new_scale - min_scale) < 1e-6:
            translate.X = 0
            translate.Y = 0
        else:
            # Корректируем сдвиг, чтобы не прыгала картинка
            translate.X = translate.X * (new_scale / old_scale)
            translate.Y = translate.Y * (new_scale / old_scale)

        # Применяем новый масштаб
        scale.ScaleX = new_scale
        scale.ScaleY = new_scale



    def __init__(self):
        xaml_path = os.path.join(script_dir, "FormListImage.xaml")
        wpf.LoadComponent(self, xaml_path)
        self.WindowStartupLocation = WindowStartupLocation.CenterScreen

        self.Topmost = True  # Окно всегда поверх других
        self.Activate()

        self._isDragging = False
        self._startPoint = None



        self.image_files = self.load_image_files(keywords=keywords)
        self.ItemListView.ItemsSource = self.image_files
        self.OkButton.IsEnabled = False
        self.SelectedLegendNames = []

        # Подписываемся на событие закрытия окна
        self.Closing += self.OnWindowClosing

        self.ShowDialog()

    def OnWindowClosing(self, sender, e):
        # Очистка папки с превью
        try:
            if os.path.exists(preview_dir):
                for file_name in os.listdir(preview_dir):
                    file_path = os.path.join(preview_dir, file_name)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
        except Exception as ex:
            print("Ошибка при очистке папки превью:", ex)

    def load_image_files(self, keywords=None):

        if keywords is None:
            keywords = []

        if not os.path.exists(PATH_PREVIEWS):
            return []

        filtered_files = []
        for f in os.listdir(PATH_PREVIEWS):
            fname_lower = f.lower()
            if not fname_lower.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                continue
            # Проверяем ключевые слова
            if keywords:
                # Приводим ключевые слова к нижнему регистру для нечувствительного поиска
                if not any(kw.lower() in fname_lower for kw in keywords):
                    continue
            filtered_files.append(ImageItem(f))

        return filtered_files
        
    def load_image(self, filename):
        image_path = os.path.join(PATH_PREVIEWS, filename)
        if not os.path.exists(image_path):
            return None
        try:
            uri_path = "file:///" + image_path.replace("\\", "/")
            bitmap = BitmapImage()
            bitmap.BeginInit()
            bitmap.UriSource = Uri(uri_path)
            bitmap.CacheOption = BitmapCacheOption.OnLoad
            bitmap.EndInit()
            return bitmap
        except Exception:
            return None

    def ItemListBox_SelectionChanged(self, sender, e):
        selected = sender.SelectedItem
        if not selected:
            self.ItemImage.Source = None
            self.update_ok_button()
            return

        bitmap = self.load_image(selected.filename)
        self.ItemImage.Source = bitmap
        self.imageScale.ScaleX = 1
        self.imageScale.ScaleY = 1
        self.imageTranslate.X = 0
        self.imageTranslate.Y = 0

        self.update_ok_button()

    def update_ok_button(self):
        any_checked = any(item.checked for item in self.image_files)
        selected = self.ItemListView.SelectedItem
        self.OkButton.IsEnabled = any_checked or selected is not None




    def OkButton_Click(self, sender, e):
        # Получаем список отмеченных чекбоксов
        checked_items = [item.name for item in self.image_files if item.checked]

        if checked_items:
            selected_items = checked_items
        else:
            # Если ничего не отмечено, берем выбранный элемент из списка (SelectedItem)
            selected = self.ItemListView.SelectedItem
            selected_items = [selected.name] if selected else []

        if selected_items:
            self.SelectedLegendNames = selected_items  # <-- сохраняем результат

            #from System.Windows import MessageBox
            #MessageBox.Show("Вы выбрали:\n" + "\n".join(selected_items), "Результат")

        self.Close()

    def Cancel_Click(self, sender, args):
        self.Close()

    def CheckBox_Click(self, sender, e):
        self.update_ok_button()
        




# Запускаем окно выбора с превью чертежных видов
form = PreviewForm()

# Получаем список выбранных имён чертежных видов из окна
selected_names = form.SelectedLegendNames

if not selected_names:
    #forms.alert("Чертежные виды не выбраны.")
    source_doc.Close(False)
    raise SystemExit()

# Нормализуем имена, выбранные пользователем
normalized_selected_names = [normalize_name(name) for name in selected_names]

# Фильтруем чертежных видов по нормализованным именам
selected_views = [normalized_view_dict[name] for name in normalized_selected_names if name in normalized_view_dict]



if not selected_views:
    forms.alert("Выбранные чертежных видов не найдены в шаблоне.")
    source_doc.Close(False)
    raise SystemExit()

class DuplicateTypeNamesHandler(DB.IDuplicateTypeNamesHandler):
    def OnDuplicateTypeNamesFound(self, args):
        # Возвращаем DuplicateTypeAction.UseDestinationTypes,
        # чтобы использовать существующие типы в документе назначения без предупреждений
        return DB.DuplicateTypeAction.UseDestinationTypes

# Создаем экземпляр обработчика
duplicate_handler = DuplicateTypeNamesHandler()

copy_options = DB.CopyPasteOptions()
copy_options.SetDuplicateTypeNamesHandler(duplicate_handler)

#=== Обновление семейств
"""
Обновляет все семейства с указанного вида, запоминая, что уже было обновлено
"""
class FamilyLoadOptions(DB.IFamilyLoadOptions):
    'Класс для загрузки семейств'
    def __init__(self, over_parem_up=False, over_parem_under=False):
        self.overwriteParameterValues_up = over_parem_up
        self.overwriteParameterValues_under = over_parem_under

    def OnFamilyFound(self, familyInUse, overwriteParameterValues):
        "Поведение при обнаружении семейства в модели"
        # global is_OverwriteParameter
        overwriteParameterValues.Value = self.overwriteParameterValues_up
        return True

    def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
        "Поведение при обнаружении в модели общего семейства"
        overwriteParameterValues.Value = self.overwriteParameterValues_under
        if self.overwriteParameterValues_under:
            source.Value = DB.FamilySource.Family
        else: 
            source.Value = DB.FamilySource.Project

class FailureProcessor(DB.IFailuresPreprocessor):
    def PreprocessFailures(self, failuresAccessor):
        failure_messages = failuresAccessor.GetFailureMessages()
        for msg in failure_messages:
            if "Поведение зависимостей между" in msg.GetDescriptionText():
                failuresAccessor.DeleteWarning(msg)

        return DB.FailureProcessingResult.Continue
    
def on_failures(sender, args):
    processor = FailureProcessor()
    result = processor.PreprocessFailures(args.GetFailuresAccessor())
    args.SetProcessingResult(result)

app.FailuresProcessing += EventHandler[FailuresProcessingEventArgs](on_failures)

uploaded_famuly = []
for view in selected_views:
    collector = DB.FilteredElementCollector(document=source_doc, viewId=view.Id)
    family_instances = collector.OfClass(DB.FamilyInstance).ToElements()

    for element in family_instances:
        family = element.Symbol.Family
        if family.Id not in uploaded_famuly:
            # print(family.Name)
            doc_family_to_load = source_doc.EditFamily(family)
            try:
                options = FamilyLoadOptions(over_parem_up=False, over_parem_under=False)
                doc_family_to_load.LoadFamily(doc, options)
            except Exception as ex:
                print("Ошибка в обновлении семейства {}\n{}".format(view.Name,ex))
            finally:
                uploaded_famuly.append(family.Id)
                doc_family_to_load.Close(False)

# копируем с переименованием и удалением потому что ревит при копировании создает дубль вида. не получилось обойти поэтому сделано так
for view in selected_views:
    with DB.Transaction(doc, "Копирование чертежного вида '{}'".format(view.Name)) as t:
        t.Start()

        # 1. Копируем сам вид
        copied_view_ids = DB.ElementTransformUtils.CopyElements(
            source_doc,
            List[DB.ElementId]([view.Id]),
            doc,
            DB.Transform.Identity,
            copy_options
        )

        if not copied_view_ids or len(copied_view_ids) == 0:
            t.RollBack()
            continue

        copied_view_id = copied_view_ids[0]
        copied_view = doc.GetElement(copied_view_id)

        # 2. Переименовываем скопированный вид
        new_name = view.Name + "_copy"
        copied_view.Name = new_name

        # 3. Копируем элементы с исходного вида на скопированный вид
        collector = DB.FilteredElementCollector(source_doc, view.Id)
        element_ids = collector.ToElementIds()

        DB.ElementTransformUtils.CopyElements(
            view,
            element_ids,
            copied_view,
            DB.Transform.Identity,
            copy_options
        )

        # 4. Удаляем скопированный и переименованный вид
        doc.Delete(copied_view.Id)

        t.Commit()








source_doc.Close(False)
app.FailuresProcessing -= EventHandler[FailuresProcessingEventArgs](on_failures)