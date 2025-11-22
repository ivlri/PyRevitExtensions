# -*- coding: utf-8 -*-
from pyrevit import revit, EXEC_PARAMS
from Autodesk.Revit.UI import TaskDialog
from functions._Panel import PaswordPanel
import os
# Функция для записи отформатированного XML
try:
    #📦 Variables
    sender = __eventsender__
    args = __eventargs__

    doc = revit.doc
    uidoc = revit.uidoc

    # Список разрешенных пользователей, для которых не нужно вводить пароль
    allowed_users = []


    # Получаем выбранные элементы
    selected_ids = uidoc.Selection.GetElementIds()
    selected_elements = [doc.GetElement(id) for id in selected_ids]

    # Категории, при которых окно не нужно показывать
    excluded_categories = ["Оси", "Уровни","Несущая арматура","Армирование по площади несущей конструкции","Армирование по траектории несущей конструкции","Формы"]

    # Проверяем, есть ли в выбранных элементах категории, отличные от "Оси" и "Уровни"
    show_password_prompt = False
    for element in selected_elements:
        if element.Category and element.Category.Name not in excluded_categories:
            show_password_prompt = True
            break

    if show_password_prompt:
        passw = PaswordPanel(current_doc=doc, 
                    allowed_users=allowed_users, 
                    current_sender=sender, 
                    current_args=args,
                    logging=True)
        
        logfile_path = os.path.join(os.path.dirname(__file__), 
                                    "password_hide_elements_user_log.xml")
        check_passw = passw.check_passward(logfile_path=logfile_path)
    else:
        pass

except Exception as e:
    # Показываем сообщение с ошибкой в диалоговом окне Revit
    TaskDialog.Show("Ошибка", str(e))
