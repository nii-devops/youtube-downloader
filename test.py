from tkinter.filedialog import askdirectory
import pathlib



def get_directory():
    file_dir = askdirectory()
    print(file_dir)


#get_directory()

dl_folder = str(pathlib.Path.home()/ "Downloads").replace("\\", "/")

print(dl_folder)