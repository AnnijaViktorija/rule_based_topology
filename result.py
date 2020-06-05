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
    os.path.dirname(__file__), 'result.ui'))


class Result(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        '''Constructor.'''

        super(Result, self).__init__(parent)
        self.setupUi(self)

        self.featureID1.clicked.connect(lambda: self.show_feature(1))
        self.featureID2.clicked.connect(lambda: self.show_feature(2))

    def show_feature(self, nr):
        '''Show selected feature on map'''
        try:
            featureID = eval('self.featureID' + str(nr))
            feature_data = featureID.text().split('\n')
            layer_name = feature_data[0]
            layer = QgsProject.instance().mapLayersByName(layer_name)[0]
            iface.setActiveLayer(layer)
            layer.removeSelection()
            # if result contains features id select it
            if len(feature_data)==2:
                layer.select(int(feature_data[1]))
                box = layer.boundingBoxOfSelected()
                iface.mapCanvas().setExtent(box)
                iface.mapCanvas().refresh()
        except Exception as e:
            print('Something happened at delete_rule [%s]' % (e))
