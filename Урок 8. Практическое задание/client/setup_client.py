'''
server_setup.py
'''

'''
c)	cx_freeze некорректно обрабатывает SQLAlchemy, поэтому после подготовки дистрибутива нужно вручную заменить папку sqlalchemy в папке lib на аналогичную папку из директории интерпретатора.
d)	Перейдите в директорию lib -> PyQt5 -> Qt -> plugins. Нужно вырезать папку platforms и перенести в директорию, где находится exe-файл.

"No module named 'encodings" починилось после
pip install git+https://github.com/anthony-tuininga/cx_Freeze.git

https://coderoad.ru/28258991/%D0%9E%D1%88%D0%B8%D0%B1%D0%BA%D0%B0-cx_Freeze-Fatal-Python-Py_Initialize-%D0%BD%D0%B5-%D1%83%D0%B4%D0%B0%D0%BB%D0%BE%D1%81%D1%8C-%D0%BF%D0%BE%D0%BB%D1%83%D1%87%D0%B8%D1%82%D1%8C-%D0%BA%D0%BE%D0%B4%D0%B8%D1%80%D0%BE%D0%B2%D0%BA%D1%83

'''

import sys
from cx_Freeze import setup, Executable
build_exe_options = {
    "packages": ["common_defs", "log", "client", "codecs", "encodings", "sqlalchemy"],
    "include_files": ["ClientConnectWindow.ui",
                      "ClientMainWindow.ui",
                      "ServerMainWindow.ui",
                      "ClientAddContactWindow.ui",
                      ],
}
setup(
    name="msg_client",
    version="0.0.0.1",
    description="msg_client",
    options={
        "build_exe": build_exe_options
    },
    executables=[Executable('client.py',
                            # base='Win32GUI',
                            targetName='client.exe',
                            )]
)
