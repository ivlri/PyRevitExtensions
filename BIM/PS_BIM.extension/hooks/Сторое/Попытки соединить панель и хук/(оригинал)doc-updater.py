# -*- coding: utf-8 -*-
#==================================================
#⬇️ IMPORTS
#==================================================
try:
    import clr

    import System

    from datetime import datetime
    from Autodesk.Revit.DB import *
    import math

    import string
    #==================================================
    #VARIABLES
    #==================================================

    sender = __eventsender__
    args   = __eventargs__
    doc = args.GetDocument()
    active_view = doc.ActiveView
    #==================================================
    #Func
    #==================================================

    def approximate_gostcommon_string_width(st):
        if len(st) == 0:
            size = 1
        else:
            size = 0
            
        for s in st:
            if s:
                if s in 'qwertyuiuopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNMйцукенгшщзхъфывапролджэячсмитьёЁЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬ1234567890-=+#$^&*?/~"№': size += 2
                elif s in  ';:,.`()[]{}!': size += 1
                elif s in  "'": size += 1
            else: 
                size = 1
        return size

    #==================================================
    #MAIN
    #==================================================
    try:
        scale_views = float(active_view.LookupParameter("Масштаб вида").AsInteger())

        modified_el_ids = args.GetModifiedElementIds()

        modified_el = [doc.GetElement(e_id) for e_id in modified_el_ids]
        modified_el_id = [e_id for e_id in modified_el_ids]

        if all([type(el) == AnnotationSymbol and ('Аннотация_Текст_сВыноской' in el.LookupParameter('Семейство').AsValueString()) for el in modified_el]):
            for el in modified_el:
                width = el.LookupParameter('Ширина полки')

                try:
                    test = width.AsValueString().split(',')[1]
                except:
                    test = '0'

                if test != '0':
                    pass
                else:
                    top_txt = el.LookupParameter('Текст верх').AsValueString()
                    lower_txt = el.LookupParameter('Текст низ').AsValueString()
                    max_value = max(top_txt,lower_txt, key=len)

                    annot_size = approximate_gostcommon_string_width(max_value)
                    #annot_size = len(max_value)*2
                    #new_size = (float(annot_size) - (len(max_value)/2) + 3)/304.8
                    new_size = (float(annot_size))/304.8
                    #new_size = annot_size
                    #print(annot_size,new_size,new_size/scale_views)
                    width.Set(new_size)
    except System.MissingMemberException:
        pass

except Exception as ex:
    #print(ex)
    pass