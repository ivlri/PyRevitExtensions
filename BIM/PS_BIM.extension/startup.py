# # -*- coding: utf-8 -*-
# import clr
# import datetime
# from System.Security.Cryptography import Aes, CryptoStream, CryptoStreamMode
# from System.Text import Encoding
# from System.IO import MemoryStream, StreamReader
# from pyrevit import script
# import random
# from pyrevit.coreutils import envvars


# # Ключ и IV на основе текущей даты (формат: DDMMYYYY)
# current_date = datetime.datetime.now().strftime('%d%m%Y')
# KEY = Encoding.UTF8.GetBytes(current_date.ljust(16, '0')[:16])
# IV = Encoding.UTF8.GetBytes(current_date[::-1].ljust(16, '0')[:16])


# pasw_to_unview = 'unview_password_' + current_date
# pasw_to_load = 'load_password_' + current_date
# pasw_to_unview = 'unview_password_' + current_date

# # if envvars.get_pyrevit_env_var(pasw_to_unview):
# #     encrypted_password = envvars.get_pyrevit_env_var(pasw_to_unview)
# # else:
# #     password = ''.join(str(random.randint(0, 9)) for _ in range(4))
# #     encrypted_password = password

# # print('Сегодняшний пароль:')
# # print(password)



# def encoder(text):
#     aes = Aes.Create()
#     aes.Key = KEY
#     aes.IV = IV
    
#     encryptor = aes.CreateEncryptor()
#     ms = MemoryStream()
#     cs = CryptoStream(ms, encryptor, CryptoStreamMode.Write)
    
#     bt = Encoding.UTF8.GetBytes(text)
#     cs.Write(bt, 0, len(bt))
#     cs.FlushFinalBlock()
    
#     return ms.ToArray()


# def decored(encrypted):
#     aes = Aes.Create()
#     aes.Key = KEY
#     aes.IV = IV
    
#     decryptor = aes.CreateDecryptor()
#     ms = MemoryStream(encrypted)
#     cs = CryptoStream(ms, decryptor, CryptoStreamMode.Read)
#     sr = StreamReader(cs)
    
#     return sr.ReadToEnd()

# # if envvars.get_pyrevit_env_var(pasw_to_unview):
# #     encrypted_password = envvars.get_pyrevit_env_var(pasw_to_unview)
# #     password = decored(encrypted_password)
# # else:
# #     # Если нет - генерируем новый и сохраняем
# #     password = ''.join(str(random.randint(0, 9)) for _ in range(4))
# #     encrypted_password = encoder(password)
# #     env.set_key(pasw_to_unview, encrypted_password)
# #     env.save()

# password = ''.join(str(random.randint(0, 9)) for _ in range(4))
# encrypted_password = encoder(password)


# print('Сегодняшний пароль:')
# print(password)

# print('\nЗашифрованное значение:')
# print(encrypted_password)

# print('\nПроверка дешифрования:')
# print(decored(encrypted_password))