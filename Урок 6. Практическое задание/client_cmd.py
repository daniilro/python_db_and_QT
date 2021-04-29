'''


'''
import argparse
import json
import socket
import threading
import time

from tabulate import tabulate

from client_db import ClientDB
from common_defs import *
from common_defs.messages import send_message, get_my_message
from decors import log
from errors import IncorrectDataRecivedError, ReqFieldMissingError, ServerError
from metas import ClientMaker

LOGGER = logging.getLogger('client')

sock_lock = threading.Lock()
database_lock = threading.Lock()


##########################################################################
class ClientSender(threading.Thread, metaclass=ClientMaker):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database

        super().__init__()

    def create_exit_message(self):
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.account_name
        }

    ##########################################################################
    def create_message(self):
        to = input('Введите получателя сообщения: ')
        message = input('Введите сообщение для отправки: ')
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.account_name,
            DESTINATION: to,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')

        with database_lock:
            self.database.save_message(self.account_name, to, message)

        try:
            send_message(self.sock, message_dict)
            LOGGER.info(f'Отправлено сообщение для пользователя {to}')
        except BaseException:
            LOGGER.critical('Потеряно соединение с сервером.')
            exit(1)

    ##########################################################################
    def run(self):
        self.print_help()
        while True:
            command = input('Enter command: ')
            if command == 'message':
                self.create_message()
            elif command == 'help':
                self.print_help()
            elif command == 'exit':
                try:
                    send_message(self.sock, self.create_exit_message())
                except BaseException:
                    pass
                LOGGER.info('Connection closed.')
                # Задержка неоходима, чтобы успело уйти сообщение о выходе
                time.sleep(DEF_TIMEOUT)
                break
            elif command == 'contacts':
                with database_lock:
                    contacts_list = self.database.get_contacts()
                for contact in contacts_list:
                    print(contact)

            elif command == 'edit':
                self.edit_contacts()

            elif command == 'history':
                self.print_history()

            else:
                print('Undefined command.')
                self.print_help()

    ##########################################################################
    def print_help(self):
        print('Поддерживаемые команды:')
        print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('history - история сообщений')
        print('contacts - список контактов')
        print('edit - редактирование списка контактов')
        print('help - вывести подсказки по командам')
        print('exit - выход из программы')

    ##########################################################################
    def edit_contacts(self):
        ans = input('Для удаления введите del, для добавления add: ')
        if ans == 'del':
            edit = input('Введите имя удаляемного контакта: ')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    LOGGER.error('Попытка удаления несуществующего контакта.')
        elif ans == 'add':
            # Проверка на возможность такого контакта
            edit = input('Введите имя создаваемого контакта: ')
            if self.database.check_user(edit):
                with database_lock:
                    self.database.add_contact(edit)
                with sock_lock:
                    try:
                        add_contact(self.sock, self.account_name, edit)
                    except ServerError:
                        LOGGER.error(
                            'Не удалось отправить информацию на сервер.')

    ##########################################################################
    def print_history(self):
        ask = input(
            'Показать входящие сообщения - in, исходящие - out, все - просто Enter: ')
        with database_lock:
            if ask == 'in':
                print(
                    tabulate(
                        self.database.get_history(
                            to_who=self.account_name),
                        headers=[
                            'From',
                            'To',
                            'Message',
                            'Sent']))
            elif ask == 'out':
                print(
                    tabulate(
                        self.database.get_history(
                            from_who=self.account_name),
                        headers=[
                            'From',
                            'To',
                            'Message',
                            'Sent']))
            else:
                print(
                    tabulate(
                        self.database.get_history(),
                        headers=[
                            'From',
                            'To',
                            'Message',
                            'Sent']))


