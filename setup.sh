#!/bin/bash

SCRIPT_DIR=$(cd $(dirname $0);pwd)

sudo cp $SCRIPT_DIR/img/ros_launcher.png /usr/share/pixmaps/
cat $SCRIPT_DIR/desktop/ros_launcher.desktop | sed -e "s?PATH?$SCRIPT_DIR?" > ~/.local/share/applications/ros_launcher.desktop

if ! grep -q "ros_launcher.desktop" $HOME/.config/mimeapps.list; then
    ROW="application/xml=ros_launcher.desktop"
    sed -i -e '/^$/i'$ROW';' $HOME/.config/mimeapps.list
    sed -i -e '$a'$ROW $HOME/.config/mimeapps.list
fi