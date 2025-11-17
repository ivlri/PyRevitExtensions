# -*- coding: utf-8 -*-
#⬇️ Imports
import pyrevit
from pyrevit import EXEC_PARAMS, revit
from pyrevit import DB, UI
import System.Windows.Forms as WinForms
import re  # Импортируем модуль регулярных выражений

# Получаем аргументы события
args = EXEC_PARAMS.event_args

# Получаем текущий документ
doc1 = revit.doc  # Получаем текущий документ из PyRevit

# Получаем имена транзакций
transaction_names = list(args.GetTransactionNames())  # Список имен транзакций

# Получаем добавленные и измененные элементы
try:
    added_elements = list(args.GetAddedElementIds())  # Добавленные элементы
    modified_elements = list(args.GetModifiedElementIds())  # Измененные элементы
except Exception:
    added_elements = []
    modified_elements = []

# Список транзакций для проверки
transaction_list = [
    "Начальная вставка",
    "Вставить с выравниванием",
    "Вставить",
    "+",
    # Добавьте другие транзакции по мере необходимости
]

# Функция для проверки на дубли по имени семейства
def check_for_duplicate_families(element_ids):
    warnings = []  # Список для предупреждений
    for element_id in element_ids:
        try:
            element = doc1.GetElement(element_id)

            # Проверяем, является ли элемент экземпляром семейства
            if hasattr(element, 'Symbol'):
                family = element.Symbol.Family
                if family is not None:
                    family_name = family.Name
                    
                    # Проверяем условия для дубликатов
                    if re.search(r'[0-9]$', family_name) and not re.search(r'[vV_.][0-9]?$', family_name) and not re.search(r'[0-9]{2,}$', family_name):
                        warnings.append(" Семейство '{0}' является дублем. Отмените последние действия".format(family_name))

        except Exception:
            continue  # Игнорируем элемент, если возникла ошибка

    return warnings  # Возвращаем список предупреждений

# Функция для фильтрации уникальных предупреждений
def filter_unique_warnings(warnings):
    return list(set(warnings))  # Преобразуем в множество для уникальности и обратно в список

# Проверяем наличие изменений и выполняем проверку на дубли
if any(tx in transaction_names for tx in transaction_list) and (added_elements or modified_elements):
    # Объединяем добавленные и измененные элементы
    all_elements = added_elements + modified_elements

    # Выполняем проверку на дубли
    all_warnings = check_for_duplicate_families(all_elements)

    # Фильтруем уникальные предупреждения
    unique_warnings = filter_unique_warnings(all_warnings)

    # Если есть уникальные предупреждения, выводим их в окно
    if unique_warnings:
        # Создаем окно предупреждения
        message = "\n".join(unique_warnings)  # Соединяем уникальные предупреждения в одно сообщение
        WinForms.MessageBox.Show(message, "Предупреждение", WinForms.MessageBoxButtons.OK, WinForms.MessageBoxIcon.Warning)
