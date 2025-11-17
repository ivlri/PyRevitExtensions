# -*- coding: utf-8 -*-
import clr
import os
import tempfile
from System.Collections.Generic import List

import shutil
from pyrevit import revit

clr.AddReference('System.Windows.Forms')
from System.Windows.Forms import MessageBox, MessageBoxButtons, MessageBoxIcon, DialogResult

from Autodesk.Revit import DB
from pyrevit import revit, forms, script
from rpw.ui.forms import FlexForm, Label, ComboBox, Button, TaskDialog, CommandLink
from collections import OrderedDict, defaultdict
import re
import time
from Autodesk.Revit.UI import UIApplication


clr.AddReference("PresentationFramework")
clr.AddReference("WindowsBase")
import wpf
from System.Windows import Window
from System import Uri

from System.Windows.Media.Imaging import BitmapImage, BitmapCacheOption
from System.Windows.Media import RenderOptions, BitmapScalingMode
from System.Windows import WindowStartupLocation

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application
ui_app = UIApplication(__revit__.Application)  
user_name = ui_app.Application.Username

# путь к XAML рядом со скриптом
script_dir = os.path.dirname(os.path.abspath(__file__))
xaml_file = os.path.join(script_dir, "SelectFromList.xaml")


    
# === Настройки путей
template_dirs = {
    'Шаблон КЖ': r'\\fs\public\Холдинг\ПоревитД\ТИМ\01_Библиотека\01_Рабочие задачи\KR_Арматура и жб',
    'Шаблон КМ': r'\\fs\public\Холдинг\ПоревитД\ТИМ\01_Библиотека\01_Рабочие задачи\ALL_Изделия металлические',
    'Шаблон АР/КР': r'\\fs\public\Холдинг\ПоревитД\ТИМ\01_Библиотека\01_Рабочие задачи\AR, KR_Шаблон',
}
template_order = ['Шаблон КЖ', 'Шаблон АР/КР', 'Шаблон КМ']
ordered_template_dirs = OrderedDict((k, template_dirs[k]) for k in template_order)

# === UI Выбор шаблона
components = [
    Label('Выберите файл шаблона (где хранятся легенды):'),
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


def normalize_name(name):
    return name.replace('.', '-').replace('"', '-').replace('*', '-')
# === Получение легенд
all_legends = DB.FilteredElementCollector(source_doc).OfClass(DB.View).WhereElementIsNotElementType()\
    .ToElements()
legends = [v for v in all_legends if v.ViewType == DB.ViewType.Legend and not v.IsTemplate]

# Создаем словарь нормализованных имен легенд -> объекты легенд
normalized_legend_dict = {normalize_name(legend.Name): legend for legend in legends}


if not legends:
    #source_doc.Close(False)
    forms.alert("В шаблоне не найдено легенд.", title="Ошибка")
    raise SystemExit()



# Создаём путь к папке с превью, в папке previews/имя_пользователя
previews_root = os.path.join(script_dir, "previews")
user_preview_dir = os.path.join(previews_root, user_name)

if not os.path.exists(user_preview_dir):
    os.makedirs(user_preview_dir)

# Удаляем старые файлы в user_preview_dir
for file_name in os.listdir(user_preview_dir):
    full_path = os.path.join(user_preview_dir, file_name)
    try:
        if os.path.isfile(full_path):
            os.remove(full_path)
    except Exception as e:
        print("Не удалось удалить {}. Причина: {}".format(full_path, e))



for legend in legends:
    export_options = DB.ImageExportOptions()
    export_options.ExportRange = DB.ExportRange.SetOfViews
    export_options.SetViewsAndSheets(List[DB.ElementId]([legend.Id]))
    export_options.ImageResolution = DB.ImageResolution.DPI_150
    export_options.ZoomType = DB.ZoomFitType.FitToPage
    export_options.PixelSize = 720
    export_options.HLRandWFViewsFileType = DB.ImageFileType.PNG
    export_options.FitDirection = DB.FitDirectionType.Horizontal

    base_file_name = ""  # базовое имя файла для экспорта
    export_options.FilePath = os.path.join(user_preview_dir, base_file_name)

    source_doc.ExportImage(export_options)


for filename in os.listdir(user_preview_dir):
    if filename.endswith(".png"):
        old_path = os.path.join(user_preview_dir, filename)
        
        # Ищем " Легенда -" и всё, что до него, включая
        match = re.search(r'Легенда\s*-\s*(.*)', filename)
        if match:
            new_name = match.group(1).strip()
            new_path = os.path.join(user_preview_dir, new_name)

            # Переименовываем
            try:
                os.rename(old_path, new_path)
            except Exception as e:
                print("Не удалось переименовать файл:", old_path, "->", new_path)
                print("Ошибка:", e)



# === UI Выбор с превью
PATH_SCRIPT = os.path.dirname(__file__)
PATH_PREVIEWS = os.path.join(PATH_SCRIPT, "previews", user_name)



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
        xaml_path = os.path.join(PATH_SCRIPT, "FormListImage.xaml")
        wpf.LoadComponent(self, xaml_path)
        self.WindowStartupLocation = WindowStartupLocation.CenterScreen

        self._isDragging = False
        self._startPoint = None

        keywords = ["УО", "АС", "_"]

        self.image_files = self.load_image_files(keywords=keywords)
        self.ItemListView.ItemsSource = self.image_files
        self.OkButton.IsEnabled = False
        self.SelectedLegendNames = []

        self.ShowDialog()

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
        




# Запускаем окно выбора с превью легенд
form = PreviewForm()

# Получаем список выбранных имён легенд из окна
selected_names = form.SelectedLegendNames

if not selected_names:
    forms.alert("Легенды не выбраны.")
    source_doc.Close(False)
    raise SystemExit()

# Нормализуем имена, выбранные пользователем
normalized_selected_names = [normalize_name(name) for name in selected_names]

# Фильтруем легенды по нормализованным именам
selected_legends = [normalized_legend_dict[name] for name in normalized_selected_names if name in normalized_legend_dict]


if not selected_legends:
    forms.alert("Выбранные легенды не найдены в шаблоне.")
    #source_doc.Close(False)
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


# Копируем выбранные легенды в активный документ
with DB.Transaction(doc, "Копирование легенд") as t:
    t.Start()
    for legend in selected_legends:
        element_ids = List[DB.ElementId]()
        element_ids.Add(legend.Id)
        DB.ElementTransformUtils.CopyElements(
            source_doc,
            element_ids,
            doc,
            None,
            copy_options
        )
    t.Commit()

#source_doc.Close(False)
