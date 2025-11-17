#! /usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import clr
clr.AddReference("System.Drawing")
clr.AddReference("System.Windows.Forms")

from System.Windows.Forms import Application, Form, FormWindowState, Screen, Label, PictureBox, PictureBoxSizeMode, \
    AnchorStyles, BorderStyle, ComboBox, ComboBoxStyle, FormBorderStyle, CheckBox, TextBox, TextBoxBase
from System.Windows.Forms import Button, LinkLabel, Panel, Button
from System.Drawing import Icon, Color, Font, Point, Size
import System.IO

#------ Глобальные настройки формы ------#
bitmapImage = System.Drawing.Bitmap(
    r"Z:\01_Библиотека\02_Семейства\ALL_Основные надписи\Логотип\\" + "Логотип Партнер.png")  # Логотип
titleIcon = Icon.FromHandle(bitmapImage.GetHicon())
titleText = "Обновляем номер секции"  # текст, который появляется в строке заголовка GUI
txtWith = 160 # ширина текстовой зоны
st_height = 30 # высота с кототорой начинается ввод
btnHeight = 40  # Высота кнопки
btnWidth = 100  # Ширина кнопки
btnSpacing = 20  # Интервал между кнопками + оступ элементов от края
htSpacing = 50  # Интервал между вводам данных
fontMessage = Font("Times New Roman ", 14)
fontCK = Font("Times New Roman ", 12)  # настройка шрифта у Checkbox
winSize = Size(400, 300)  # размеры winform (ширина(min = 300), высота).


def button(txt, loc, clc):
    btn = Button()
    # btnCancel.Parent = self
    btn.Text = txt
    btn.Anchor = (AnchorStyles.Bottom | AnchorStyles.Right)
    btn.Location = loc
    btn.Click += clc
    btn.Height = btnHeight
    btn.Width = btnWidth
    btn.BackColor = Color.FromArgb(220, 220, 220)
    return btn


def logo(uiH):
    logo = PictureBox()
    bitmapImage = System.Drawing.Bitmap(
        r"Z:\01_Библиотека\02_Семейства\ALL_Основные надписи\Логотип\\" + "Лого Партнер горизонтальный полный прозрачный фон.png")
    logo.Image = bitmapImage
    ratio = float(logo.Height) / float(logo.Width)  # должно быть значение с плавающей точкой, так как int округляется до ближайшего целого числа
    logo.Size = Size(150, 80 * ratio)  # размер логотипа
    logo.Location = Point(btnSpacing, (uiH - logo.Height) - btnSpacing)
    logo.SizeMode = PictureBoxSizeMode.Zoom  # масштабирование изображения
    logo.Anchor = (
                AnchorStyles.Bottom | AnchorStyles.Left)  # Привязка для охранения положения при масштабировании окна
    return logo


out = []
class WinForm(Form):
    def add_Logotxt(self, uiW, value):
        label_class = Label()
        font = fontMessage
        label_class.Text = value
        label_class.Font = font
        label_class.Location = Point(btnSpacing, btnSpacing)
        label_class.Height = htSpacing
        label_class.Width = uiW / 2
        return label_class

    def add_CHECKBOX(self, uiW, count=1,name="Пример ввода", value="Пример ввода!!"):
        ch_box = CheckBox()
        ch_box.Name = name
        ch_box.Text = value
        ch_box.Location = Point(btnSpacing, st_height + (count * htSpacing))
        ch_box.Width = uiW - (btnSpacing * 2)
        ch_box.Font = fontCK
        ch_box.Height = 40
        return ch_box

    def add_txtbox(self,uiW, count=1):#(self,uiW, count=1, value="Пример ввода") - если нужно в рамку добавить тест описания
        # окно ввода данных
        text_box = TextBox()
        text_box.Width = uiW / 2 - 2*btnSpacing
        #text_box.Text = value
        text_box.Font = fontCK
        text_box.Location = Point(htSpacing + txtWith, (st_height + htSpacing * count))
        return text_box

    def add_txtbox_label(self, count=1, name = "Пример ввода"):
        # текст возле ввода данных
        text_box_label = Label()
        text_box_label.Text = name
        text_box_label.Width = txtWith
        text_box_label.Font = fontCK
        text_box_label.Location = Point(btnSpacing, (st_height + htSpacing * count))
        text_box_label.Height = 50
        return text_box_label

    def okButton_pressed(self, sender, args):
        chBox_checks = []
        numErrorProvider = System.Windows.Forms.ErrorProvider()
        try:
            for i in range(len(self.lst_checkbox_index)):
                out.append((self.lst_checkbox_index)[i].Checked) # чаще будет нужен insetr для вставки по месту
            self.Close()  # Тригер для закрытия окна
        except ValueError:
            numErrorProvider.SetError(sender, 'Must be a number')

    def __init__(self):
        #------ Настройка окна ------#
        self.CenterToScreen()  # открывать по центру экрана
        self.BringToFront()  # Выводить на предний план
        self.Topmost = True  # Отобрадение окна поверх других окон
        self.Icon = titleIcon
        self.Size = winSize
        uiWidth = self.DisplayRectangle.Width  # ширина формы для использования в классе
        uiHeight = self.DisplayRectangle.Height # высота формы для использования в классе
        stHeight = uiHeight / 10  # высота с которой будут начинаться поля ввода
        htSpacing = 50  # расстояни между полями ввода
        # self.FormBorderStyle = FormBorderStyle.FixedDialog  # fixed dialog stops the user from adjusting the form size. Recomended disabling this when testing to see if elements are in the wrong place.#
        self.BackColor = Color.FromArgb(242, 242, 242)

        self.Controls.Add(logo(uiHeight))

        self.Text = titleText # Текст заголовка

        # Настройка текста в форме(можно добавить к кажой кнопке, но это гемор)
        self.Controls.Add(self.add_Logotxt(uiWidth,
                                      "Заполните значения")
                          )
        #----- добавить ввод данных с клавиатуры -----#
        # чекбокс
        self.cg0 = self.add_CHECKBOX(uiWidth, 1, "Квартира", "Выбраны помещения квартиры?")
        self.cg1 = self.add_CHECKBOX(uiWidth, 2 , "Все", "Обновить у всех помещений?")
        self.lst_checkbox_index = [self.cg0,self.cg1]
        self.Controls.Add(self.cg0)
        self.Controls.Add(self.cg1)


        #Добавляем поле ввода
        # self.txtBox_numb = self.add_txtbox(uiWidth, 1)
        # self.lst_txtBoxses = [self.txtBox_numb] # формируем список из полей вставки (нужно для вывода)
        # self.Controls.Add(self.txtBox_numb)

        # ----- добавить кнопку -----#
        btnOkClick = self.okButton_pressed  # Регистрация нажатия
        # Ниже одна кнопка. Для расчета нужно btnWidth * кол-во кнопок
        btnOkLoc = Point(uiWidth - ((btnWidth) + btnSpacing), uiHeight - (btnHeight + btnSpacing)) #Расчет положения.
        btnOk = button('OK', btnOkLoc, btnOkClick)
        self.Controls.Add(btnOk)


form = WinForm()
Application.Run(form)

print(out) # print заменить на out
