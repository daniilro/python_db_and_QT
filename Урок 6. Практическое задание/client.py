'''


'''

import argparse
import sys
import os

from Cryptodome.PublicKey import RSA

from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import qApp, QMessageBox

from client_db import ClientDatabase
from client_main_window import ClientMainWindow
from common_defs import *
from errors import ServerError
from transport import ClientTransport

################################################################


LOGGER = logging.getLogger('client')


################################################################
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEF_IP_ADDR, nargs='?')
    parser.add_argument('port', default=DEF_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    parser.add_argument('-p', '--password', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name
    client_passwd = namespace.password

    # проверим подходящий номер порта
    if not 1023 < server_port < 65536:
        LOGGER.critical(
            f'Попытка запуска клиента с неподходящим номером порта: {server_port}. Допустимы адреса с 1024 до 65535. Клиент завершается.')
        exit(1)

    return server_address, server_port, client_name, client_passwd


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
    server_address, server_port, client_name, client_passwd = get_args()

    app = QtWidgets.QApplication(sys.argv)
    connect_window = ClientConnectWindow()
    connect_window.show()
    app.exec_()

    if not connect_window.ok_pressed:
        print("User interrupt")
        exit(0)

    server_address, server_port, client_name, client_passwd = connect_window.host.text(
    ), connect_window.port.text(), connect_window.client_name.text(), connect_window.client_passwd.text()

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

    dir_path = os.path.dirname(os.path.realpath(__file__))
    key_file = os.path.join(dir_path, f'{client_name}.key')
    if not os.path.exists(key_file):
        keys = RSA.generate(2048, os.urandom)
        with open(key_file, 'wb') as key:
            key.write(keys.export_key())
    else:
        with open(key_file, 'rb') as key:
            keys = RSA.import_key(key.read())

    LOGGER.debug("Keys sucsessfully loaded.")

    database = ClientDatabase(client_name)

    try:
        transport = ClientTransport(
            server_port,
            server_address,
            database,
            client_name,
            client_passwd,
            keys)
    except ServerError as error:
        LOGGER.fatal(error.text)
        QMessageBox.critical(
            connect_window,
            'Error',
            error.text,
            QMessageBox.Ok)
        exit(1)

    del connect_window

    transport.setDaemon(True)
    transport.start()

    client_app = QtWidgets.QApplication(sys.argv)
    main_window = ClientMainWindow(database, transport, keys)
    main_window.show()
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'"{client_name}" chat')
    client_app.exec_()

    transport.transport_shutdown()
    transport.join()
