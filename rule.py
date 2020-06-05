# -*- coding: utf-8 -*-

import os
import os.path
import json

from PyQt5 import uic
from PyQt5.QtCore import pyqtSlot, QSize
from PyQt5 import QtWidgets

from qgis.PyQt import QtCore
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsProject, QgsVectorLayer, QgsGeometry
from qgis.utils import iface

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'rule.ui'))


class Rule(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        '''Constructor.'''

        super(Rule, self).__init__(parent)
        self.setupUi(self)

        self.the_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.the_dir,  'data')
        self.rules_json = os.path.join(self.data_dir, 'rules.json')
        self.tmp_json = os.path.join(self.data_dir, 'tmp.json')

        self.set_button(self.infoButton, 'info.png', self.info_rule)
        self.set_button(self.editButton, 'edit.png', self.edit_rule)
        self.set_button(self.deleteButton, 'delete.png', self.delete_rule)

    def set_button(self, button, icon_name, action):
        icon_path = ':/plugins/rule_based_topology/img/' + icon_name
        button.setIcon(QIcon(icon_path))
        button.setIconSize(QSize(13, 13))
        button.clicked.connect(action)

    def info_rule(self):

        with open(self.tmp_json) as data:
            tmp = json.load(data)

        tmp['rule_info'] = self.ruleTitleLabel.text()

        with open(self.tmp_json, 'w') as data:
            json.dump(tmp, data)

    def edit_rule(self):

        with open(self.tmp_json) as data:
            tmp = json.load(data)

        json_acceptable_string = self.whatsThis().replace("'", "\"")
        rule_data = json.loads(json_acceptable_string)
        rule_data['title'] = self.ruleTitleLabel.text()
        tmp['rule_edit'] = rule_data

        with open(self.tmp_json, 'w') as data:
            json.dump(tmp, data)

    def delete_rule(self):
        '''Delete chosen rule from rule.json file'''
        try:
            with open(self.rules_json) as data:
                rules = json.load(data)
            rules.pop(self.ruleTitleLabel.text())

            with open(self.rules_json, 'w') as data:
                json.dump(rules, data)

        except Exception as e:
            print('Something happened at delete_rule [%s]' % (e))
