# -*- coding: utf-8 -*-


import os
import os.path
import json
import ast # used to convert string to dictionary
from datetime import datetime

from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, QSize
from qgis.PyQt.QtGui import QIcon

from qgis.core import QgsProject, QgsMapLayer
from qgis.utils import iface

from .rule_based_topology_functions import *

from .rule import Rule
from .result import Result

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'rule_based_topology_dockwidget.ui'))


class RuleBasedTopologyDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        '''Constructor.'''
        super(RuleBasedTopologyDockWidget, self).__init__(parent)

        self.setupUi(self)

        self.title = 'Rule Based Topology'
        # paths
        self.the_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.the_dir,  'data')
        self.rules_json = os.path.join(self.data_dir, 'rules.json')
        self.tmp_json = os.path.join(self.data_dir, 'tmp.json')
        self.translate_json = os.path.join(self.data_dir, 'translate.json')

        # language
        self.setup_language()
        self.langComboBox.currentIndexChanged.connect(self.refresh_language)

        self.rulePlayground.currentChanged.connect(self.tab_changed)
        # tab 'Rules'
        self.rulePlayground.setTabText(0, self.lang('rules'))
        self.refresh_rules_list()
        self.rulesList.clicked.connect(self.click_on_rule)
        self.checkButton.setEnabled(False)
        self.checkButton.setText(self.lang('check'))
        self.checkButton.clicked.connect(self.check_rule)
        # tab '+'
        self.titleLabel.setText(self.lang('rule_title'))

        self.layerLabel1.setText(self.lang('layer1'))
        self.layerComboBox1.currentIndexChanged.connect(lambda: self.refresh_field_list(1))
        self.layerComboBox1.currentIndexChanged.connect(self.refresh_check_list)

        self.fieldLabel1.setText(self.lang('field'))
        self.fieldComboBox1.currentIndexChanged.connect(lambda: self.refresh_field_filter_list(1))
        self.valueLabel1.setText(self.lang('value'))
        self.addFilterButton1.setText('add_field_filter')
        self.addFilterButton1.clicked.connect(lambda: self.add_field_filter(1))

        self.checkLabel.setText(self.lang('check'))
        self.checkComboBox.currentIndexChanged.connect(self.refresh_layer2_list)

        self.layerLabel2.setText(self.lang('layer2'))
        self.layerComboBox2.currentIndexChanged.connect(lambda: self.refresh_field_list(2))
        self.fieldLabel2.setText(self.lang('field'))
        self.fieldComboBox2.currentIndexChanged.connect(lambda: self.refresh_field_filter_list(2))
        self.addFilterButton1.setText(self.lang('add_field_filter'))
        self.addFilterButton2.clicked.connect(lambda: self.add_field_filter(2))

        self.createRuleButton.setText(self.lang('create_rule'))
        self.createRuleButton.clicked.connect(self.create_rule)

        self.resultsLabel.setText(self.lang('results'))

        icon_path = ':/plugins/rule_based_topology/img/down.png'

        self.setStyleSheet(
            '''
            QComboBox[enabled="true"]::down-arrow  {
                image: url(:/plugins/rule_based_topology/img/down.png);
            }
            QComboBox QAbstractItemView {
                selection-color: black;
            }
            '''
        )

    def setup_language(self):
        with open(self.tmp_json) as data:
            tmp = json.load(data)
        self.language = tmp['current_lang']

        with open(self.translate_json) as data:
            languages = json.load(data)
        self.langComboBox.clear()
        for lang in list(languages.keys()):
            self.langComboBox.addItem(lang)
        self.langComboBox.setCurrentText(self.language)

    def lang(self, text):
        '''Translate given word into set language'''
        try:
            # get all languages
            with open(self.translate_json) as data:
                lang = json.load(data)
            # get translations in set language
            translate = lang[self.language]
            # translate given word
            translated = translate[text]
            return translated
        except Exception as e:
            print('Something happened at translation [%s]' % (e))
            return text

    def lang_key(self, text):
        '''Get key from translation'''
        try:
            # get all languages
            with open(self.translate_json) as data:
                lang = json.load(data)
            # get translations in set language
            translate = lang[self.language]
            # get key of translated word
            for key, translation in translate.items():
                if translation == text:
                    return key
        except Exception as e:
            print('Something happened at translation [%s]' % (e))
            return text

    def refresh_language(self):
        self.language = self.langComboBox.currentText()
        with open(self.tmp_json) as data:
            tmp = json.load(data)
        tmp['current_lang'] = self.language
        with open(self.tmp_json, 'w') as data:
            json.dump(tmp, data)
        self.rulePlayground.setTabText(0, self.lang('rules'))
        self.checkButton.setText(self.lang('check'))
        self.titleLabel.setText(self.lang('rule_title'))
        self.layerLabel1.setText(self.lang('layer1'))
        self.fieldLabel1.setText(self.lang('field'))
        self.valueLabel1.setText(self.lang('value'))
        self.addFilterButton1.setText('add_field_filter')
        self.checkLabel.setText(self.lang('check'))
        self.layerLabel2.setText(self.lang('layer2'))
        self.fieldLabel2.setText(self.lang('field'))
        self.addFilterButton1.setText(self.lang('add_field_filter'))
        self.createRuleButton.setText(self.lang('create_rule'))
        self.resultsLabel.setText(self.lang('results'))
        self.rulePlayground.setCurrentIndex(0)

    def set_combo_box_img(self, nr, enabled):
        if enabled:
            self.fieldComboBox1.setStyleSheet(
                '''
                QComboBox::down-arrow  {
                    image: url(:/plugins/rule_based_topology/img/down.png);
                }
                '''
            )
        else:
            self.fieldComboBox1.setStyleSheet(
                '''
                QComboBox::down-arrow  {border: none;}
                '''
            )

    def show_message(self, message):
        '''Show message in result text field'''
        self.resultList.clear()
        for line in message:
            self.resultList.addItem(line)

    def create_file(self, filename):
        '''Create an empty json file.'''
        try:
            if not os.path.isdir(self.data_dir):
                os.mkdir(self.data_dir)
            with open(filename, 'w') as data:
                json.dump({}, data)
        except Exception as e:
            print('Something happened at create_file [%s]' % (e))

    def tab_changed(self):
        '''Update settings when tab is change'''
        self.show_message('')
        if self.rulePlayground.currentIndex() == 0:  # Rules tab
            self.refresh_rules_list()
        elif self.rulePlayground.currentIndex() == 1:  # Create rule tab
            self.titleLineEdit.setText('')
            self.createRuleButton.setText(self.lang('create_rule'))
            self.refresh_layer_list(1)

    # --- All rules tab -------------------------------------------------------

    def refresh_rules_list(self):
        '''Refresh the 'Active rules' list with rules from rules.json file'''

        self.rulesList.clear()

        # get rules from rules_json file
        if os.path.isfile(self.rules_json):
            with open(self.rules_json) as data:
                rules = json.load(data)

            # if rules exists add one by one to rules list
            if len(rules) is not 0:
                for rule_from_json in list(rules.keys()):
                    # rule list widget to be added to list
                    rule = QtWidgets.QListWidgetItem(self.rulesList)
                    # rule custom look from rule.py file
                    rule_widget = Rule()
                    # fill rule list widget with neded data
                    rule.setWhatsThis(str(rules[rule_from_json]))
                    rule.setSizeHint(QSize(self.rulesList.sizeHint().width(), 35))
                    rule_widget.setWhatsThis(str(rules[rule_from_json]))
                    rule_widget.ruleTitleLabel.setText(rule_from_json)
                    # add actions to rule buttons
                    rule_widget.deleteButton.clicked.connect(
                        self.refresh_rules_list)
                    rule_widget.infoButton.clicked.connect(self.rule_info)
                    rule_widget.editButton.clicked.connect(self.rule_edit)
                    # add rule to rule list
                    self.rulesList.addItem(rule)
                    self.rulesList.setItemWidget(rule, rule_widget)

                self.checkButton.setEnabled(False)

    def rule_info(self):
        '''Action when info button on rule is clicked'''
        # get data about clicked rule
        with open(self.tmp_json) as data:
            tmp = json.load(data)
        with open(self.rules_json) as data:
            rules = json.load(data)
        rule_data = rules[tmp['rule_info']]
        # organize rule data for output
        # info about first layer and its filter (optional)
        first_rule = rule_data['layer1']
        if rule_data['field_filter1'] != 'no_filter':
            first_rule += " ('%s' %s '%s')" % (
                rule_data['field1'], self.lang(rule_data['field_filter1']),
                self.lang(rule_data['field_filter_value1'])
            )
        # info about topology check
        check = self.lang(rule_data['check'])
        # info about second layer (optional) and its filter (optional)
        if rule_data['layer2'] != self.lang('no_layer'):
            second_rule = rule_data['layer2']
            if rule_data['field_filter2'] != 'no_filter':
                second_rule += " ('%s' %s '%s')" % (
                    rule_data['field2'], self.lang(rule_data['field_filter2']),
                    rule_data['field_filter_value2']
                )
        else:
            second_rule = ''

        message = [first_rule, check, second_rule]
        self.show_message(message)

    def rule_edit(self):
        '''Action when edit button on rule is clicked'''
        # get data about clicked rule
        with open(self.tmp_json) as data:
            tmp = json.load(data)
        rule_data = tmp['rule_edit']
        # switch to edit (create) tab and fill it with rule data
        self.rulePlayground.setCurrentIndex(1)
        self.titleLineEdit.setText(rule_data['title'])
        self.layerComboBox1.setCurrentText(rule_data['layer1'])
        if rule_data['field_filter1'] != 'no_filter':
            self.fieldComboBox1.setCurrentText(rule_data['field1'])
            self.fieldFilterComboBox1.setCurrentText(self.lang(rule_data['field_filter1']))
            self.valueLineEdit1.setText(rule_data['field_filter_value1'])
            self.add_field_filter(1)
        self.checkComboBox.setCurrentText(self.lang(rule_data['check']))
        if rule_data['layer2'] != 'no_layer':
            self.layerComboBox2.setCurrentText(rule_data['layer2'])
            if rule_data['field_filter2'] and rule_data['field_filter2'] != 'no_filter':
                self.fieldComboBox2.setCurrentText(rule_data['field2'])
                self.fieldFilterComboBox2.setCurrentText(self.lang(rule_data['field_filter2']))
                self.valueLineEdit2.setText(rule_data['field_filter_value2'])
                self.add_field_filter(2)
        # change text from 'Create rule' to 'Edit rule'
        self.createRuleButton.setText(self.lang('edit_rule'))

    def click_on_rule(self):
        '''Activate check button'''
        self.checkButton.setEnabled(True)

    def check_rule(self):
        '''Check selected rule'''
        try:
            self.resultList.clear()
            # get data about rule
            rule = self.rulesList.currentItem().whatsThis()
            json_acceptable_string = rule.replace("'", "\"")
            rule_data = json.loads(json_acceptable_string)
            field_filter_function = eval(rule_data['field_filter1'])
            # get arguments for field filter
            args = [
                rule_data['layer1'],
                rule_data['field1'],
                rule_data['field_filter_value1'],
                rule_data['is_numeric1']
            ]
            kwargs = {}
            # get filtered features
            features = field_filter_function(*args, **kwargs)

            check_function = eval(rule_data['check'])
            # created rule is for one layer
            if FUNCTIONS[rule_data['check']]['geom2_type'] == '':
                args = [features]
                results = check_function(*args, **kwargs)
                self.print_results(results, rule_data['layer1'], rule_data['layer1'])

            # created rule is for two layer
            else:
                # get field filter function name from FILTER dictionay
                field_filter_function = eval(rule_data['field_filter2'])
                # get arguments for field filter
                args = [
                    rule_data['layer2'],
                    rule_data['field2'],
                    rule_data['field_filter_value2'],
                    rule_data['is_numeric2']
                ]
                kwargs = {}
                features2 = field_filter_function(*args, **kwargs)

                args = [features, features2]
                results = check_function(*args, **kwargs)
                if results:
                    self.print_results(results, rule_data['layer1'],
                        rule_data['layer2'])
                else:
                    self.show_message([self.lang('all_good')])

        except Exception as e:
            print('Something happened at check_rule [%s]' % (e))

    def print_results(self, results, layer1, layer2):
        '''show results from check_rule'''
        for result in results:

            error = QtWidgets.QListWidgetItem(self.resultList)
            error_widget = Result()

            error.setSizeHint(QSize(self.resultList.sizeHint().width(), 35))

            feature_text1 = layer1 + '\n' + str(result[0])
            self.adjust_text(error_widget.featureID1, feature_text1)

            self.adjust_text(error_widget.resultLabel, self.lang(result[1]))

            if result[2]:
                feature_text2 = layer2 + '\n' + str(result[2])
            else:
                feature_text2 = layer2
            self.adjust_text(error_widget.featureID2, feature_text2)

            self.resultList.addItem(error)
            self.resultList.setItemWidget(error, error_widget)

    def adjust_text(self, widget, text):
        '''show results from check_rule'''

        widget.setText(text)
        widget_width = widget.rect().width()
        font_size = widget.font().pointSizeF()
        font = QtGui.QFont()
        while font_size > 5:
            textRect = widget.fontMetrics().boundingRect(widget.text())
            if textRect.width() <= widget_width:
                break
            font_size -= 1
            font.setPointSize(font_size)
            widget.setFont(font)

    # --- Create rule tab -----------------------------------------------------

    def refresh_layer_list(self, nr, geom=None):
        '''
        Refresh layer list with layers from current project file.
        '''
        layerComboBox = eval('self.layerComboBox' + str(nr))
        layerComboBox.clear()
        layerComboBox.addItem(self.lang('no_layer'))
        check_geom = geom if geom else [0, 1, 2]

        for layer in QgsProject.instance().mapLayers().values():
            if layer.type() == QgsMapLayer.VectorLayer:

                has_features = layer.featureCount() != 0
                has_correct_geom = layer.geometryType() in check_geom

                if has_correct_geom and has_features:
                    if nr == 2 and layer.name() == self.layerComboBox1.currentText():
                        continue
                    layerComboBox.addItem(layer.name(),
                        userData=layer.geometryType())
        # clear field list
        self.refresh_field_list(nr)

    def refresh_field_list(self, nr):
        '''
        Refresh field list with fields of selected layer
        '''
        # to check selected layer
        layerComboBox = eval('self.layerComboBox' + str(nr))
        layerStatus = eval('self.layerStatus' + str(nr))
        # to update field list
        fieldComboBox = eval('self.fieldComboBox' + str(nr))
        # to enable/disable field filter
        fieldFilterGroupBox = eval('self.fieldFilterGroupBox' + str(nr))
        addFilterButton = eval('self.addFilterButton' + str(nr))

        fieldComboBox.clear()
        fieldComboBox.addItem('')

        current_layer = layerComboBox.currentText()
        # if layer selected
        if current_layer != self.lang('no_layer'):
            # set status color to green
            self.set_status(layerStatus, 'ok')
            fieldComboBox.setEnabled(True)
            layers = QgsProject.instance().mapLayersByName(current_layer)
            if len(layers) == 1:
                layer = layers[0]
                for field in layer.fields():
                    userData = {
                        'field': field.name(),
                        'type_name': field.typeName(),
                        'is_numeric': field.isNumeric(),
                        'is_bool': field.type()==1,
                    }
                    fieldComboBox.addItem(field.name(),userData=userData)
                # enable field filter stuff
                fieldFilterGroupBox.setEnabled(True)
                addFilterButton.setEnabled(True)
            # if more than one layer have selected layer name
            elif len(layers) > 1:
                self.show_message([self.lang('layer_name_not_unique')])
        # if layer not selected
        else:
            # set status color to white
            self.set_status(layerStatus, 'default')
            # disable field filter stuff
            fieldFilterGroupBox.setEnabled(False)
            addFilterButton.setEnabled(False)

        self.refresh_field_filter_list(nr)

    def refresh_field_filter_list(self, nr):
        '''
        Refresh field filter list
        '''
        # to check selected field
        fieldComboBox = eval('self.fieldComboBox' + str(nr))
        # to update filter list
        fieldTypeLabel = eval('self.fieldTypeLabel' + str(nr))
        fieldFilterComboBox = eval('self.fieldFilterComboBox' + str(nr))
        valueLineEdit = eval('self.valueLineEdit' + str(nr))
        fieldFilterStatus = eval('self.fieldFilterStatus' + str(nr))

        fieldFilterComboBox.clear()
        fieldFilterComboBox.addItem('')
        valueLineEdit.setText('')
        valueLineEdit.setPlaceholderText('')

        self.set_status(fieldFilterStatus, 'default')

        field = fieldComboBox.currentText()
        if field != '':
            field_data = fieldComboBox.currentData()
            # show data type of chosen field
            fieldTypeLabel.setText(field_data['type_name'])
            # fill filter list according to chosen field data type
            if field_data['is_bool']:
                fieldFilterComboBox.addItem(self.lang('equals'))
                valueLineEdit.setPlaceholderText('True/False')
            else:
                for filter in FILTERS:
                    fieldFilterComboBox.addItem(self.lang(filter),
                        userData=field_data['is_numeric'])
            self.set_field_filter_enabled(nr, True)
        else:
            self.set_field_filter_enabled(nr, False)

    def set_field_filter_enabled(self, nr, selected):
        '''
        Refresh field filter
        '''
        eval('self.fieldTypeLabel' + str(nr)).setVisible(selected)
        eval('self.fieldFilterComboBox' + str(nr)).setEnabled(selected)
        eval('self.valueLabel' + str(nr)).setEnabled(selected)
        eval('self.valueLineEdit' + str(nr)).setEnabled(selected)
        eval('self.addFilterButton' + str(nr)).setEnabled(selected)
        eval('self.addFilterButton' + str(nr)).setText(self.lang('add_field_filter'))

    def add_field_filter(self, nr):
        '''
        Add field filter to selected layer
        '''
        fieldFilterGroupBox = eval('self.fieldFilterGroupBox' + str(nr))
        fieldComboBox = eval('self.fieldComboBox' + str(nr))
        fieldFilterComboBox = eval('self.fieldFilterComboBox' + str(nr))
        valueLineEdit = eval('self.valueLineEdit' + str(nr))
        addFilterButton = eval('self.addFilterButton' + str(nr))
        fieldFilterStatus = eval('self.fieldFilterStatus' + str(nr))
                                                                                #TODO check if numeric value provided for numeric atribute
        if addFilterButton.text() == self.lang('add_field_filter'):

            field_data = fieldComboBox.currentData()
            value = valueLineEdit.text()

            if fieldComboBox.currentText() == '':
                self.show_message([self.lang('select_field'),])

            elif fieldFilterComboBox.currentText() == '':
                self.show_message([self.lang('select_field_filter'),])

            elif value == '':
                self.show_message([self.lang('provide_value'),])

            elif self.is_correct_value_type(field_data, value):
                fieldFilterGroupBox.setEnabled(False)
                self.set_combo_box_img(nr, False)
                addFilterButton.setText(self.lang('edit_field_filter'))
                self.set_status(fieldFilterStatus, 'ok')
        else:
            fieldFilterGroupBox.setEnabled(True)
            self.set_combo_box_img(nr, True)
            addFilterButton.setText(self.lang('add_field_filter'))
            self.set_status(fieldFilterStatus, 'default')

    def is_correct_value_type(self, filter_data, value):
        '''
        Ckeck value data type regarding data type of chosen field
        '''
        if filter_data['is_bool']:
            if value not in ['True', 'False']:
                self.show_message([self.lang('value_for_field'),
                    filter_data['field'], self.lang('must_be_true_false'),])
                return False
        if filter_data['is_numeric']:
            if self.is_not_number(value):
                self.show_message([self.lang('value_for_field'),
                    filter_data['field'], self.lang('must_be_numeric'),])
                return False
        self.show_message([])
        return True

    def is_not_number(self, value):
        '''Ckeck if value is numeric'''
        try:
            float(value)
            return False
        except ValueError:
            return True

    def set_status(self, button, status):
        '''Set color on left side to show rule making progress'''
        color = 'white'
        if status == 'ok':
            color = 'rgb(138, 226, 52)'
        style = 'color:' + color + ';background-color:' + color + ';border: 0px'
        button.setStyleSheet(style)

    def refresh_check_list(self):
        '''
        Update check list with created functions
        '''
        self.checkComboBox.clear()
        self.checkComboBox.addItem(self.lang('not_selected'))
        current_layer_name = self.layerComboBox1.currentText()
        current_layer_geom = self.layerComboBox1.currentData()
        # if layer selected
        if current_layer_name != self.lang('no_layer'):
            # add functions depending on geometry
            for function, data in FUNCTIONS.items():
                if current_layer_geom in data['geom1_type']:
                    self.checkComboBox.addItem(self.lang(function))
            self.checkLabel.setEnabled(True)
            self.checkComboBox.setEnabled(True)
        else:
            self.checkLabel.setEnabled(False)
            self.checkComboBox.setEnabled(False)
        self.refresh_layer2_list()

    def refresh_layer2_list(self):
        '''
        Refresh second layer list
        '''
        # get selected check function label
        current_check = self.checkComboBox.currentText()
        if current_check and current_check != self.lang('not_selected'):
            self.set_status(self.checkStatus, 'ok')
            # get function name
            check_function_name = self.lang_key(current_check)
            # check how many layers needed in check function
            if FUNCTIONS[check_function_name]['geom2_type']:
                # get geom from check
                geom = FUNCTIONS[check_function_name]['geom2_type']
                self.layerLabel2.setEnabled(True)
                self.layerComboBox2.setEnabled(True)
                self.refresh_layer_list(2, geom)
            else:
                self.layerLabel2.setEnabled(False)
                self.layerComboBox2.setEnabled(False)
                self.refresh_layer_list(2)
        else:
            self.set_status(self.checkStatus, 'default')
            self.layerComboBox2.clear()
            self.layerLabel2.setEnabled(False)
            self.layerComboBox2.setEnabled(False)
            self.refresh_layer_list(2)

    def add_rule_check(self):
        '''Update check progres color'''

        if self.checkComboBox.currentText() != self.lang('not_selected'):
            self.set_status(self.checkStatus, 'ok')
            self.layerComboBox2.setEnabled(True)
            self.fieldFilterGroupBox2.setEnabled(True)
        else:
            self.set_status(self.checkStatus, 'default')
            self.layerComboBox2.setEnabled(False)
            self.fieldFilterGroupBox2.setEnabled(False)

    def create_rule(self, rule):
        '''Create or edit and save rule in rules.json file'''

        try:
            title = self.titleLineEdit.text()
            button = self.createRuleButton.text()
            check_function_name = self.lang_key(self.checkComboBox.currentText())
            with open(self.rules_json) as data:
                rules = json.load(data)
            with open(self.tmp_json) as data:
                tmp = json.load(data)

            if not title:
                self.show_message([self.lang('no_title')])
            elif self.layerComboBox1.currentText() == self.lang('no_layer'):
                self.show_message([self.lang('no_layer_selected')])
            elif self.checkComboBox.currentText() == self.lang('not_selected'):
                self.show_message([self.lang('no_check_selected')])
            elif (button == self.lang('create_rule') and title in rules):
                self.show_message([self.lang('title_exists')])
            elif (FUNCTIONS[check_function_name]['geom2_type'] and
                        self.layerComboBox2.currentText() == self.lang('no_layer')):
                self.show_message([self.lang('no_second_layer')])
            else:
                if self.addFilterButton1.text() == self.lang('add_field_filter'):
                    is_numeric1 = ''
                    field_filter1 = 'no_filter'
                else:
                    is_numeric1 = '1' if self.fieldFilterComboBox1.currentData() else ''
                    field_filter1 = self.lang_key(self.fieldFilterComboBox1.currentText())
                if self.addFilterButton2.text() == self.lang('add_field_filter'):
                    is_numeric2 = ''
                    field_filter2 = 'no_filter'
                else:
                    is_numeric2 = '1' if self.fieldFilterComboBox1.currentData() else ''
                    field_filter2 = self.lang_key(self.fieldFilterComboBox2.currentText())
                new_rule = {
                    'layer1': self.layerComboBox1.currentText(),
                    'field1': self.fieldComboBox1.currentText(),
                    'is_numeric1': is_numeric1,
                    'field_filter1': field_filter1,
                    'field_filter_value1': self.valueLineEdit1.text(),
                    'check': self.lang_key(self.checkComboBox.currentText()),
                    'layer2': self.layerComboBox2.currentText(),
                    'field2': self.fieldComboBox2.currentText(),
                    'is_numeric2': is_numeric2,
                    'field_filter2': field_filter2,
                    'field_filter_value2': self.valueLineEdit2.text()
                }
                edit_mode = button == self.lang('edit_rule')
                title_changed = title != tmp['rule_edit']['title']
                title_taken = title in rules
                if edit_mode and title_changed :
                    if title_taken:
                        self.show_message([self.lang('title_exists')])
                        return
                    else:
                        old_title = str(tmp['rule_edit']['title'])
                        rules.pop(old_title)
                rules[title] = new_rule
                with open(self.rules_json, 'w') as data:
                    json.dump(rules, data)

                self.rulePlayground.setCurrentIndex(0)
                self.titleLineEdit.setText('')
                self.show_message('')

        except Exception as e:
            print('Something happened at create_rule [%s]' % (e))

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
