#!/usr/bin/env python3

import os
import sys
import signal
import yaml
import subprocess
import xml.etree.ElementTree as et

from PyQt5 import uic, QtWidgets, QtGui
from PyQt5.QtWidgets import QFileDialog, QMessageBox

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

class LauncherWindow(QtWidgets.QWidget):

    def __init__(self, path, launch_file=None):
        super().__init__()
        uic.loadUi(SCRIPT_DIR + "/ui/launcher.ui", self)

        self.path = path

        self.home_dir = os.getenv('HOME')
        self.conf = {}
        self.arg_items = []
        self.proc = None
        self.conf_file = None
        self.launch_file = None

        self.pb_file.clicked.connect(self.__pb_file_call)
        self.pb_launch.clicked.connect(self.__pb_launch_call)

        self.pb_launch.setText("Start")
        self.le_file.setStyleSheet("QLineEdit { color: gray; }")

        if launch_file != None:
            self.loadLaunch(launch_file)        
            
    def __pb_file_call(self):
        file = QFileDialog.getOpenFileName(
            self, 'Choose Launch File', self.home_dir, 'Launch XML (*.launch.xml)')[0]
        if file == None:
            return
        self.loadLaunch(file)

    def __pb_launch_call(self):
        if self.launch_file == None:
            return
        
        if self.proc:
            print('[INFO] terminateProc()')
            os.killpg(self.proc.pid, signal.SIGINT)
            self.proc = None
            self.pb_launch.setText("Start")

        else:
            cmd = 'source ' + self.path
            cmd += ' && '
            cmd += 'exec ros2 launch ' + self.launch_file

            self.conf['path'] = self.path
            for arg_item in self.arg_items:
                if arg_item.default != arg_item.currentVal():
                    self.conf["args"][arg_item.arg_name]['override'] = arg_item.currentVal()
                    cmd += ' ' + arg_item.arg_name + ':=' + arg_item.currentVal()
                elif self.conf["args"][arg_item.arg_name].get('override'):
                    self.conf["args"][arg_item.arg_name].pop('override')

            print('[INFO] startProc():', cmd)
            self.saveConf()
            self.proc = subprocess.Popen(cmd, shell=True, executable='/bin/bash', text=True, preexec_fn=os.setsid)
            self.pb_launch.setText("Stop")

    def saveConf(self):
        print('[INFO] saveConf():', self.conf_file)
        with open(self.conf_file, 'w') as file:
            yaml.safe_dump(self.conf, file, sort_keys=False)

    def loadConf(self):
        try:
            with open(self.conf_file, 'r') as file:
                self.conf = yaml.safe_load(file)
        except FileNotFoundError:
            print('[INFO] loadConf(): file not found. create file.')
            self.conf = {"launch_file": self.launch_file, "path": self.path, "args": {}}
            self.saveConf()

    def loadLaunch(self, file):
        if file == '':
            return
        
        self.launch_file = file
        self.conf_file = SCRIPT_DIR + "/config/" + os.path.basename(file) + ".yaml"
        
        self.loadConf()

        self.le_file.setText(os.path.basename(file))
        self.le_file.setStyleSheet("QLineEdit { color: white; }")
        self.parseFile(file)
        self.createParamList()

    def parseFile(self, file):
        tree = et.parse(file)
        root = tree.getroot()
        i = 0
        for child in root:
            if child.tag == 'arg':
                arg_name = child.attrib['name']
                if self.conf['args'].get(arg_name) == None:
                    self.conf['args'][arg_name] = child.attrib
                i += 1

    def createParamList(self):
        for item in self.arg_items:
            item.deleteLater()
        self.arg_items.clear()

        for key, val in self.conf['args'].items():
            arg_item = ArgItem(val)
            self.arg_items.append(arg_item)
            self.arglist.addWidget(arg_item)
        self.arglist.addStretch()


class ArgItem(QtWidgets.QWidget):

    def __init__(self, val):
        super().__init__()

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
            uic.loadUi(SCRIPT_DIR + '/ui/argitem_bool.ui', self)
            self.name.setText(self.arg_name)
            self.value.setCurrentText(override)
            self.value.currentTextChanged.connect(self.valueChanged)
            self.valueChanged()
        else:
            self.arg_type = 'str'
            uic.loadUi(SCRIPT_DIR + '/ui/argitem_str.ui', self)
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

if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)
    with open(SCRIPT_DIR + '/ui/stylesheet.css', 'r') as f:
        style = f.read()
        app.setStyleSheet(style)

    path = "/opt/ros/humble/setup.bash"
    ui_main = LauncherWindow(path)
    ui_main.setWindowIcon(QtGui.QIcon(SCRIPT_DIR + '/img/ros_launcher.png'))
    ui_main.show()

    sys.exit(app.exec())
