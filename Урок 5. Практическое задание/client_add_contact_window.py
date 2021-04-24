'''


'''

import sys
import logging

from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QPushButton
from PyQt5 import QtWidgets, uic

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem

############################################################################
logger = logging.getLogger('client')

############################################################################
class AddContactDialog(QDialog):
    def __init__(self, transport, database):
        super().__init__()
        self.transport = transport
        self.database = database

        uic.loadUi('ClientAddContactWindow.ui', self)
        self.setWindowTitle('Add contact')


        self.possible_contacts_update()
        # Назначаем действие на кнопку обновить
        #self.buttonBox.accepted.connect(self.update_possible_contacts)

        self.btn_add.clicked.connect(self.update_possible_contacts)
        self.btn_cancel.clicked.connect(self.close)
        self.btn_refresh.clicked.connect(self.update_possible_contacts)
        #self.buttonBox.accepted.connect(self.clickOk)

        #connect(ui->buttonBox->button(QDialogButtonBox::Reset), SIGNAL(clicked()), SLOT(on_reset_clicked())

    ###############################################
    def possible_contacts_update(self):
        self.selector.clear()
        contacts_list = set(self.database.get_contacts())
        users_list = set(self.database.get_users())
        users_list.remove(self.transport.username)
        self.selector.addItems(users_list - contacts_list)

    ###############################################
    def update_possible_contacts(self):
        try:
            self.transport.user_list_update()
        except OSError:
            pass
        else:
            logger.debug('Обновление списка пользователей с сервера выполнено')
            self.possible_contacts_update()
