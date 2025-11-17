# -*- coding: utf-8 -*-
import os
import shutil
import subprocess
import System.Diagnostics
from Autodesk.Revit.UI import UIApplication
from pyrevit import EXEC_PARAMS
import time
import ctypes

# Путь к исполняемому файлу Dynamo Player
dynamo_player_path = r"C:\Program Files\Autodesk\Revit 2022\AddIns\DynamoPlayerForRevit\resource\DynamoPlayer.exe"

# Путь к директории пользовательских данных
user_data_base_dir = os.path.join(os.getenv('LOCALAPPDATA'), r"dynamoplayer-4\PyRevit")

# Путь к файлу с директориями образцов
samples_file_path = os.path.join(os.path.dirname(__file__), 'samples_directory.txt')

# Путь к файлу chrome-extension, который лежит рядом со скриптом
local_file_to_copy = os.path.join(os.path.dirname(__file__), 'chrome-extension_cmhgjmicokekghelcdjlgokdhhihcekc_0.localstorage')

# Функция для чтения пути к директории образцов из файла
def read_samples_directory():
    if os.path.exists(samples_file_path):
        with open(samples_file_path, 'rb') as file:  # Открываем в бинарном режиме
            directory = file.read().decode('utf-8').strip()  # Декодируем содержимое
            return directory
    else:
        raise FileNotFoundError("Файл с директориями образцов не найден: {}".format(samples_file_path))

# Путь к директории, которая должна открыться при запуске Dynamo Player
dynamo_samples_directory = read_samples_directory()

# Функция для получения PID текущего процесса Revit
def get_current_revit_pid():
    current_process = System.Diagnostics.Process.GetCurrentProcess()
    return str(current_process.Id)

# Функция для получения списка процессов Revit
def get_ports_and_processes():
    try:
        netstat_output = subprocess.check_output(['netstat', '-aon']).decode('cp1251')
        ports_info = []

        for line in netstat_output.splitlines():
            parts = line.split()
            if len(parts) >= 5:
                protocol = parts[0]
                local_address = parts[1]
                state = parts[3]
                pid = parts[4]

                port = local_address.split(':')[-1]
                ip = local_address.split(':')[0]

                ports_info.append({
                    'port': port,
                    'ip': ip,
                    'state': state,
                    'pid': pid,
                    'protocol': protocol
                })

        return ports_info
    
    except Exception as e:
        return []

# Функция для получения открытых портов, связанных с текущим процессом Revit
def get_current_revit_ports_info():
    revit_ports = []
    current_revit_pid = get_current_revit_pid()
    ports_info = get_ports_and_processes()

    for port_info in ports_info:
        if (port_info['pid'] == current_revit_pid and
            port_info['ip'] == '127.0.0.1' and
            port_info['state'] == 'LISTENING' and
            port_info['port'] != '8088'):
            revit_ports.append(port_info['port'])

    return revit_ports

# Функция для копирования файла при первом запуске
def copy_file_if_first_run(localstorage_dir_path):
    target_file_path = os.path.join(localstorage_dir_path, 'chrome-extension_cmhgjmicokekghelcdjlgokdhhihcekc_0.localstorage')

    # Проверяем, если файл отсутствует, то копируем
    if not os.path.exists(target_file_path):
        shutil.copy(local_file_to_copy, target_file_path)

# Константа для предотвращения открытия окна
CREATE_NO_WINDOW = 0x08000000

# Функция для закрытия процесса Dynamo по конкретному порту
def close_dynamo_by_port(port):
    try:
        # Выполняем команду tasklist для получения списка запущенных процессов
        tasklist_output = subprocess.check_output(
            ['tasklist'], creationflags=CREATE_NO_WINDOW
        ).decode('cp1251')

        # Проходим по всем процессам, чтобы найти Dynamo Player
        for line in tasklist_output.splitlines():
            if 'dynamoplayer.exe' in line:
                # Получаем PID процесса
                pid = line.split()[1]

                # Выполняем команду для получения командной строки процесса
                process_info = subprocess.check_output(
                    ['wmic', 'process', 'where', 'ProcessId={}'.format(pid), 'get', 'CommandLine'],
                    creationflags=CREATE_NO_WINDOW
                ).decode('cp1251')

                # Проверяем, что порт совпадает
                if '--port={}'.format(port) in process_info:
                    subprocess.call(
                        ['taskkill', '/F', '/PID', pid], creationflags=CREATE_NO_WINDOW
                    )  # Завершаем процесс по PID
                    break  # Закрываем только первое найденное окно с указанным портом
    except Exception as e:
        print("Ошибка при закрытии процесса: {}".format(str(e)))



# Функция для удаления директорий старше 5 дней
def delete_unused_directories():
    current_time = time.time()  # Получаем текущее время в секундах с начала эпохи
    five_days_in_seconds = 7 * 24 * 60 * 60  # 5 дней в секундах

    for folder_name in os.listdir(user_data_base_dir):
        if folder_name.startswith("dynamoplayerinstance"):
            folder_path = os.path.join(user_data_base_dir, folder_name)
            folder_creation_time = os.path.getmtime(folder_path)  # Получаем время последнего изменения
            
            # Проверяем, если папка старше 5 дней
            if current_time - folder_creation_time > five_days_in_seconds:
                try:
                    shutil.rmtree(folder_path)  # Удаляем папку
                except Exception as e:
                    # Ошибка игнорируется, можно логировать в файл, если нужно
                    pass  # или использовать logging для записи ошибок в файл, если это необходимо




# Функция для запуска Dynamo Player с использованием первого найденного порта
def launch_dynamo_player():
    revit_ports = get_current_revit_ports_info()  # Получаем список портов Revit
    
    if revit_ports:
        dynamo_port = revit_ports[0]

        # Закрываем процесс Dynamo, если он запущен с этим портом
        close_dynamo_by_port(dynamo_port)

        user_data_dir = os.path.join(user_data_base_dir, "dynamoplayerinstance {}".format(dynamo_port))
        localstorage_dir_path = os.path.join(user_data_dir, "Default", "Local Storage")

        # Копируем файл при первом запуске
        if not os.path.exists(localstorage_dir_path):
            os.makedirs(localstorage_dir_path)

        copy_file_if_first_run(localstorage_dir_path)

        command_data = EXEC_PARAMS.command_data
        ui_app = command_data.Application

        if os.path.exists(dynamo_player_path):
            command_line = [
                dynamo_player_path,
                "--port={}".format(dynamo_port),
                "--docname={}".format(ui_app.ActiveUIDocument.Document.Title),
                "--lang=ru",
                "--user-data-dir={}".format(user_data_dir),
                "--samples={}".format(dynamo_samples_directory)
            ]

            subprocess.Popen(command_line, close_fds=True, shell=True)
        else:
            raise IOError("Не найден путь к Dynamo Player: {}".format(dynamo_player_path))

        # Удаление неиспользуемых директорий
        delete_unused_directories()




# Пример использования
if __name__ == "__main__":
    launch_dynamo_player()
