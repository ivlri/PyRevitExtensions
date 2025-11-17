# -*- coding: utf-8 -*-
import clr
import System
clr.AddReference("System")
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from System.Windows.Forms import Application, Form, Button, CheckedListBox, Label, CheckBox, MessageBox, MessageBoxButtons
from System.Drawing import Point, Size
from Autodesk.Revit.DB import Transaction, SaveAsOptions, ModelPathUtils, WorksharingUtils
from pyrevit import forms

import tempfile
import os
from Autodesk.Revit.DB import UnitSystem

# --- Активная сессия Revit ---
uiapp = __revit__
app = uiapp.Application
doc = uiapp.ActiveUIDocument.Document

# --- Получаем все открытые документы ---
open_docs = list(app.Documents)

# --- Классификация документов ---
docs_workshared = []
docs_projects = []
docs_families = []
docs_unsaved = []

for d in open_docs:
    try:
        # Пропускаем все Revit-связи
        if hasattr(d, "IsLinked") and d.IsLinked:
            continue

        if not d.PathName:
            docs_unsaved.append(d)
        elif d.IsFamilyDocument:
            docs_families.append(d)
        elif d.IsWorkshared:
            docs_workshared.append(d)
        else:
            docs_projects.append(d)
    except:
        pass

#=== Исправления потери контекста после открытия окна - Начало части 1
import pyrevit
from Autodesk.Revit.UI import UIApplication
original_uiapp_property = pyrevit._HostApplication.uiapp
ui_app = UIApplication(__revit__.Application)  
@property
def custom_uiapp(self):
    """Return UIApplication provided to the running command."""
    return ui_app

pyrevit._HostApplication.uiapp = custom_uiapp
#=== Исправления потери контекста после открытия окна - Конец части 1

