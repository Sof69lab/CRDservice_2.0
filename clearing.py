import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'formsite.settings')
django.setup()
from formapp.models import files

# folder_path = "D:/Webpool/CRDservice/media/Tables"
# for filename in os.listdir(folder_path):
#     file_path = os.path.join(folder_path, filename)
#     try:
#         if os.path.isfile(file_path):
#             os.remove(file_path)
#     except Exception as e:
#         print(f'Ошибка удаления файла {file_path}. {e}')

folder_path ="/home/user/Документы/webCRDS/CRDservice/media"
for directory in os.listdir(folder_path):
    if directory != 'Tables':
        dir_path = os.path.join(folder_path, directory)
        for file in os.listdir(dir_path):
            file_path = os.path.join(dir_path, file)
            if os.path.isfile(file_path):
                file_name = os.path.join(directory, file)
                if len(files.objects.filter(file=file_name)) == 0:
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f'Ошибка удаления файла {file_path}. {e}')
            else:
                for f in os.listdir(file_path):
                    file_name = os.path.join(directory, file)
                    file_name = os.path.join(file_name, f)
                    if len(files.objects.filter(file=file_name)) == 0:
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            print(f'Ошибка удаления файла {file_path}. {e}')
