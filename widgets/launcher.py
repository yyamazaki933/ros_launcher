#!/usr/bin/env python3

import os
import yaml
import subprocess
import xml.etree.ElementTree as et

from PyQt5 import uic, QtWidgets
from PyQt5.QtWidgets import QFileDialog, QMessageBox


class LauncherWindow(QtWidgets.QWidget):

    def __init__(self, ui_file, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi(ui_file, self)

        self.home_dir = os.getenv('HOME')
        self.ui_file = ui_file
        self.arg_items = []
        self.conf_file = ''
        self.conf = {}
        self.conf['launch_file'] = ''
        self.conf['source_file'] = ''

        self.pb_xml.clicked.connect(self.pb_xml_cb)
        self.pb_src.clicked.connect(self.pb_src_cb)
        self.pb_launch.clicked.connect(self.pb_launch_cb)

    def saveConf(self, conf_file, conf):
        with open(conf_file, 'w') as file:
            yaml.safe_dump(conf, file, sort_keys=False)

    def loadConf(self, conf_file, default_conf):
        try:
            with open(conf_file, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            self.saveConf(conf_file, default_conf)
            return default_conf

    def pb_xml_cb(self):
        xml = QFileDialog.getOpenFileName(
            self, 'Choose ROS2 Launch File', self.home_dir, 'Launch XML File (*.launch.xml)')[0]
        self.set_launch_file(xml)

    def pb_src_cb(self):
        src = QFileDialog.getOpenFileName(
            self, 'Choose Source File', self.home_dir, 'Bash File (*.bash)')[0]
        self.set_src_file(src)

    def set_launch_file(self, file):
        if file == '':
            return

        self.le_xml.setText(file)
        self.conf['launch_file'] = file
        self.parseFile(file)

        self.conf_file = file.replace('.xml', '.override.conf')
        self.conf = self.loadConf(self.conf_file, self.conf)
        self.set_src_file(self.conf['source_file'])

        self.createParamList()

    def set_src_file(self, file):
        if file == '':
            return

        self.le_src.setText(file)
        self.conf['source_file'] = file

    def pb_launch_cb(self):
        xml = self.le_xml.text()
        src = self.le_src.text()

        if xml == '':
            QMessageBox.critical(self, 'Error', 'Launch File is empty!')
            return

        if src == '':
            QMessageBox.critical(self, 'Error', 'Source File is empty!')
            return

        cmd = 'source ' + src
        cmd += ' && '
        cmd += 'ros2 launch ' + xml

        for arg_item in self.arg_items:
            if arg_item.default != arg_item.currentVal():
                self.conf[arg_item.arg_name]['override'] = arg_item.currentVal()
                cmd += ' ' + arg_item.arg_name + ':=' + arg_item.currentVal()

        print('[INFO] execCmdAsync():', cmd)
        self.saveConf(self.conf_file, self.conf)
        subprocess.Popen(cmd, shell=True, executable='/bin/bash', text=True)

    def parseFile(self, file):
        tree = et.parse(file)
        root = tree.getroot()
        i = 0
        for child in root:
            if child.tag == 'arg':
                arg_name = child.attrib['name']
                self.conf[arg_name] = child.attrib
                i += 1

    def createParamList(self):
        for key, val in self.conf.items():
            if key == 'launch_file' or key == 'source_file':
                continue

            arg_item = ArgItem(self.ui_file.replace(
                'launcher.ui', 'argitem.ui'), val)
            self.arg_items.append(arg_item)
            self.arglist.addWidget(arg_item)


class ArgItem(QtWidgets.QWidget):

    def __init__(self, ui_file, val, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.arg_name = val['name']
        self.default = ''
        self.arg_type = ''

        try:
            self.default = val['default']
        except:
            self.default = ''

        try:
            override = val['override']
        except:
            override = self.default

        try:
            arg_description = val['description']
        except:
            arg_description = ''

        if self.default == 'true' or self.default == 'false':
            self.arg_type = 'bool'
            uic.loadUi(ui_file.replace('argitem.ui', 'argitem_bool.ui'), self)
            self.name.setText(self.arg_name)
            self.value.setCurrentText(override)
            self.value.currentTextChanged.connect(self.valueChanged)
            self.valueChanged()
        else:
            self.arg_type = 'str'
            uic.loadUi(ui_file.replace('argitem.ui', 'argitem_str.ui'), self)
            self.name.setText(self.arg_name)
            self.value.setText(override)
            self.value.setPlaceholderText(arg_description)
            self.value.textChanged.connect(self.valueChanged)
            self.valueChanged()

    def currentVal(self):
        if self.arg_type == 'str':
            return self.value.text()
        elif self.arg_type == 'bool':
            return self.value.currentText()

    def valueChanged(self):
        if self.arg_type == 'str':
            val = self.value.text()
        elif self.arg_type == 'bool':
            val = self.value.currentText()

        if val == '':
            self.setStyleSheet("QLineEdit,QComboBox { color: gray; }")
        elif val == self.default:
            self.setStyleSheet("QLineEdit,QComboBox { color: white; }")
        else:
            self.setStyleSheet("QLineEdit,QComboBox { color: lime; }")
