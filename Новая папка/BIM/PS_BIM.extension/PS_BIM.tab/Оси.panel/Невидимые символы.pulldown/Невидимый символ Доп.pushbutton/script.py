# -*- coding: utf-8 -*-

import clr
import os
from Autodesk.Revit.UI import UIApplication, Result  # Импортируем Result
from pyrevit import EXEC_PARAMS
import System

# Параметры
DLL_NAME = 'SimvDP.dll'  # Имя вашего DLL файла
COMMAND_NAME = 'SimvDP.SimvDP'  # Полное имя класса с пространством имен


# Получаем объект командных данных
command_data = EXEC_PARAMS.command_data

# Получаем текущую папку, где находится script.py
current_dir = os.path.dirname(__file__)

# Путь к вашему .DLL файлу в той же папке, где и script.py
dll_path = os.path.join(current_dir, DLL_NAME)

# Проверяем, существует ли файл
if not os.path.exists(dll_path):
    raise FileNotFoundError("Файл {} не найден".format(dll_path))

# Функция для загрузки всех DLL файлов в папке
def load_all_dlls(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".dll") and filename != DLL_NAME:  # Пропускаем основной DLL файл
            full_path = os.path.join(directory, filename)
            clr.AddReferenceToFileAndPath(full_path)  # Загружаем DLL

# Загружаем все DLL файлы, кроме основного
load_all_dlls(current_dir)

# Добавляем ссылку на основную DLL
clr.AddReferenceToFileAndPath(dll_path)

# Импортируем пространство имен и получаем класс с помощью рефлексии
try:
    # Загружаем сборку
    assembly = System.Reflection.Assembly.LoadFile(dll_path)

    # Получаем тип команды
    command_type = assembly.GetType(COMMAND_NAME)
    
    if command_type is None:
        raise Exception("Не удалось получить тип {}".format(COMMAND_NAME))

    # Создаем экземпляр класса с помощью Activator
    plugin_instance = System.Activator.CreateInstance(command_type)

except Exception as e:
    raise

# Получаем активное приложение и документ
ui_app = command_data.Application
doc = ui_app.ActiveUIDocument.Document

try:
    # Подготовка переменных для вызова метода Execute
    message = System.String.Empty  # Это важно для строки
    elements = None  # Если вам не нужно передавать элементы

    # Преобразуем список параметров в массив объектов
    parameters = System.Array[System.Object]([command_data, message, elements])

    try:
        # Вызов метода Execute с помощью рефлексии
        result = command_type.InvokeMember("Execute", 
                                           System.Reflection.BindingFlags.InvokeMethod | 
                                           System.Reflection.BindingFlags.Public | 
                                           System.Reflection.BindingFlags.Instance, 
                                           None, 
                                           plugin_instance, 
                                           parameters)  # Передаем массив параметров
        
        # Проверяем результат выполнения
        if result != Result.Succeeded:
            pass  # Не выводим сообщение, если метод завершился неудачей

    except System.Reflection.TargetInvocationException as tie:
        raise

except Exception as e:
    raise  # Прекращаем выполнение при возникновении ошибки
