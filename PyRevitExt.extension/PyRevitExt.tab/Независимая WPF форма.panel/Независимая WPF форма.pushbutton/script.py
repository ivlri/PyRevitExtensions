# -*- coding: utf-8 -*-
# from pyrevit import forms
# layout = '<Window ' \
#          'xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" ' \
#          'xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" ' \
#          'ShowInTaskbar="False" ResizeMode="NoResize" ' \
#          'WindowStartupLocation="CenterScreen" ' \
#          'HorizontalContentAlignment="Center">' \
#          '</Window>'
# w = forms.WPFWindow(layout, literal_string=True)
# w.show()
__title__ = "ModelessForm"
__persistentengine__ = True
try:
    import clr
    clr.AddReference("System.Windows.Forms")
    clr.AddReference("System.Collections")

    import System

    from Autodesk.Revit.UI import IExternalEventHandler, ExternalEvent
    from Autodesk.Revit.DB import *
    from Autodesk.Revit.Exceptions import InvalidOperationException
    from pyrevit import forms
    from pyrevit.forms import WPFWindow


    doc   = __revit__.ActiveUIDocument.Document
    uidoc = __revit__.ActiveUIDocument
    app   = __revit__.Application
    active_view = doc.ActiveView

    initial_conditions = (isinstance(active_view, ViewPlan) or 
                        isinstance(active_view, ViewDrafting) or 
                        isinstance(active_view, ViewSection) or 
                        doc.GetElement(active_view.GetTypeId()).FamilyName == "Легенды")

    if initial_conditions:
        from DesignOfDrawings import (_ViewSection,
                                _CliffLine,
                                _Arrow,
                                _ElevationMark,
                                _Flag,
                                _Knot,
                                _Fragment,
                                _Gidroisolate,
                                _CreateText,
                                _GrebenchAnnotation,
                                _MultiAnnotation,
                                _Multitag,
                                _MultiTagAling,
                                _GrebenchTag,
                                _GrebenchTagAling
                                )
        
        class EventHandler(IExternalEventHandler):
            """
            Вспомагательный класс для активации скрипта
            """

            def __init__(self, do_this):
                self.do_this = do_this

            def Execute(self, uiapp):
                try:
                    self.do_this()
                except InvalidOperationException:
                    print ("InvalidOperationException не уcтановлен")

            def GetName(self):
                return "simple function"

        '''
        Для каждой функции кнопи повторяем действие
        # 1) Создать экзепяр класса EventHandler
        simple_event_handler = EventHandler(_ViewSection.start)
        # 2) Создать ExternalEvent
        ext_event = ExternalEvent.Create(simple_event_handler)
        '''

        # ----- 2D узлы -----
        _ViewSectionHandler = EventHandler(_ViewSection.start)
        _ViewSectionExternalEvent = ExternalEvent.Create(_ViewSectionHandler)

        _CliffLineHandler = EventHandler(_CliffLine.start)
        _CliffLineExternalEvent = ExternalEvent.Create(_CliffLineHandler)

        _ArrowHandler = EventHandler(_Arrow.start)
        _ArrowExternalEvent = ExternalEvent.Create(_ArrowHandler)

        _ElevationMarkHandler = EventHandler(_ElevationMark.start)
        _ElevationMarkExternalEvent = ExternalEvent.Create(_ElevationMarkHandler)

        _FlagHandler = EventHandler(_Flag.start)
        _FlagExternalEvent = ExternalEvent.Create(_FlagHandler)

        _KnotHandler = EventHandler(_Knot.start)
        _KnotExternalEvent = ExternalEvent.Create(_KnotHandler)

        _FragmentHandler = EventHandler(_Fragment.start)
        _FragmentExternalEvent = ExternalEvent.Create(_FragmentHandler)

        _GidroisolateHandler = EventHandler(_Gidroisolate.start)
        _GidroisolateExternalEvent = ExternalEvent.Create(_GidroisolateHandler)


        # ----- Текстовые аннотации -----
        _CreateTextHandler = EventHandler(_CreateText.start)
        _CreateTextExternalEvent = ExternalEvent.Create(_CreateTextHandler)

        _GrebenchAnnotationHandler = EventHandler(_GrebenchAnnotation.start)
        _GrebenchAnnotationExternalEvent = ExternalEvent.Create(_GrebenchAnnotationHandler)

        _MultiAnnotationHandler = EventHandler(_MultiAnnotation.start)
        _MultiAnnotationExternalEvent = ExternalEvent.Create(_MultiAnnotationHandler)

        # ----- Марки -----
        _MultitagHandler = EventHandler(_Multitag.start)
        _MultitagExternalEvent = ExternalEvent.Create(_MultitagHandler)

        _MultiTagAlingHandler = EventHandler(_MultiTagAling.start)
        _MultiTagAlingExternalEvent = ExternalEvent.Create(_MultiTagAlingHandler)

        _GrebenchTagHandler = EventHandler(_GrebenchTag.start)
        _GrebenchTagExternalEvent = ExternalEvent.Create(_GrebenchTagHandler)

        _GrebenchTagAlingHandler = EventHandler(_GrebenchTagAling.start)
        _GrebenchTagAlingExternalEvent = ExternalEvent.Create(_GrebenchTagAlingHandler)

        class ModelessForm(WPFWindow):
            """
            Simple modeless form sample
            """

            def __init__(self, xaml_file_name):
                WPFWindow.__init__(self, xaml_file_name)
                self.Show()

            def ViewSection(self, sender, e):
                _ViewSectionExternalEvent.Raise()

            def CliffLine(self, sender, e):
                _CliffLineExternalEvent.Raise()

            def ElevationMark(self, sender, e):
                _ElevationMarkExternalEvent.Raise()

            def Arrow(self, sender, e):
                _ArrowExternalEvent.Raise()

            def Knot(self, sender, e):
                _KnotExternalEvent.Raise()

            def Flag(self, sender, e):
                _FlagExternalEvent.Raise()

            def Fragment(self, sender, e):
                _FragmentExternalEvent.Raise()

            def Gidroisolate(self, sender, e):
                _GidroisolateExternalEvent.Raise()

            # ----- Текстовые аннотации -----
            def CreateText(self, sender, e):
                _CreateTextExternalEvent.Raise()

            def GrebenchAnnotation(self, sender, e):
                _GrebenchAnnotationExternalEvent.Raise()

            def MultiAnatation(self, sender, e):
                _MultiAnnotationExternalEvent.Raise()

            # ----- Марки -----
            def Info(self, sender, e):
                forms.alert('Инструменты раздела "Марки" имеет одно серьезное ограничение.\n Нельзя использовать на активированном видовом экране на листе.', title='Важная информация')
                
            def MultiTag(self, sender, e):
                _MultitagExternalEvent.Raise()

            def MultiTagAling(self, sender, e):
                _MultiTagAlingExternalEvent.Raise()


            def GrebenchTag(self, sender, e):
                _GrebenchTagExternalEvent.Raise()

            def GrebenchTagAling(self, sender, e):
                _GrebenchTagAlingExternalEvent.Raise()

        modeless_form = ModelessForm("ModelessForm.xaml")
    else:
        forms.alert("На данном виде запуск невозможен!")
except:
    pass