# --- Форма ---
class DocsOverviewForm(Form):
    def __init__(self):
        self.Text = "Открытые документы Revit"
        self.Size = Size(605, 800)
        self.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen

        # Блокируем изменение размеров
        self.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        self.MinimizeBox = False

        # Автопрокрутка
        self.AutoScroll = True

        self.y = 10
        self.checkedlists = []

        # --- Добавляем блоки документов ---
        self.add_block("Файлы хранилища (ФХ):", docs_workshared, enabled=True)
        self.add_block("Обычные проекты:", docs_projects, enabled=True)
        self.add_block("Семейства:", docs_families, enabled=True)
        self.add_block("Несохранённые документы:", docs_unsaved, enabled=False)  # галка «Выбрать все» не нужна

        # --- Чекбоксы действий ---
        self.y += 10

        self.chk_sync = CheckBox()
        self.chk_sync.Text = "Синхронизировать и сохранить"
        self.chk_sync.AutoSize = True
        self.chk_sync.Location = Point(20, self.y)
        self.chk_sync.Checked = True
        self.Controls.Add(self.chk_sync)
        self.y += 30

        self.chk_close_docs = CheckBox()
        self.chk_close_docs.Text = "Закрыть документы"
        self.chk_close_docs.AutoSize = True
        self.chk_close_docs.Location = Point(20, self.y)
        self.Controls.Add(self.chk_close_docs)
        self.y += 30
        self.chk_close_docs.CheckedChanged += lambda s, e: self.update_close_revit_visibility()


        self.chk_close_revit = CheckBox()
        self.chk_close_revit.Text = "Закрыть Revit"
        self.chk_close_revit.AutoSize = True
        self.chk_close_revit.Location = Point(20, self.y)
        self.chk_close_revit.Visible = False
        self.Controls.Add(self.chk_close_revit)
        self.y += 50

        # --- Кнопки ---
        self.btn_ok = Button()
        self.btn_ok.Text = "Продолжить"
        self.btn_ok.Size = Size(200, 35)
        self.btn_ok.Location = Point(80, self.y)
        self.btn_ok.Click += self.ok_click
        self.Controls.Add(self.btn_ok)

        self.btn_cancel = Button()
        self.btn_cancel.Text = "Отмена"
        self.btn_cancel.Size = Size(200, 35)
        self.btn_cancel.Location = Point(320, self.y)
        self.btn_cancel.Click += lambda s, e: self.Close()
        self.Controls.Add(self.btn_cancel)

        # Проверяем видимость кнопки "Закрыть Revit"
        self.update_close_revit_visibility_initial()

    def add_block(self, title, docs, enabled=True):
        """Добавляем блок с заголовком и CheckedListBox"""
        from System.Drawing import Font, FontStyle  # добавить в начале файла, если еще нет

        lbl = Label()
        lbl.Text = title
        lbl.Size = Size(560, 25)  # чуть выше, чтобы помещался жирный текст
        lbl.Location = Point(10, self.y)
        lbl.Font = Font("Arial", 12, FontStyle.Bold)  # 🔹 жирный и крупный шрифт
        self.Controls.Add(lbl)
        self.y += 25  # увеличиваем вертикальный отступ, чтобы кнопка "Выбрать все" не налезала


        clb = CheckedListBox()
        clb.Size = Size(560, 100)
        clb.Location = Point(10, self.y)
        clb.CheckOnClick = True
        clb.Enabled = enabled

        # Добавляем документы
        if docs:
            for d in docs:
                clb.Items.Add(d.Title, True)  # по умолчанию все выбрано
        else:
            clb.Items.Add("(пусто)", False)
            clb.Enabled = False

        self.Controls.Add(clb)
        self.y += 95

        # Подключаем событие изменения галки
        clb.ItemCheck += lambda s, e: self.update_close_revit_visibility(s, e)

        # Добавляем галку "Выбрать все" только если список не пустой
        if enabled and docs:
            self.checkedlists.append(clb)

            chk_all = CheckBox()
            chk_all.Text = "Выбрать все"
            chk_all.AutoSize = True
            chk_all.Location = Point(13, self.y)  # теперь под списком
            chk_all.Checked = True  # по умолчанию включена
            self.Controls.Add(chk_all)

            def toggle_all(sender, event):
                try:
                    val = sender.Checked
                    for i in range(clb.Items.Count):
                        clb.SetItemChecked(i, val)
                except:
                    pass
                self.update_close_revit_visibility_initial()

            chk_all.CheckedChanged += toggle_all

            # Увеличиваем y, чтобы следующий блок не накладывался
            self.y += 30  # дополнительный отступ после галки "Выбрать все"


    def update_close_revit_visibility_initial(self):
        """Проверка видимости 'Закрыть Revit' при инициализации формы."""
        self.update_close_revit_visibility()


    def update_close_revit_visibility(self, sender=None, e=None):
        """Обновляем видимость кнопки 'Закрыть Revit'."""
        try:
            all_checked = True
            for clb in self.checkedlists:
                if clb.Items.Count == 0:
                    continue
                for i in range(clb.Items.Count):
                    state = e.NewValue if clb == sender and i == e.Index else clb.GetItemCheckState(i)
                    if state != System.Windows.Forms.CheckState.Checked:
                        all_checked = False
                        break
                if not all_checked:
                    break

            # 🔹 Появляется только если выбраны все элементы И галка 'Закрыть документы' активна
            self.chk_close_revit.Visible = all_checked and self.chk_close_docs.Checked

        except:
            self.chk_close_revit.Visible = False
            
    def ok_click(self, sender, event):
        import os
        from System import DateTime, Environment
        from Autodesk.Revit.DB import UnitSystem, SaveAsOptions, TransactWithCentralOptions, SynchronizeWithCentralOptions, RelinquishOptions
        from Autodesk.Revit.UI import TaskDialog

        try:
            # --- 1️⃣ Подсчет общего количества операций(что бы не делить) ---
            total_operations = 0
            
            # перации синхронизации
            if self.chk_sync.Checked:
                for clb in self.checkedlists:
                    for i in range(clb.Items.Count):
                        if clb.GetItemChecked(i):
                            total_operations += 1
            
            # Операции закрытия документов
            if self.chk_close_docs.Checked:
                docs_to_close = []
                
                for clb in self.checkedlists:
                    for i in range(clb.Items.Count):
                        if clb.GetItemChecked(i):
                            doc_title = clb.Items[i].ToString()
                            for d in list(app.Documents):
                                try:
                                    if (
                                        d.Title == doc_title
                                        and d.IsValidObject
                                        and not (hasattr(d, "IsLinked") and d.IsLinked)
                                    ):
                                        docs_to_close.append(d)
                                except:
                                    pass
                
                # Добавляем несохранённые документы
                for d in list(app.Documents):
                    try:
                        if not d.PathName and d.IsValidObject and not (hasattr(d, "IsLinked") and d.IsLinked):
                            docs_to_close.append(d)
                    except:
                        pass
                
                if not self.chk_sync.Checked:
                    total_operations += len(docs_to_close)
            
            # --- 2️⃣ Создание временного документа только если нужно закрывать документы ---
            temp_doc = None
            if self.chk_close_docs.Checked:
                my_docs = Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments)
                timestamp = DateTime.Now.ToString("yyyyMMdd_HHmmss")
                new_file_path = os.path.join(my_docs, "Закрыватор_{}.rvt".format(timestamp))
                temp_doc = app.NewProjectDocument(UnitSystem.Metric)
                save_options = SaveAsOptions()
                save_options.OverwriteExistingFile = True
                temp_doc.SaveAs(new_file_path, save_options)
                uiapp.OpenAndActivateDocument(new_file_path)

            # --- 3️⃣ Обработка документов---
            current_operation = 0
            
            with forms.ProgressBar(title='Обработка документов: ({value} из {max_value})', cancellable=True) as pb:
                # --- Синхронизация и сохранение выбранных документов ---
                if self.chk_sync.Checked:
                    for clb in self.checkedlists:
                        for i in range(clb.Items.Count):
                            if clb.GetItemChecked(i):
                                # Обновление прогресбара 
                                if not self.chk_close_docs.Checked:
                                    current_operation += 1
                                    pb.update_progress(current_operation, total_operations)
                                    
                                if pb.cancelled:
                                    TaskDialog.Show("Информация", "Операция прервана пользователем.")
                                    return
        
                                
                                doc_title = clb.Items[i].ToString()
                                for d in list(app.Documents):
                                    if d.Title == doc_title:
                                        try:
                                            if d.IsWorkshared:
                                                # Настройка опций для синхронизации с центральной моделью
                                                trans_opts = TransactWithCentralOptions()
                                                sync_opts = SynchronizeWithCentralOptions()
                                                relinquish_opts = RelinquishOptions(True)  # отдать все рабочие наборы
                                                sync_opts.SetRelinquishOptions(relinquish_opts)
                                                sync_opts.SaveLocalAfter = True
                                                sync_opts.Comment = "Синхронизация через закрыватор"
                                                d.SynchronizeWithCentral(trans_opts, sync_opts)
                                            if d.PathName:
                                                d.Save()
                                        except Exception as ex:
                                            TaskDialog.Show("Ошибка", "Не удалось сохранить {}: {}".format(doc_title, ex))

                # --- Закрытие выбранных документов ---
                if self.chk_close_docs.Checked:
                    # Теперь закрываем их последовательно, безопасно
                    for d in docs_to_close:
                        try:
                            # Обновление прогресбара 
                            current_operation += 1
                            pb.update_progress(current_operation, total_operations)
                            
                            if pb.cancelled:
                                TaskDialog.Show("Информация", "Операция прервана пользователем.")
                                return
                            
                            if d.IsWorkshared:
                                relinquish = RelinquishOptions(True)
                                relinquish.CheckedOutElements = True
                                relinquish.FamilyWorksets = True
                                relinquish.StandardWorksets = True
                                relinquish.UserWorksets = True 

                                transact_options = TransactWithCentralOptions()
                                WorksharingUtils.RelinquishOwnership(d, relinquish, transact_options)

                            if d.IsValidObject:
                                d.Close(False)
                        except Exception as ex:
                            print("Ошибка при закрытии {}: {}".format(d.Title if d else "?", ex))

            # --- 4️⃣ Закрытие Revit, если выбрано ---
            if self.chk_close_revit.Checked:
                import System.Windows.Forms as WinForms
                import time

                # Задержка, чтобы убедиться, что форма закрыта
                #time.sleep(0.2)

                # Симулируем Alt+F4 для закрытия активного окна Revit
                #WinForms.SendKeys.SendWait("%{F4}")  # % = Alt, {F4} = F4

            # --- 5️⃣ Финальный информационный диалог ---
            #TaskDialog.Show("Информация", "Действия выполнены успешно.")

        except Exception as e:
            TaskDialog.Show("Ошибка", "Произошла ошибка при выполнении действий: {}".format(e))

        # --- 6️⃣ Закрываем окно формы после всех действий ---
        self.Close()


    # def ok_click(self, sender, event):
    #     import os
    #     from System import DateTime, Environment
    #     from Autodesk.Revit.DB import UnitSystem, SaveAsOptions, TransactWithCentralOptions, SynchronizeWithCentralOptions, RelinquishOptions
    #     from Autodesk.Revit.UI import TaskDialog

    #     try:
    #         # --- 1️⃣ Создание временного документа только если нужно закрывать документы ---
    #         temp_doc = None
    #         if self.chk_close_docs.Checked:
    #             my_docs = Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments)
    #             timestamp = DateTime.Now.ToString("yyyyMMdd_HHmmss")
    #             new_file_path = os.path.join(my_docs, "Закрыватор_{}.rvt".format(timestamp))
    #             temp_doc = app.NewProjectDocument(UnitSystem.Metric)
    #             save_options = SaveAsOptions()
    #             save_options.OverwriteExistingFile = True
    #             temp_doc.SaveAs(new_file_path, save_options)
    #             uiapp.OpenAndActivateDocument(new_file_path)

    #         with forms.ProgressBar(title='Обработка фалов ({value} из {max_value})', cancellable=True) as pb:
    #             total = len(self.checkedlists)
    #             idx = 0
    #             # --- 2️⃣ Синхронизация и сохранение выбранных документов ---
    #             if self.chk_sync.Checked:
    #                 for clb in self.checkedlists:
    #                     for i in range(clb.Items.Count):
    #                         if clb.GetItemChecked(i):
    #                             idx += 1
    #                             pb.update_progress(idx, total)

    #                             doc_title = clb.Items[i].ToString()

    #                             for d in list(app.Documents):
    #                                 if d.Title == doc_title:
    #                                     try:
    #                                         if d.IsWorkshared:
    #                                             # Настройка опций для синхронизации с центральной моделью
    #                                             trans_opts = TransactWithCentralOptions()
    #                                             sync_opts = SynchronizeWithCentralOptions()
    #                                             relinquish_opts = RelinquishOptions(True)  # отдать все рабочие наборы
    #                                             sync_opts.SetRelinquishOptions(relinquish_opts)
    #                                             sync_opts.SaveLocalAfter = True
    #                                             sync_opts.Comment = "Синхронизация через закрыватор"
    #                                             d.SynchronizeWithCentral(trans_opts, sync_opts)
    #                                         if d.PathName:
    #                                             d.Save()
    #                                     except Exception as ex:
    #                                         TaskDialog.Show("Ошибка", "Не удалось сохранить {}: {}".format(doc_title, ex))

    #             # --- 3️⃣ Закрытие выбранных документов ---
    #             if self.chk_close_docs.Checked:
    #                 # Формируем стабильный список заранее
    #                 docs_to_close = []

    #                 for clb in self.checkedlists:
    #                     for i in range(clb.Items.Count):
    #                         if clb.GetItemChecked(i):
    #                             doc_title = clb.Items[i].ToString()
    #                             for d in list(app.Documents):
    #                                 try:
    #                                     if (
    #                                         d.Title == doc_title
    #                                         and d.IsValidObject
    #                                         and not (hasattr(d, "IsLinked") and d.IsLinked)
    #                                     ):
    #                                         docs_to_close.append(d)
    #                                 except:
    #                                     pass

    #                 # Добавляем несохранённые документы (если нужно)
    #                 for d in list(app.Documents):
    #                     try:
    #                         if not d.PathName and d.IsValidObject and not (hasattr(d, "IsLinked") and d.IsLinked):
    #                             docs_to_close.append(d)
    #                     except:
    #                         pass

    #                 # Теперь закрываем их последовательно, безопасно
    #                 for d in docs_to_close:
    #                     try:
    #                         if d.IsWorkshared:
    #                             relinquish = RelinquishOptions(d)
    #                             relinquish.CheckedOutElements = True
    #                             relinquish.FamilyWorksets = True
    #                             relinquish.StandardWorksets = True
    #                             relinquish.UserWorksets = True 

    #                             transact_options = TransactWithCentralOptions()

    #                             WorksharingUtils.RelinquishOwnership(d, relinquish, transact_options)

    #                         if d.IsValidObject:
    #                             idx += 1
    #                             pb.update_progress(idx, total)

    #                             d.Close(False)
    #                     except Exception as ex:
    #                         print("Ошибка при закрытии {}: {}".format(d.Title if d else "?", ex))


            # # --- 4️⃣ Закрытие Revit, если выбрано ---
            # if self.chk_close_revit.Checked:
            #     import System.Windows.Forms as WinForms
            #     import time

            #     # Задержка, чтобы убедиться, что форма закрыта
            #     #time.sleep(0.2)

            #     # Симулируем Alt+F4 для закрытия активного окна Revit
            #     #WinForms.SendKeys.SendWait("%{F4}")  # % = Alt, {F4} = F4

            # # --- 5️⃣ Финальный информационный диалог ---
            # #TaskDialog.Show("Информация", "Действия выполнены успешно.")

        # except Exception as e:
        #     TaskDialog.Show("Ошибка", "Произошла ошибка при выполнении действий: {}".format(e))

        # # --- 6️⃣ Закрываем окно формы после всех действий ---
        # self.Close()




# --- Запуск формы ---
try:
    form = DocsOverviewForm()
    Application.EnableVisualStyles()
    Application.Run(form)
finally:
    pyrevit._HostApplication.uiapp = original_uiapp_property
