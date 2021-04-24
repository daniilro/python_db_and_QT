'''


'''

import argparse
import sys

from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import qApp, QMessageBox

from client_db import ClientDB
from client_main_window import ClientMainWindow
from common_defs import *
from errors import ServerError
from transport import ClientTransport

################################################################


LOGGER = logging.getLogger('client')


################################################################
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--addr", default=DEF_IP_ADDR)
    parser.add_argument("-p", "--port", type=int, default=DEF_PORT)
    # parser.add_argument('-n', '--name', default=None, nargs='?')
    parser.add_argument('-n', '--name', default='test_user', nargs='?')
    args = parser.parse_args()
    if int(args.port) < 1024 or int(args.port) > 65535:
        LOGGER.fatal(
            f'Попытка запуска поцесса с неподходящим номером порта: {int(args.port)}.'
            f' Допустимы адреса с 1024 до 65535. Поцесс завершается.')
        exit(1)
    return args.addr, int(args.port), args.name


################################################################
class ClientConnectWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):
        self.ok_pressed = False
        QtWidgets.QWidget.__init__(self, parent)
        uic.loadUi('ClientConnectWindow.ui', self)
        self.setWindowTitle('Server connection parameters')
        self.buttonBox.accepted.connect(self.clickOk)
        self.buttonBox.rejected.connect(QtWidgets.qApp.quit)
        self.host.setText(server_address)
        self.port.setText(str(server_port))
        self.client_name.setText(client_name)

    ################################################################
    def clickOk(self):
        print(f"Host: {self.host.text()}")
        print(f"Port: {self.port.text()}")
        print(f"Client name: {self.client_name.text()}")
        self.ok_pressed = True
        qApp.exit()


################################################################
if __name__ == '__main__':

    # login ###############################################################
    server_address, server_port, client_name = get_args()

    app = QtWidgets.QApplication(sys.argv)
    connect_window = ClientConnectWindow()
    connect_window.show()
    app.exec_()

    if not connect_window.ok_pressed:
        print("User interrupt")
        exit(0)

    server_address, server_port, client_name = connect_window.host.text(), connect_window.port.text(), connect_window.client_name.text()

    if not server_port.isdigit():
        mess = f'Задан неверный номер порта: {server_port}.' \
               f' Номером порта должен быть цифровой.'
        LOGGER.fatal(mess)
        QMessageBox.critical(connect_window, 'Error', mess, QMessageBox.Ok)
        sys.exit(-1)
    server_port = int(server_port)
    if int(server_port) < 1024 or int(server_port) > 65535:
        mess = f'Попытка запуска поцесса с неподходящим номером порта: {int(server_port)}.' \
               f' Допустимы адреса с 1024 до 65535. Поцесс завершается.'
        LOGGER.fatal(mess)
        QMessageBox.critical(connect_window, 'Error', mess, QMessageBox.Ok)
        sys.exit(-1)

    # main ###############################################################

    database = ClientDB(client_name)

    # Создаём объект - транспорт и запускаем транспортный поток
    try:
        transport = ClientTransport(server_port, server_address, database, client_name)
    except ServerError as error:
        LOGGER.fatal(error.text)
        QMessageBox.critical(connect_window, 'Error', error.text, QMessageBox.Ok)
        exit(1)

    del connect_window

    transport.setDaemon(True)
    transport.start()

    # Создаём GUI
    client_app = QtWidgets.QApplication(sys.argv)
    main_window = ClientMainWindow(database, transport)
    main_window.show()
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'"{client_name}" chat')
    client_app.exec_()

    # Раз графическая оболочка закрылась, закрываем транспорт
    transport.transport_shutdown()
    transport.join()

#    sys.exit(status)