##########################################################################
class ClientReader(threading.Thread, metaclass=ClientMaker):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()

    # Основной цикл приёмника сообщений, принимает сообщения, выводит в
    # консоль. Завершается при потере соединения.
    def run(self):
        while True:
            # Отдыхаем секунду и снова пробуем захватить сокет.
            # если не сделать тут задержку, то второй поток может достаточно
            # долго ждать освобождения сокета.
            time.sleep(1)
            with sock_lock:
                try:
                    message = get_my_message(self.sock)

                except IncorrectDataRecivedError:
                    LOGGER.error(
                        f'Не удалось декодировать полученное сообщение.')
                except OSError as err:
                    if err.errno:
                        LOGGER.critical(f'Потеряно соединение с сервером.')
                        break
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                    LOGGER.critical(f'Потеряно соединение с сервером.')
                    break
                else:
                    if ACTION in message and message[ACTION] == MESSAGE and SENDER in message and DESTINATION in message \
                            and MESSAGE_TEXT in message and message[DESTINATION] == self.account_name:
                        print(
                            f'\nПолучено сообщение от пользователя {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
                        # Захватываем работу с базой данных и сохраняем в неё
                        # сообщение
                        with database_lock:
                            try:
                                self.database.save_message(
                                    message[SENDER], self.account_name, message[MESSAGE_TEXT])
                            except BaseException:
                                LOGGER.error(
                                    'Ошибка взаимодействия с базой данных')

                        LOGGER.info(
                            f'Получено сообщение от пользователя {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
                    else:
                        LOGGER.error(
                            f'Получено некорректное сообщение с сервера: {message}')


##########################################################################
@log
def create_presence(account_name):
    out = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }
    LOGGER.debug(
        f'Сформировано {PRESENCE} сообщение для пользователя {account_name}')
    return out


##########################################################################
@log
def process_response_ans(message):
    LOGGER.debug(f'Разбор приветственного сообщения от сервера: {message}')
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        elif message[RESPONSE] == 400:
            raise ServerError(f'400 : {message[ERROR]}')
    raise ReqFieldMissingError(RESPONSE)
    exit(1)


##########################################################################
def contacts_list_request(sock, name):
    LOGGER.debug(f'Запрос контакт листа для пользователся {name}')
    req = {
        ACTION: GET_CONTACTS,
        TIME: time.time(),
        USER: name
    }
    LOGGER.debug(f'Сформирован запрос {req}')
    send_message(sock, req)
    ans = get_my_message(sock)
    LOGGER.debug(f'Получен ответ {ans}')
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[LIST_INFO]
    else:
        raise ServerError


##########################################################################
def add_contact(sock, username, contact):
    LOGGER.debug(f'Создание контакта {contact}')
    req = {
        ACTION: ADD_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact
    }
    send_message(sock, req)
    ans = get_my_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Ошибка создания контакта')
    print('Удачное создание контакта.')


##########################################################################
def user_list_request(sock, username):
    LOGGER.debug(f'Запрос списка известных пользователей {username}')
    req = {
        ACTION: USERS_REQUEST,
        TIME: time.time(),
        ACCOUNT_NAME: username
    }
    send_message(sock, req)
    ans = get_my_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[LIST_INFO]
    else:
        raise ServerError


##########################################################################
def remove_contact(sock, username, contact):
    LOGGER.debug(f'Создание контакта {contact}')
    req = {
        ACTION: REMOVE_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact
    }
    send_message(sock, req)
    ans = get_my_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Ошибка удаления клиента')
    print('Удачное удаление')


##########################################################################
# @log
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--addr", default=DEF_IP_ADDR)
    parser.add_argument("-p", "--port", type=int, default=DEF_PORT)
    parser.add_argument('-n', '--name', default=None, nargs='?')
    args = parser.parse_args()
    if int(args.port) < 1024 or int(args.port) > 65535:
        LOGGER.fatal(
            f'Попытка запуска поцесса с неподходящим номером порта: {int(args.port)}.'
            f' Допустимы адреса с 1024 до 65535. Поцесс завершается.')
        exit(1)
    return args.addr, int(args.port), args.name


##########################################################################
def database_load(sock, database, username):
    try:
        users_list = user_list_request(sock, username)
    except ServerError:
        LOGGER.error('Ошибка запроса списка известных пользователей.')
    else:
        database.add_users(users_list)

    try:
        contacts_list = contacts_list_request(sock, username)
    except ServerError:
        LOGGER.error('Ошибка запроса списка контактов.')
    else:
        for contact in contacts_list:
            database.add_contact(contact)


##########################################################################
def main():
    print('Client started')

    server_address, server_port, client_name = get_args()

    if not client_name:
        client_name = input('Введите имя пользователя: ')
    else:
        print(f'Клиентский модуль запущен с именем: {client_name}')

    LOGGER.info(
        f'Запущен клиент с парамертами: адрес сервера: {server_address} , порт: {server_port}, имя пользователя: {client_name}')

    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        transport.settimeout(DEF_TIMEOUT)

        transport.connect((server_address, server_port))
        send_message(transport, create_presence(client_name))
        answer = process_response_ans(get_my_message(transport))
        LOGGER.info(
            f'Установлено соединение с сервером. Ответ сервера: {answer}')
        print(f'Установлено соединение с сервером.')
    except json.JSONDecodeError:
        LOGGER.error('Не удалось декодировать полученную Json строку.')
        exit(1)
    except ServerError as error:
        LOGGER.error(
            f'При установке соединения сервер вернул ошибку: {error.text}')
        exit(1)
    except ReqFieldMissingError as missing_error:
        LOGGER.error(
            f'В ответе сервера отсутствует необходимое поле {missing_error.missing_field}')
        exit(1)
    except (ConnectionRefusedError, ConnectionError):
        LOGGER.critical(
            f'Не удалось подключиться к серверу {server_address}:{server_port}, конечный компьютер отверг запрос на подключение.')
        exit(1)
    else:

        database = ClientDB(client_name)
        database_load(transport, database, client_name)

        module_sender = ClientSender(client_name, transport, database)
        module_sender.daemon = True
        module_sender.start()
        LOGGER.debug('Запущены процессы')

        module_receiver = ClientReader(client_name, transport, database)
        module_receiver.daemon = True
        module_receiver.start()

        while True:
            time.sleep(1)
            if module_receiver.is_alive() and module_sender.is_alive():
                continue
            break


##########################################################################
if __name__ == '__main__':
    main()
