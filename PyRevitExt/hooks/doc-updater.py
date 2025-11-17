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

    # sender = __eventsender__
    args   = __eventargs__
    doc_for_update = args.GetDocument()
    doc_active_view = doc_for_update.ActiveView

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
                if s in '⌀ØqwertyuiuopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNMйцукенгшщзхъфывапролдэячсмитьёбБЁЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЭЯЧСМИТЬ=+#$^&*?~"№Ø1234567890': size += 2
                elif s in  ' ;:,.`()[]{}!°/-³': size += 1
                elif s in  "'": size += 1
                elif s in  "ЛжЖ": size += 3
            else: 
                size = 1
        return size

#==================================================
#MAIN
#==================================================

    # scale_views = float(doc_active_view.LookupParameter("Масштаб вида").AsInteger())

    modified_el_ids = args.GetModifiedElementIds()

    modified_el = [doc_for_update.GetElement(e_id) for e_id in modified_el_ids]
    modified_el_id = [e_id for e_id in modified_el_ids]

    if all([type(el) == AnnotationSymbol and (('ADSK_Аннотация_Текст_сВыноской' in el.LookupParameter('Семейство').AsValueString())
                                              or (('ADSK_A_Текст с выноской' in el.LookupParameter('Семейство').AsValueString()))
                                              ) for el in modified_el]):
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

                if len(top_txt) == len(lower_txt):
                    max_value = top_txt
                else:
                    max_value = max(top_txt,lower_txt, key=len)

                annot_size = approximate_gostcommon_string_width(max_value)
                new_size = (round(float(annot_size) - float(annot_size)*0.1))/304.8
                
                if str(annot_size) == width.AsValueString():
                    pass
                else:
                    width.Set(new_size)
                    
except System.MissingMemberException:
    pass
except Exception as ex:
    print(ex)
