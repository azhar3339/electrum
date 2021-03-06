#!/usr/bin/env python
#
# Electrum - lightweight Bitcoin client
# Copyright (C) 2013 ecdsa@github
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from electrum.i18n import _
from util import *



def make_password_dialog(self, wallet, msg, new_pass=True):

    self.pw = QLineEdit()
    self.pw.setEchoMode(2)
    self.new_pw = QLineEdit()
    self.new_pw.setEchoMode(2)
    self.conf_pw = QLineEdit()
    self.conf_pw.setEchoMode(2)
    #Password Strength Label
    self.pw_strength = QLabel("Password Strength:<font color=""red""> Empty </font> ")
    
    vbox = QVBoxLayout()
    label = QLabel(msg)
    label.setWordWrap(True)

    grid = QGridLayout()
    grid.setSpacing(8)
    grid.setColumnMinimumWidth(0, 70)
    grid.setColumnStretch(1,1)

    logo = QLabel()
    lockfile = ":icons/lock.png" if wallet and wallet.use_encryption else ":icons/unlock.png"
    logo.setPixmap(QPixmap(lockfile).scaledToWidth(36))
    logo.setAlignment(Qt.AlignCenter)

    grid.addWidget(logo,  0, 0)
    grid.addWidget(label, 0, 1, 1, 2)
    vbox.addLayout(grid)

    grid = QGridLayout()
    grid.setSpacing(8)
    grid.setColumnMinimumWidth(0, 250)
    grid.setColumnStretch(1,1)
    
    if wallet and wallet.use_encryption:
        grid.addWidget(QLabel(_('Password')), 0, 0)
        grid.addWidget(self.pw, 0, 1)

    grid.addWidget(QLabel(_('New Password') if new_pass else _('Password')), 1, 0)
    grid.addWidget(self.new_pw, 1, 1)

    #add Password Strength Label to grid
    grid.addWidget(self.pw_strength, 1, 2)

    grid.addWidget(QLabel(_('Confirm Password')), 2, 0)
    grid.addWidget(self.conf_pw, 2, 1)
    vbox.addLayout(grid)

    #Add an event handler to update password strength interactively
    self.connect(self.new_pw, SIGNAL("textChanged(QString)"), lambda: update_password_strength(self.pw_strength,self.new_pw.text()))

    vbox.addStretch(1)
    vbox.addLayout(ok_cancel_buttons(self))
    return vbox


def run_password_dialog(self, wallet, parent):
        
    if wallet and wallet.is_watching_only():
        QMessageBox.information(parent, _('Error'), _('This is a watching-only wallet'), _('OK'))
        return False, None, None

    if not self.exec_():
        return False, None, None

    password = unicode(self.pw.text()) if wallet and wallet.use_encryption else None
    new_password = unicode(self.new_pw.text())
    new_password2 = unicode(self.conf_pw.text())

    if new_password != new_password2:
        QMessageBox.warning(parent, _('Error'), _('Passwords do not match'), _('OK'))
        # Retry
        return run_password_dialog(self, wallet, parent)

    if not new_password:
        new_password = None

    return True, password, new_password


def check_password_strength(password):

    '''
    Check the strength of the password entered by the user and return back the same
    A higher weightage is given to the length
    :param password: password entered by user in New Password
    :return: password strength Weak or Medium or Strong
    '''

    entropy = 0

    if len(password) == 0:
        return "Empty"

    for character in str(password):
        if character.islower():
            entropy += 1
        elif character.isupper():
            entropy += 1.5
        elif character.isdigit():
            entropy += 1.5
        else:
            entropy += 1.5

    #Discouraging the use of same characters
    distinct = ''.join(set(str(password)))
    if len(distinct) < 5 :
        entropy = 0

    if entropy < 15:
        strength = "Weak"
    elif 15 <= entropy < 20:
        strength = "Medium"
    else:
        strength = "Strong"

    return strength


def update_password_strength(pw_strength_label,password):

    '''
    call the passwordmeter module and update the label pw_strength interactively as the user is typing the password
    :param pw_strength_label: the label pw_strength
    :param password: password entered in New Password text box
    :return: None
    '''
    colors = {"Empty":"Red","Weak":"Red","Medium":"Blue","Strong":"Green"}
    strength = check_password_strength(password)
    pw_strength_label.setText("Password Strength:<font color=" + colors[strength] + ">" + strength + "</font>")




class PasswordDialog(QDialog):

    def __init__(self, wallet, parent):
        QDialog.__init__(self, parent)
        self.setModal(1)
        self.wallet = wallet
        self.parent = parent
        self.setWindowTitle(_("Set Password"))
        msg = (_('Your wallet is encrypted. Use this dialog to change your password.') + ' '\
               +_('To disable wallet encryption, enter an empty new password.')) \
               if wallet.use_encryption else _('Your wallet keys are not encrypted')
        self.setLayout(make_password_dialog(self, wallet, msg))


    def run(self):
        ok, password, new_password = run_password_dialog(self, self.wallet, self.parent)
        if not ok:
            return

        try:
            self.wallet.check_password(password)
        except Exception:
            QMessageBox.warning(self.parent, _('Error'), _('Incorrect Password'), _('OK'))
            return False, None, None

        try:
            self.wallet.update_password(password, new_password)
        except:
            import traceback, sys
            traceback.print_exc(file=sys.stdout)
            QMessageBox.warning(self.parent, _('Error'), _('Failed to update password'), _('OK'))
            return

        if new_password:
            QMessageBox.information(self.parent, _('Success'), _('Password was updated successfully'), _('OK'))
        else:
            QMessageBox.information(self.parent, _('Success'), _('This wallet is not encrypted'), _('OK'))




