# -*- coding: utf-8 -*-
import clr
import datetime
clr.AddReference('System.Windows.Forms')
clr.AddReference('System.Drawing')
from System.Security.Cryptography import Aes, CryptoStream, CryptoStreamMode
from System.Text import Encoding
from System.IO import MemoryStream, StreamReader
from System.Windows.Forms import Form, Label, TextBox, Button, DialogResult, FormStartPosition, FormBorderStyle
import System.Drawing
from System import Convert
from pyrevit import script
from pyrevit import forms
import xml.etree.ElementTree as ET
from xml.dom import minidom
import random
from pyrevit.coreutils import envvars
import json
import os


class PasswordForm(Form):
    def __init__(self, x, y):
        self.Text = 'Действие запрещено!'
        self.Width = 255
        self.Height = 150
        self.StartPosition = FormStartPosition.Manual
        self.Location = System.Drawing.Point(x, y)

        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        self.MinimizeBox = False

        label = Label()
        label.Text = 'Введите пароль для продолжения:'
        label.Top = 20
        label.Left = 20
        label.Width = 260
        label.AutoSize = False
        self.Controls.Add(label)

        self.password_box = TextBox()
        self.password_box.Left = 20
        self.password_box.Top = 50
        self.password_box.Width = 200
        self.password_box.UseSystemPasswordChar = True
        self.Controls.Add(self.password_box)

        button_ok = Button()
        button_ok.Text = 'OK'
        button_ok.Left = 20
        button_ok.Top = 80
        button_ok.DialogResult = DialogResult.OK
        self.Controls.Add(button_ok)

        button_cancel = Button()
        button_cancel.Text = 'Отмена'
        button_cancel.Top = 80
        button_cancel.Left = 145
        button_cancel.DialogResult = DialogResult.Cancel
        self.Controls.Add(button_cancel)

        self.AcceptButton = button_ok
        self.CancelButton = button_cancel


class PaswordPanel(object):
    """
    Инициализация панели
    
    Args:
        current_doc: Текущий документ Revit
        allowed_users: Список разрешенных пользователей
        current_sender: Отправитель события (опционально)
        current_args: Аргументы события (опционально)
        info: Выводить/не выводить оповещение о не правильном паролем
    """
    def __init__(self, 
                 current_doc, 
                 current_sender=None, 
                 current_args=None,
                 allowed_users = ["legostaev", "chernova.a"], 
                 info=False,
                 logging=False):
        
        self.doc = current_doc
        self.allowed_users = allowed_users
        self.current_user = current_doc.Application.Username
        self.sender = current_sender
        self.args = current_args
        self.info = info
        self.logging = logging

    def _generate_password(self):
        today = datetime.datetime.now()
        day = today.day
        month = today.month

        day_str = str(day + 1).zfill(2)
        month_str = str(month + 1).zfill(2)

        password = month_str[1] + day_str[1] + str(int(month_str[0]) + 1) + str(int(day_str[0])+ 1)
        
        return str(password)

    def _write_pretty_xml(self, filepath, root):
        xml_string = ET.tostring(root, encoding='utf-8')
        
        formatted_xml = minidom.parseString(xml_string)
        
        pretty_xml_as_string = '\n'.join([line for line in formatted_xml.toprettyxml(indent="    ").splitlines() if line.strip()])

        with open(filepath, 'wb') as f:
            f.write(pretty_xml_as_string.encode('utf-8'))

    def _log_user_data(self, user_name, file_path):
        """Логирование действий пользователя"""
        xml_file = file_path
        
        if os.path.exists(xml_file):
            tree = ET.parse(xml_file)
            root = tree.getroot()
        else:
            root = ET.Element("UserLog")
            tree = ET.ElementTree(root)

        log_entry = ET.Element("LogEntry")
        user_element = ET.SubElement(log_entry, "User")
        user_element.text = user_name
        time_element = ET.SubElement(log_entry, "Time")
        time_element.text = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        root.append(log_entry)

        self._write_pretty_xml(xml_file, root)

    def check_passward(self, logfile_path=''):
        """Проверка пароля"""
        if self.current_user in self.allowed_users:
            return True
        
        calculated_password = self._generate_password()
        
        cursor_position = System.Windows.Forms.Cursor.Position
        
        form = PasswordForm(cursor_position.X-130, cursor_position.Y-80)
        result = form.ShowDialog()
        
        if result == DialogResult.Cancel:
            if self.args is not None:
                self.args.Cancel = True
            return False
        else:
            user_input = form.password_box.Text
            if user_input != calculated_password:
                if self.args is not None:
                    self.args.Cancel = True
                return False
            else:
                if self.logging:
                    self._log_user_data(self.current_user, logfile_path)
                return True
    
    def get_passward(self):
        cursor_position = System.Windows.Forms.Cursor.Position
        form = PasswordForm(cursor_position.X-130, cursor_position.Y-80)
        result = form.ShowDialog()
        if result=='7250':
            print('Текущий пароль: {}'.format(self._generate_password()))