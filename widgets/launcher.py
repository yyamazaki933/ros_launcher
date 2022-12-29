#!/usr/bin/env python3

import os
from PyQt5 import uic, QtWidgets

class LauncherWindow(QtWidgets.QWidget):

    def __init__(self, ui_file, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi(ui_file, self)

        self.home_dir = os.getenv('HOME')
        self.ros_ver = 2
        self.ros_distro = 'humble'
        self.ros_path = '/opt/ros/' + self.ros_distro + '/setup.bash'

        self.pb_launch.clicked.connect(self.pb_launch_cb)
