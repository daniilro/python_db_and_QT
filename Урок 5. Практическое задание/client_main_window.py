'''


'''

import argparse
import sys

from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import qApp, QMessageBox, QMainWindow, QDialog

from client_db import ClientDB
from errors import IncorrectDataRecivedError, ReqFieldMissingError, ServerError
from transport import ClientTransport
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor


from  PyQt5.QtCore import QAbstractListModel


from PyQt5.QtCore import *
from PyQt5.QtGui import *

from common_defs import *

from client_add_contact_window import AddContactDialog

##############################################################################
LOGGER = logging.getLogger('client')

##############################################################################



class listModel(QAbstractListModel):
    def __init__(self, datain, parent=None, *args):
        QAbstractListModel.__init__(self, parent, *args)
        self.listdata = datain

    def rowCount(self, parent=QModelIndex()):
        return len(self.listdata)

    def data(self, index, role):
        if index.isValid() and role == Qt.DisplayRole:
            return QVariant(self.listdata[index.row()])
        else:
            return QVariant()








##############################################################################
class ClientMainWindow(QMainWindow):
    def __init__(self, database, transport):
        super().__init__()

        self.database = database
        self.transport = transport

        uic.loadUi('ClientMainWindow.ui', self)
        self.setWindowTitle('Server connection parameters')




        #self.menu_exit.triggered.connect(qApp.exit)
        self.actionExit.triggered.connect(qApp.exit)



        # contacts ##########################################################
        self.btn_add_contact.clicked.connect(self.add_contact_window)
        #self.menu_add_contact.triggered.connect(self.add_contact_window)
        self.btn_remove_contact.clicked.connect(self.delete_contact)
        #self.menu_del_contact.triggered.connect(self.delete_contact_window)

        self.btn_clear.clicked.connect(self.text_message.clear)
        self.btn_send.clicked.connect(self.send_message)

        self.contacts_model = None
        self.history_model = None

        self.messages = QMessageBox()

        self.current_chat = None

        self.list_contacts.doubleClicked.connect(self.select_active_user)
        self.clients_list_update()
        self.set_disabled_input()
        self.show()


    def send_message(self):
        # Текст в поле, проверяем что поле не пустое затем забирается сообщение и поле очищается
        message_text = self.text_message.toPlainText()
        self.text_message.clear()
        if not message_text:
            return
        try:
            self.transport.send_message(self.current_chat, message_text)
            pass
        except ServerError as err:
            self.messages.critical(self, 'Ошибка', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения 2!')
        except (ConnectionResetError, ConnectionAbortedError):
            self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
            self.close()
        else:
            self.database.save_message(self.current_chat, 'out', message_text)
            LOGGER.debug(f'Отправлено сообщение для {self.current_chat}: {message_text}')
            self.history_list_update()

    def history_list_update(self):
        # Получаем историю сортированную по дате
        list = sorted(self.database.get_history(self.current_chat), key=lambda item: item[3])
        # Если модель не создана, создадим.
        if not self.history_model:
            self.history_model = QStandardItemModel()
            self.list_messages.setModel(self.history_model)
        # Очистим от старых записей
        self.history_model.clear()
        # Берём не более 20 последних записей.
        length = len(list)
        start_index = 0
        if length > 20:
            start_index = length - 20
        # Заполнение модели записями, так-же стоит разделить входящие и исходящие выравниванием и разным фоном.
        # Записи в обратном порядке, поэтому выбираем их с конца и не более 20
        for i in range(start_index, length):
            item = list[i]
            if item[1] == 'in':
                mess = QStandardItem(f'Входящее от {item[3].replace(microsecond=0)}:\n {item[2]}')
                mess.setEditable(False)
                mess.setBackground(QBrush(QColor(255, 213, 213)))
                mess.setTextAlignment(Qt.AlignLeft)
                self.history_model.appendRow(mess)
            else:
                mess = QStandardItem(f'Исходящее от {item[3].replace(microsecond=0)}:\n {item[2]}')
                mess.setEditable(False)
                mess.setTextAlignment(Qt.AlignRight)
                mess.setBackground(QBrush(QColor(204, 255, 204)))
                self.history_model.appendRow(mess)
        self.list_messages.scrollToBottom()


    def select_active_user(self):
        # Выбранный пользователем (даблклик) находится в выделеном элементе в QListView
        self.current_chat = self.list_contacts.currentIndex().data()
        # вызываем основную функцию
        self.set_active_user()

    # Функция устанавливающяя активного собеседника
    def set_active_user(self):
        # Ставим надпись и активируем кнопки
        self.label_new_message.setText(f'Введите сообщенние для {self.current_chat}:')
        self.btn_clear.setDisabled(False)
        self.btn_send.setDisabled(False)
        self.text_message.setDisabled(False)

    def set_disabled_input(self):
        # Надпись  - получатель.
        self.label_new_message.setText('Для выбора получателя дважды кликните на нем в окне контактов.')
        self.text_message.clear()
        if self.history_model:
            self.history_model.clear()

        # Поле ввода и кнопка отправки неактивны до выбора получателя.
        self.btn_clear.setDisabled(True)
        self.btn_send.setDisabled(True)
        self.text_message.setDisabled(True)



    #################################################################################
    def delete_contact(self):
        LOGGER.info("delete contact")

        if not self.list_contacts.selectedIndexes():
            msg = "No contact selected for delete"
            LOGGER.info(msg)
            self.messages.information(self, 'Delete contact', msg, QMessageBox.Ok)

            return
        item = self.contacts_model.item(self.list_contacts.selectedIndexes()[0].row()).text()


        selected = item
        try:
            self.transport.remove_contact(selected)
        except ServerError as err:
            self.messages.critical(self, 'Ошибка сервера', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        else:
            self.database.del_contact(selected)
            self.clients_list_update()
            msg = f'Успешно удалён контакт "{selected}"'
            LOGGER.info(msg)
            self.messages.information(self, 'Delete contact', msg, QMessageBox.Ok)

    ############################################################################
    def add_contact_window(self):
        global select_dialog
        select_dialog = AddContactDialog(self.transport, self.database)
        select_dialog.btn_add.clicked.connect(lambda: self.add_contact_action(select_dialog))
        select_dialog.show()

    ############################################################################
    def add_contact_action(self, item):
        new_contact = item.selector.currentText()
        self.add_contact(new_contact)
        item.close()


    ############################################################################
    def add_contact(self, new_contact):
        try:
            self.transport.add_contact(new_contact)
        except ServerError as err:
            self.messages.critical(self, 'Ошибка сервера', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        else:
            self.database.add_contact(new_contact)
            new_contact = QStandardItem(new_contact)
            new_contact.setEditable(False)
            self.contacts_model.appendRow(new_contact)
            msg = f'Успешно добавлен контакт "{new_contact.text()}"'
            LOGGER.info(msg)
            self.messages.information(self, 'Success', msg, QMessageBox.Ok)















    ##############################################################################
    def make_connection(self, trans_obj):
        trans_obj.new_message.connect(self.message)
        trans_obj.connection_lost.connect(self.connection_lost)

    ##############################################################################
    #@pyqtSlot(str)
    def message(self, sender):
        if sender == self.current_chat:
            self.history_list_update()
        else:
            # Проверим есть ли такой пользователь у нас в контактах:
            if self.database.check_contact(sender):
                # Если есть, спрашиваем и желании открыть с ним чат и открываем при желании
                if self.messages.question(self, 'Новое сообщение', \
                                          f'Получено новое сообщение от {sender}, открыть чат с ним?', QMessageBox.Yes,
                                          QMessageBox.No) == QMessageBox.Yes:
                    self.current_chat = sender
                    self.set_active_user()
            else:
                print('NO')
                # Раз нету,спрашиваем хотим ли добавить юзера в контакты.
                if self.messages.question(self, 'Новое сообщение', \
                                          f'Получено новое сообщение от {sender}.\n Данного пользователя нет в вашем контакт-листе.\n Добавить в контакты и открыть чат с ним?',
                                          QMessageBox.Yes,
                                          QMessageBox.No) == QMessageBox.Yes:
                    self.add_contact(sender)
                    self.current_chat = sender
                    self.set_active_user()

    ##############################################################################
    #@pyqtSlot()
    def connection_lost(self):
        self.messages.warning(self, 'Сбой соединения', 'Потеряно соединение с сервером. ')
        self.close()

    ##############################################################################
    def clients_list_update(self):
        contacts_list = self.database.get_contacts()
        self.contacts_model = QStandardItemModel()
        for i in sorted(contacts_list):
            item = QStandardItem(i)
            item.setEditable(False)
            self.contacts_model.appendRow(item)
        self.list_contacts.setModel(self.contacts_model)

