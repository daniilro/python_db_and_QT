'''


'''

import argparse
# import traceback
import configparser
import os
import select
import socket
import sys
import threading

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication
# import tabulate
from tabulate import tabulate

from common_defs.messages import send_message, get_message
from decors import log
from descrs import Port
from metas import ServerMaker
from server_db import *  # ServerStorage
# MainWindow#, gui_create_model, HistoryWindow, create_stat_model, ConfigWindow
from server_ui import *

###############################################################
LOGGER = logging.getLogger('server')

new_connection = False
conflag_lock = threading.Lock()


@log
def lll():
    pass


###############################################################
# @log
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--addr", default='')
    parser.add_argument("-p", "--port", type=int, default=DEF_PORT)
    args = parser.parse_args()
    return args.addr, int(args.port)


###########################################################

class Server(threading.Thread, metaclass=ServerMaker):
    port = Port()

    ###############################################################
    # @log
    def __init__(self, addr, port, database):
        self.addr = addr
        self.port = port
        self.clients = []
        self.messages = []
        self.names = dict()

        self.database = database

        super().__init__()

    ###############################################################
    # @log
    def init_socket(self):
        LOGGER.info(
            f'Server started. port: {self.port} , IP: {self.addr}.')
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((self.addr, self.port))
        # transport.settimeout(DEF_TIMEOUT)
        transport.settimeout(0.5)

        self.sock = transport
        self.sock.listen()

    ###############################################################
    def run(self):
        global new_connection
        self.init_socket()

        while True:
            # LOGGER.info(f'Waiting for client message')
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                LOGGER.info(f'Connection to {client_address} established ')
                self.clients.append(client)

            recv_data_lst = []
            send_data_lst = []
            err_lst = []

            try:
                if self.clients:
                    recv_data_lst, send_data_lst, err_lst = select.select(
                        self.clients, self.clients, [], 0)
            except OSError as err:
                LOGGER.error(f'Ошибка работы с сокетами: {err}')

            # принимаем сообщения и если ошибка, исключаем клиента.
            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.process_client_message(
                            get_message(client_with_message), client_with_message)
                    except (OSError):
                        # Ищем клиента в словаре клиентов и удаляем его из него
                        # и  базы подключённых
                        LOGGER.info(
                            f'Клиент {client_with_message.getpeername()} отключился от сервера.')
                        for name in self.names:
                            if self.names[name] == client_with_message:
                                self.database.user_logout(name)
                                del self.names[name]
                                break
                        self.clients.remove(client_with_message)
                        with conflag_lock:
                            new_connection = True

            # Если есть сообщения, обрабатываем каждое.
            for message in self.messages:
                try:
                    self.process_message(message, send_data_lst)
                except (ConnectionAbortedError, ConnectionError, ConnectionResetError, ConnectionRefusedError):
                    LOGGER.info(
                        f'Связь с клиентом с именем {message[DESTINATION]} была потеряна')
                    self.clients.remove(self.names[message[DESTINATION]])
                    self.database.user_logout(message[DESTINATION])
                    del self.names[message[DESTINATION]]
                    with conflag_lock:
                        new_connection = True
            self.messages.clear()

            # Если есть сообщения, обрабатываем каждое.

    #            for message in self.messages:
    #                try:
    #                    self.process_message(message, send_data_lst)
    #                except:
    #                    LOGGER.info(f'Связь с клиентом с именем {message[DESTINATION]} была потеряна')
    #                    self.clients.remove(self.names[message[DESTINATION]])
    #                    del self.names[message[DESTINATION]]
    #            self.messages.clear()

    ##########################################################################
    def process_message(self, message, listen_socks):
        if message[DESTINATION] in self.names and self.names[message[DESTINATION]
                                                             ] in listen_socks:
            send_message(self.names[message[DESTINATION]], message)
            LOGGER.info(
                f'Отправлено сообщение пользователю {message[DESTINATION]} от пользователя {message[SENDER]}.')
        elif message[DESTINATION] in self.names and self.names[message[DESTINATION]] not in listen_socks:
            raise ConnectionError
        else:
            LOGGER.error(
                f'Пользователь {message[DESTINATION]} не зарегистрирован на сервере, отправка сообщения невозможна.')

    ##########################################################################
    def process_client_message(self, message, client):
        LOGGER.debug(f'Message fom client : {message}')
        # 1 ###################################################################
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            print(
                "ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:")
            print(f"names : {self.names}")
            if message[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[message[USER][ACCOUNT_NAME]] = client

                client_ip, client_port = client.getpeername()
                self.database.user_login(
                    message[USER][ACCOUNT_NAME], client_ip, client_port)

                send_message(client, RESPONSE_200)

                with conflag_lock:
                    new_connection = True
            else:
                response = RESPONSE_400
                response[ERROR] = 'Имя пользователя уже занято.'
                send_message(client, response)
                self.clients.remove(client)
                client.close()
            return

        # 2 ###################################################################
        elif ACTION in message and message[ACTION] == MESSAGE and DESTINATION in message and TIME in message \
                and SENDER in message and MESSAGE_TEXT in message and self.names[message[SENDER]] == client:
            if message[DESTINATION] in self.names:
                self.messages.append(message)
                self.database.process_message(
                    message[SENDER], message[DESTINATION])
                send_message(client, RESPONSE_200)
            else:
                response = RESPONSE_400
                response[ERROR] = 'Пользователь не зарегистрирован на сервере.'
                send_message(client, response)
            return

        # 3 ################################################################
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:

            self.database.user_logout(message[ACCOUNT_NAME])
            self.clients.remove(self.names[message[ACCOUNT_NAME]])
            self.names[message[ACCOUNT_NAME]].close()
            del self.names[message[ACCOUNT_NAME]]
            return
        ############
        elif ACTION in message and message[ACTION] == GET_CONTACTS and USER in message and \
                self.names[message[USER]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = self.database.get_contacts(message[USER])
            send_message(client, response)

        ############
        elif ACTION in message and message[ACTION] == ADD_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == client:
            self.database.add_contact(message[USER], message[ACCOUNT_NAME])
            send_message(client, RESPONSE_200)

        ############
        elif ACTION in message and message[ACTION] == REMOVE_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == client:
            self.database.remove_contact(message[USER], message[ACCOUNT_NAME])
            send_message(client, RESPONSE_200)

        ############
        elif ACTION in message and message[ACTION] == USERS_REQUEST and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = [user[0]
                                   for user in self.database.users_list()]
            send_message(client, response)

        ############
        else:
            response = RESPONSE_400
            response[ERROR] = 'Запрос некорректен.'
            send_message(client, response)
            return


###############################################################
def print_help():
    print('Поддерживаемые комманды:')
    print('users - список известных пользователей')
    print('connected - список подключенных пользователей')
    print('loghist - история входов пользователя')
    print('exit - завершение работы сервера.')
    print('help - вывод справки по поддерживаемым командам')


###############################################################
def main():
    print("starting main")
    addr, port = get_args()

    database = ServerStorage()

    server = Server(addr, port, database)
    server.daemon = True
    server.start()

    if SERVER_GUI == 'Y':
        main_gui(database)
        exit(0)

    print_help()

    while True:
        command = input('Введите комманду: ')
        if command == 'help':
            print_help()
        elif command == 'exit':
            break
        elif command == 'users':
            print(
                tabulate(
                    database.users_list(),
                    headers=[
                        'Пользователь',
                        'Последний вход']))
        elif command == 'connected':
            print(
                tabulate(
                    database.active_users_list(),
                    headers=[
                        'Пользователь',
                        'IP',
                        'PORT',
                        'Последний вход']))
        elif command == 'loghist':
            name = input(
                'Введите имя пользователя для просмотра истории. Для вывода всей истории, просто нажмите Enter: ')
            print(
                tabulate(
                    database.login_history(name),
                    headers=[
                        'Пользователь',
                        'Время входа',
                        'IP',
                        'PORT']))

        else:
            print('Команда не распознана.')


###############################################################
def main_gui(database):
    #####################################
    def list_update():
        global new_connection
        if new_connection or 1 == 1:
            main_window.active_clients_table.setModel(
                gui_create_model(database))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with conflag_lock:
                new_connection = False

    #####################################
    def show_statistics():
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    #######################################

    # Это была попытка сделать по правильному.
    # Если ini файла нет или там нет нужных эначений то возникают доп. задачи
    # Но по быстрому не получилось
    # Набросок оставил на будущее

    defset = {
        'SETTINGS': {'dtabase_path': '.', },
        'SETTINGS': {'database_file': 'server_base.db3', },
        'SETTINGS': {'default_port': '7777', },
        'SETTINGS': {'listen_address': '', },
    }

    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read_dict(defset)
    config.read(f"{dir_path}/{'server.ini'}")

    def server_config():
        global config_window
        # Создаём окно и заносим в него текущие параметры
        config_window = ConfigWindow()

        config_window.db_path.insert(config['SETTINGS']['Database_path'])
        config_window.db_file.insert(config['SETTINGS']['Database_file'])
        config_window.port.insert(config['SETTINGS']['Default_port'])
        config_window.ip.insert(config['SETTINGS']['Listen_Address'])
        config_window.save_btn.clicked.connect(save_server_config)

    #######################################
    def save_server_config():
        global config_window
        message = QMessageBox()
        config['SETTINGS']['Database_path'] = config_window.db_path.text()
        config['SETTINGS']['Database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            config['SETTINGS']['Listen_Address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['Default_port'] = str(port)
                print(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(
                        config_window, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(
                    config_window,
                    'Ошибка',
                    'Порт должен быть от 1024 до 65536')

    #######################################

    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    main_window.statusBar().showMessage('Server Working')
    main_window.active_clients_table.setModel(gui_create_model(database))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()

    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)

    server_app.exec_()


###############################################################
if __name__ == '__main__':
    main()
