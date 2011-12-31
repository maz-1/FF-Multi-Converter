#!/usr/bin/python
# -*- coding: utf-8 -*-
# Program: FF Multi Converter
# Purpose: GUI application to convert multiple file formats
#
# Copyright (C) 2011 Ilias Stamatis <stamatis.iliass@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

__version__ = "1.3.0 planning"

import platform
py_version = platform.python_version()

if not (py_version >= '2.6' and py_version < '3'):
    exit('Error: You need python 2.6 or python2.7 to run this program.')
    
try:
    import PyQt4
except ImportError:
    exit('Error: You need PyQt4 to run this program.')    

try:
    from PythonMagick import Image
except ImportError:
    pass
    # User will be informed about this later

from PyQt4.QtCore import (QSettings, QString, QRegExp, QTimer, QBasicTimer, 
                  QLocale, QTranslator, QSize, QT_VERSION_STR,PYQT_VERSION_STR)
from PyQt4.QtGui import (QApplication, QMainWindow, QDialog, QWidget, QFrame,
                  QGridLayout, QVBoxLayout, QHBoxLayout, QSizePolicy, QLabel, 
                  QSpacerItem, QLineEdit, QToolButton, QComboBox, QCheckBox, 
                  QRadioButton, QPushButton, QProgressBar, QTabWidget, QIcon, 
                  QAction, QKeySequence, QFileDialog, QMessageBox, 
                  QRegExpValidator)

from PyQt4.QtCore import *     
from PyQt4.QtGui import *
                  
import sys
import os
import signal
import subprocess
import shlex
import shutil
import re
import time

import pyqttools
import preferences_dlg
import path_generator
import qrc_resources

class Tab(QWidget):
    def __init__(self, parent, formats):
        super(Tab, self).__init__(parent)
        self.parent = parent
        self.formats = formats        
        
        label1 = QLabel(self.tr('Convert from:'))
        label2 = QLabel(self.tr('Convert to:'))
        self.fromComboBox = QComboBox()
        self.toComboBox = QComboBox()        
        grid = pyqttools.add_to_grid(QGridLayout(), 
                        [label1, self.fromComboBox], [label2, self.toComboBox])        
        self.layout = pyqttools.add_to_layout(QVBoxLayout(), grid)
        self.setLayout(self.layout)       
        
        self.update_comboboxes() 

    def update_comboboxes(self):                 
        self.fromComboBox.addItems(self.formats)
        self.toComboBox.addItems(self.formats)  
            
    def resize_parent(self):
        """Resizes MainWindow"""
        if self.frame.isVisible():
            self.parent.resize(685, 453)
        else:                                
            self.parent.setMinimumSize(685, 378)
            self.parent.resize(685, 378)   
                
    def create_more_layout(self, labels, widgets, *extralayout):
        """Creates hidden widget"""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        self.moreButton = QPushButton(self.tr('More'))
        moreSizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.moreButton.setSizePolicy(moreSizePolicy)
        self.moreButton.setCheckable(True)
        hlayout1 = pyqttools.add_to_layout(QHBoxLayout(), line,self.moreButton)
        
        hlayout2 = QHBoxLayout()
        for a, b in zip(labels, widgets):
            text = a.text()
            a.setText('<html><p align="center">{0}</p></html>'.format(text))            
            layout = pyqttools.add_to_layout(QVBoxLayout(), a, b)
            hlayout2.addLayout(layout)
        
        if extralayout:
            for item in extralayout:
                hlayout2 = pyqttools.add_to_layout(hlayout2, item)
        
        self.frame = QFrame()
        self.frame.setLayout(hlayout2)
        self.frame.hide()        
        pyqttools.add_to_layout(self.layout, hlayout1, self.frame)
        
        self.moreButton.toggled.connect(self.frame.setVisible)
        self.moreButton.toggled.connect(self.resize_parent)
            
    def create_LineEdit(self, maxsize, validator, maxlength):
        """Creates a lineEdit
        
        Keyword arguments:
        maxsize -- maximum size
        validator -- a regular expression to be added as validator
        maxlength - maximum length
        """        
        lineEdit = QLineEdit()
        if maxsize is not None:
            lineEdit.setMaximumSize(QSize(maxsize[0], maxsize[1]))
        if validator is not None:
            lineEdit.setValidator(validator)
        if maxlength is not None:
            lineEdit.setMaxLength(maxlength)
        return lineEdit     
        
    def clear(self):
        pass

            
class AudioTab(Tab):
    def __init__(self, parent, formats):
        super(AudioTab, self).__init__(parent, formats)        
        nochange = self.tr('No Change')
        self.frequency_values = [nochange, '22050', '44100', '48000']
        self.bitrate_values = [nochange, '32', '96', '112', '128', '160', 
                                                           '192', '256', '320']        
                
        freqLabel = QLabel(self.tr('Frequency (Hz):'))
        chanLabel = QLabel(self.tr('Channels:'))
        bitrateLabel = QLabel(self.tr('Bitrate (kbps):'))
        
        self.freqComboBox = QComboBox()
        self.freqComboBox.addItems(self.frequency_values)                
        self.chan1RadioButton = QRadioButton('1')  
        self.chan1RadioButton.setMaximumSize(QSize(51, 16777215))
        self.chan2RadioButton = QRadioButton('2')
        self.chan2RadioButton.setMaximumSize(QSize(51, 16777215))
        self.group = QButtonGroup()
        self.group.addButton(self.chan1RadioButton)
        self.group.addButton(self.chan2RadioButton)    
        self.group.setExclusive(False)        
        spcr1 = QSpacerItem(40, 20, QSizePolicy.Preferred, QSizePolicy.Minimum)
        spcr2 = QSpacerItem(40, 20, QSizePolicy.Preferred, QSizePolicy.Minimum)
        chanlayout = pyqttools.add_to_layout(QHBoxLayout(), spcr1, 
                           self.chan1RadioButton, self.chan2RadioButton, spcr2)
        self.bitrateComboBox = QComboBox()
        self.bitrateComboBox.addItems(self.bitrate_values)
        
        labels = [freqLabel, chanLabel, bitrateLabel]
        widgets = [self.freqComboBox, chanlayout, self.bitrateComboBox]
        
        self.create_more_layout(labels, widgets)
        
    def clear(self):
        """Clear values."""
        self.freqComboBox.setCurrentIndex(0)
        self.bitrateComboBox.setCurrentIndex(0)
        self.chan1RadioButton.setChecked(False)
        self.chan2RadioButton.setChecked(False)


class VideoTab(Tab):
    def __init__(self, parent, formats):
        super(VideoTab, self).__init__(parent, formats)                
        pattern = QRegExp(r"\d*")
        validator = QRegExpValidator(pattern, self)
        
        sizeLabel = QLabel(self.tr('Video Size:'))
        aspectLabel = QLabel(self.tr('Aspect:'))
        frameLabel = QLabel(self.tr('Frame Rate:'))
        bitrateLabel = QLabel(self.tr('Bitrate (kbps):'))
        
        self.widthLineEdit = self.create_LineEdit((50, 16777215), validator, 4)
        self.heightLineEdit = self.create_LineEdit((50, 16777215), validator,4)
        label = QLabel('x')
        layout1 = pyqttools.add_to_layout(QHBoxLayout(), self.widthLineEdit, 
                                                    label, self.heightLineEdit)
        self.aspect1LineEdit = self.create_LineEdit((35, 16777215),validator,2)                                                            
        self.aspect2LineEdit = self.create_LineEdit((35, 16777215),validator,2)
        label = QLabel(':')
        layout2 = pyqttools.add_to_layout(QHBoxLayout(), self.aspect1LineEdit, 
                                                   label, self.aspect2LineEdit)   
        self.frameLineEdit = self.create_LineEdit(None, validator, 4)
        self.bitrateLineEdit = self.create_LineEdit(None, validator, 6)
        
        labels = [sizeLabel, aspectLabel, frameLabel, bitrateLabel]
        widgets = [layout1, layout2, self.frameLineEdit, self.bitrateLineEdit]
        
        self.create_more_layout(labels, widgets)   
        
    def update_comboboxes(self):                  
        string = self.tr(' (Audio only)')          
        self.fromComboBox.addItems(self.formats[0])
        self.toComboBox.addItems(self.formats[0]) 
        self.toComboBox.addItems([(i+string) for i in self.formats[1]])
        
    def clear(self):
        """Clear values."""
        lineEdits = [self.widthLineEdit, self.heightLineEdit, 
                    self.aspect1LineEdit, self.aspect2LineEdit, 
                    self.frameLineEdit, self.bitrateLineEdit]
        [i.clear() for i in lineEdits]


class ImageTab(Tab):
    def __init__(self, parent, formats):
        super(ImageTab, self).__init__(parent, formats)                
        pattern = QRegExp(r"\d*")
        validator = QRegExpValidator(pattern, self)        
        
        resizeLabel = QLabel(self.tr('Resize:'))        
        self.widthLineEdit = self.create_LineEdit((50, 16777215), validator, 4)
        self.heightLineEdit = self.create_LineEdit((50, 16777215), validator,4)
        label = QLabel('x')
        layout1 = pyqttools.add_to_layout(QHBoxLayout(), self.widthLineEdit, 
                                                    label, self.heightLineEdit)
        spcr1 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        spcr2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        labels = [resizeLabel]
        widgets = [layout1]
        
        self.create_more_layout(labels, widgets, spcr1, spcr2)
        
    def clear(self):
        """Clear values."""
        lineEdits = [self.widthLineEdit, self.heightLineEdit]
        [i.clear() for i in lineEdits]

class DocumentTab(Tab):
    def __init__(self, parent, formats):
        super(DocumentTab, self).__init__(parent, formats)        
        
        self.fromComboBox.currentIndexChanged.connect(self.refresh_toComboBox)
        self.refresh_toComboBox()
                
    def update_comboboxes(self): 
        # create a sorted list with document_formats extensions because 
        # self.formats is a dict so values are not sorted
        _list = []
        [_list.append(ext) for ext in self.formats]
        _list.sort()
        self.fromComboBox.addItems(_list) 
    
    def refresh_toComboBox(self):
        """Add the appropriate values to toComboBox."""
        self.toComboBox.clear()
        text = str(self.fromComboBox.currentText())
        [self.toComboBox.addItem(i) for i in self.formats[text]]           
                        

class FFMultiConverter(QMainWindow):
    def __init__(self, parent=None):
        super(FFMultiConverter, self).__init__(parent)        
        self.home = os.getenv('HOME')
                
        self.audio_formats = ['aac', 'ac3', 'afc', 'aifc', 'aiff', 'amr', 
                              'asf', 'au', 'avi', 'dvd', 'flac', 'flv', 'm4a', 
                              'm4v', 'mka', 'mmf', 'mov', 'mp2', 'mp3', 'mp4', 
                              'mpeg', 'ogg', 'ra', 'rm', 'spx', 'vob', 'wav', 
                              'webm', 'wma']  
                                      
        self.video_formats = ['asf', 'avi', 'dvd', 'flv', 'm1v', 'm2t', 'm2v', 
                              'mjpg', 'mkv', 'mmf', 'mov', 'mp4', 'mpeg', 
                              'mpg', 'ogg', 'ogv', 'psp', 'rm', 'ts', 'vob', 
                              'webm', 'wma', 'wmv']
                              
        self.vid_to_aud_formats = ['aac', 'ac3', 'aiff', 'au', 'flac', 
                                   'mp2' , 'wav']                                                          
                              
        self.image_formats = ['aai', 'bmp', 'eps', 'fpx', 'gif', 'jbig', 
                              'jpeg', 'p7', 'pdf', 'picon', 'png', 'pnm', 
                              'ppm', 'psd', 'rad', 'sgi', 'sid', 'tga', 'tif', 
                              'webp', 'xpm', 'xwd']   
                              
        self.extra_img_formats = ['dib', 'ps', 'jpg', 'jpe', 'tiff']
                              
        self.document_formats = {'doc' : ['odt', 'pdf'],
                                'html' : ['odt'],
                                'odp' : ['pdf', 'ppt'],
                                'ods' : ['pdf'],
                                'odt' : ['doc', 'html', 'pdf', 'rtf', 'sxw', 
                                         'txt', 'xml'],
                                'ppt' : ['odp'],
                                'rtf' : ['odt'],
                                'sdw' : ['odt'],
                                'sxw' : ['odt'],
                                'txt' : ['odt'],
                                'xls' : ['ods'],
                                'xml' : ['doc', 'odt', 'pdf']}              

        self.fname = ''  # file to convert
        self.output = '' # output destination
        
        select_label = QLabel(self.tr('Select file:'))
        output_label = QLabel(self.tr('Output destination:'))
        self.fromLineEdit = QLineEdit()
        self.fromLineEdit.setReadOnly(True)
        self.toLineEdit = QLineEdit()
        self.toLineEdit.setReadOnly(True)
        self.fromToolButton = QToolButton()
        self.fromToolButton.setText('...')
        self.toToolButton = QToolButton()
        self.toToolButton.setText('...')        
        grid1 = pyqttools.add_to_grid(QGridLayout(), 
                        [select_label, self.fromLineEdit, self.fromToolButton], 
                        [output_label, self.toLineEdit, self.toToolButton])
             
        self.audio_tab = AudioTab(self, self.audio_formats)
        self.video_tab = VideoTab(self, 
                                 [self.video_formats, self.vid_to_aud_formats])
        self.image_tab = ImageTab(self, self.image_formats)
        self.document_tab = DocumentTab(self, self.document_formats)
        
        self.tabs = [self.audio_tab, self.video_tab, self.image_tab, 
                     self.document_tab]
        tab_names = [self.tr('Audio'), self.tr('Video'), self.tr('Image'),
                     self.tr('Documents')]                                                                     
        self.TabWidget  = QTabWidget()
        for i in enumerate(tab_names):
            self.TabWidget.addTab(self.tabs[i[0]], i[1])        
        self.TabWidget.setCurrentIndex(0)
        
        self.folderCheckBox = QCheckBox(self.tr(
                                          'Convert all files\nin this folder'))
        self.recursiveCheckBox = QCheckBox(self.tr(
                                                 'Convert files\nrecursively'))
        self.deleteCheckBox = QCheckBox(self.tr('Delete original'))        
        layout1 = pyqttools.add_to_layout(QHBoxLayout(),self.folderCheckBox, 
                             self.recursiveCheckBox, self.deleteCheckBox, None)
        
        self.typeRadioButton = QRadioButton(self.tr('Same type'))
        self.typeRadioButton.setEnabled(False)
        self.typeRadioButton.setChecked(True)
        self.extRadioButton = QRadioButton(self.tr('Same extension'))
        self.extRadioButton.setEnabled(False)
        layout2 = pyqttools.add_to_layout(QHBoxLayout(), self.typeRadioButton, 
                                                     self.extRadioButton, None)
        layout3 = pyqttools.add_to_layout(QVBoxLayout(), layout1, layout2)        

        self.convertPushButton = QPushButton(self.tr('&Convert'))
        layout4 = pyqttools.add_to_layout(QHBoxLayout(), None, 
                                                        self.convertPushButton)        
        final_layout = pyqttools.add_to_layout(QVBoxLayout(), grid1, 
                                        self.TabWidget, layout3, None, layout4)
        
        self.statusBar = self.statusBar()
        self.dependenciesLabel = QLabel()
        self.statusBar.addPermanentWidget(self.dependenciesLabel, stretch=1)        
        
        Widget = QWidget()
        Widget.setLayout(final_layout)
        self.setCentralWidget(Widget)
                            
        openAction = self.create_action(self.tr('Open'), QKeySequence.Open, 
                                  None, self.tr('Open a file'), self.open_file)
        convertAction = self.create_action(self.tr('Convert'), 'Ctrl+C', None, 
                                        self.tr('Convert files'), self.convert)
        quitAction = self.create_action(self.tr('Quit'), 'Ctrl+Q', None, 
                                                   self.tr('Quit'), self.close)
        clearAction = self.create_action(self.tr('Clear'), None, None, 
                                             self.tr('Clear form'), self.clear)
        preferencesAction = self.create_action(self.tr('Preferences'), 
                  'Alt+Ctrl+P', None, self.tr('Preferences'), self.preferences)
        aboutAction = self.create_action(self.tr('About'), 'Ctrl+?', None, 
                                                  self.tr('About'), self.about)
                                                                               
        fileMenu = self.menuBar().addMenu(self.tr('File'))
        editMenu = self.menuBar().addMenu(self.tr('Edit'))
        helpMenu = self.menuBar().addMenu(self.tr('Help'))
        self.add_actions(fileMenu, [openAction, convertAction, None,quitAction])
        self.add_actions(editMenu, [clearAction, None, preferencesAction])
        self.add_actions(helpMenu, [aboutAction])
        
        self.TabWidget.currentChanged.connect(self.checkboxes_clicked)
        self.TabWidget.currentChanged.connect(self.resize_window)
        self.folderCheckBox.clicked.connect(lambda: 
                                             self.checkboxes_clicked('folder'))
        self.recursiveCheckBox.clicked.connect(lambda: 
                                          self.checkboxes_clicked('recursive'))
        self.fromToolButton.clicked.connect(self.open_file)
        self.toToolButton.clicked.connect(self.open_dir)
        self.convertPushButton.clicked.connect(self.convert)         
        
        self.resize(685, 378)
        self.setWindowTitle('FF Multi Converter')
        
        QTimer.singleShot(0, self.check_for_dependencies)
        QTimer.singleShot(0, self.set_settings)    
    
    def create_action(self, text, shortcut=None, icon=None, tip=None,
                      triggered=None, toggled=None, data=None, 
                      context=Qt.WindowShortcut):
        """Creates a QAction"""
        action = QAction(text, self)
        if triggered is not None:
            action.triggered.connect(triggered)
        if toggled is not None:
            action.toggled.connect(toggled)
            action.setCheckable(True)
        if icon is not None:
            action.setIcon( icon )
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if data is not None:
            action.setData(to_qvariant(data))
        action.setShortcutContext(context)
        return action 
        
    def add_actions(self, target, actions, insert_before=None):
        """Adds actions to menus.
        
        Keyword arguments:
        target -- menu to add action
        actions -- list with actions to add
        """
        previous_action = None
        target_actions = list(target.actions())
        if target_actions:
            previous_action = target_actions[-1]
            if previous_action.isSeparator():
                previous_action = None
        for action in actions:
            if (action is None) and (previous_action is not None):
                if insert_before is None:
                    target.addSeparator()
                else:
                    target.insertSeparator(insert_before)
            elif isinstance(action, QMenu):
                if insert_before is None:
                    target.addMenu(action)
                else:
                    target.insertMenu(insert_before, action)
            elif isinstance(action, QAction):
                if insert_before is None:
                    target.addAction(action)
                else:
                    target.insertAction(insert_before, action)
            previous_action = action                        

    def set_settings(self):
        """Sets program settings"""
        settings = QSettings()
        self.saveto_output = settings.value('saveto_output').toBool()
        self.rebuild_structure = settings.value('rebuild_structure').toBool()
        self.default_output = settings.value('default_output').toString()
        self.prefix = settings.value('prefix').toString()
        self.suffix = settings.value('suffix').toString()
        
        if self.saveto_output:
            if self.toLineEdit.text() == self.tr('Each file to its original '
                                     'folder') or self.toLineEdit.text() == '':
                self.output = self.default_output
                self.toLineEdit.setText(self.output)            
            self.toLineEdit.setEnabled(True)            
        else:
            self.toLineEdit.setEnabled(False)
            self.toLineEdit.setText(self.tr(
                                           'Each file to its original folder'))
            self.output = 'original'
    
    def current_tab(self):
        """Returns current tab."""
        index = self.TabWidget.currentIndex()
        return [i for i in self.tabs if self.tabs.index(i) == index][0]
    
    def resize_window(self):
        """It hides widgets and resizes the window."""
        [i.moreButton.setChecked(False) for i in self.tabs[:3]]
    
    def checkboxes_clicked(self, data=None):
        """Manages the behavior of checkboxes and radiobuttons.
        
        Keywords arguments:
        data -- a string to show from which CheckBox the signal emitted.
        """
        # data default value is None because the method can also be called
        # when TabWidget's tab change.
        if data == 'folder' and self.recursiveCheckBox.isChecked():
            self.recursiveCheckBox.setChecked(False)
        elif data == 'recursive' and self.folderCheckBox.isChecked():
            self.folderCheckBox.setChecked(False)
        
        index = self.TabWidget.currentIndex()
        enable = bool(self.recursiveCheckBox.isChecked() 
                                            or self.folderCheckBox.isChecked())
        self.extRadioButton.setEnabled(enable)  
        if enable and index == 3:
            # set typeRadioButton disabled when type == document files,
            # because it is not possible to convert every file format to any 
            # other file format.            
            self.typeRadioButton.setEnabled(False)
            self.extRadioButton.setChecked(True)
        else:
            self.typeRadioButton.setEnabled(enable)
            
    def preferences(self):
        """Opens the preferences dialog."""
        dialog = preferences_dlg.Preferences()
        if dialog.exec_():
            self.set_settings()
            
    def clear(self):
        """Clears the form.
        
        Clears line edits and unchecks checkboxes and radio buttons.
        """
        
        self.fromLineEdit.clear()
        self.fname = ''
        if self.output != 'original':
            self.toLineEdit.clear()
            self.output = ''    
        boxes = [self.folderCheckBox, self.recursiveCheckBox, 
                                                           self.deleteCheckBox]              
        for box in boxes:
            box.setChecked(False)
        self.checkboxes_clicked()
        
        [i.clear() for i in self.tabs]

    def open_file(self):
        """Uses standard QtDialog to get file name."""
        all_files = '*'
        audio_files = " ".join(['*.' + i for i in self.audio_formats])
        video_files = " ".join(['*.' + i for i in self.video_formats])
        image_files = " ".join(
               ['*.' + i for i in self.image_formats + self.extra_img_formats])
        document_files = " ".join(['*.' + i for i in self.document_formats])
        formats = [all_files, audio_files, video_files, image_files, 
                                                                document_files]
        strings = [self.tr('All Files'), self.tr('Audio Files'), 
                   self.tr('Video Files'), self.tr('Image Files'), 
                   self.tr('Document Files')]
        
        filters = ''
        for string, extensions in zip(strings, formats):
            filters += string + ' ({0});;'.format(extensions)
        filters = filters[:-2] # remove last ';;'
        
        fname = QFileDialog.getOpenFileName(self, self.tr(
                       "FF Multi Converter - Choose File"), self.home, filters)
        fname = unicode(fname)
        if fname:
            self.fname = fname
            self.fromLineEdit.setText(self.fname)
            
    def open_dir(self):
        """Uses standard QtDialog to get directory name."""
        if self.toLineEdit.isEnabled():
            output = QFileDialog.getExistingDirectory(self, self.tr(
                  "FF Multi Converter - Choose output destination"), self.home)
            output = unicode(output)
            if output:
                self.output = output
                self.toLineEdit.setText(self.output)
        else:
            return QMessageBox.warning(self, self.tr(
                "FF Multi Converter - Save Location!"), self.tr(
                   "You have chosen to save every file to its original folder."
                   "\nYou can change this from preferences."))
            
    def get_extensions(self):
        """Returns the from and to extensions.
        
        Returns: 2 strings
        """        
        tab = self.current_tab()
        ext_from = '.' + unicode(tab.fromComboBox.currentText())
        ext_to = '.' + unicode(tab.toComboBox.currentText())                
        # split from the docsting (Audio Only) if it is appropriate
        ext_to = ext_to.split(' ')[0]        
        return ext_from, ext_to

    def find_type(self):
        """Specifies the current file formats.
        
        Returns: list
        """
        tab = self.current_tab()
        type_formats = tab.formats
        index = self.TabWidget.currentIndex()
        if index == 1:
            type_formats = self.video_formats
        elif index == 2:
            type_formats.extend(self.extra_img_formats)
        return type_formats      
        
    def files_to_conv_list(self):        
        """Generates paths of files to convert.
        
        Creates:
        1.files_to_conv -- list with files that must be converted
        The list will contain only the _file if conversion is no recursive
                
        Returns: list
        """           
        _dir, file_name = os.path.split(self.fname)
        base, ext = os.path.splitext(file_name)
        _dir += '/*'
                
        formats = self.find_type()
        files_to_conv = []
        includes = []
                
        if not (self.folderCheckBox.isChecked() or \
                                          self.recursiveCheckBox.isChecked()):
            files_to_conv = [self.fname]
        
        else:
            recursive = True if self.recursiveCheckBox.isChecked() else False
            if self.extRadioButton.isChecked():
                includes = ['*' + ext]
            else:
                for i in formats:
                    includes.append('*.' + i)          
            
            for i in path_generator._paths_from_path_patterns([_dir], 
                                       recursive=recursive, includes=includes):
                files_to_conv.append(i)        
        
        # put given file first in list
        files_to_conv.remove(self.fname)
        files_to_conv.insert(0, self.fname)
        
        return files_to_conv
        
    def build_lists(self, ext_to, files_list):
        """Creates two lists:
        
        1.conversion_list -- list with dicts to show where each file must be 
                             saved. 
        Example:
        [{/foo/bar.png : /foo/foo2/bar.png}, {/f/bar2.png : /f/foo2/bar2.png}]
        2.create_folders_list -- a list with folders that must be created
        
        Keyword arguments:
        ext_to       -- the extension to which each file must be converted to
        files_list   -- list with files to be converted
                           
        Returns: two lists
        """                                                    
        rel_path_files_list = []
        folders = []
        create_folders_list = []
        conversion_list = []    
        
        folder = self.output
        folder += '/'
        parent_file = files_list[0]        
        parent_dir, parent_name = os.path.split(parent_file)
        parent_base, parent_ext = os.path.split(parent_name)
        parent_dir += '/'
                        
        for i in files_list:
            _dir, name = os.path.split(i)
            base, ext = os.path.splitext(name)
            _dir += '/'
            
            y = _dir + self.prefix + base + self.suffix + ext_to
            
            if self.saveto_output:                            
                if self.rebuild_structure:
                    y = re.sub('^'+parent_dir, '', y)
                    y = folder + y
                    rel_path_files_list.append(y)
                    
                    for z in rel_path_files_list:
                        folder_to_create = os.path.split(z)[0]
                        folders.append(folder_to_create) 
                        
                    # remove list from duplicates
                    for fol in folders:
                        if not fol in create_folders_list:
                            create_folders_list.append(fol)                    
                    create_folders_list.sort()
                    # remove first folder because it already exists.
                    create_folders_list.pop(0)                                                             
                
                else:
                    y = re.sub('^'+_dir, '', y)
                    y = folder + y
        
            _dict = {}
            _dict[i] = y
            conversion_list.append(_dict)
        
        return create_folders_list, conversion_list     
        
    def ok_to_continue(self, ext_from, ext_to):
        """Checks if everything is ok to continue with conversion.
        
        Checks if: 
         - Theres is no given file
         - Given file exists
         - Given output destination exists
         - Given file extension is same with the declared extension
         - Declared from_extension == declared to_extension
         - Missing dependencies for this file type

        Keyword arguments:
        ext_from -- current file extension
        ext_to -- the extension for file to be converted to
        
        Returns: boolean        
        """
        _file = os.path.split(self.fname)[-1]
        real_ext = os.path.splitext(_file)[-1]
        index = self.TabWidget.currentIndex()
        
        # give small names to the variables in order to wide use them below
        a = real_ext
        b = ext_from
        
        try:
            if self.fname == '':
                raise ValidationError(self.tr(
                                         'You must choose a file to convert!'))
            elif not os.path.exists(self.fname):
                raise ValidationError(self.tr(
                                         'The selected file does not exists!'))
            elif self.output != 'original' and self.output == '':
                raise ValidationError(self.tr(
                                          'You must choose an output folder!'))
            elif self.output != 'original' and not os.path.exists(self.output):                
                raise ValidationError(self.tr(
                                             'Output folder does not exists!'))
            elif not a == b and not ((a == '.dib' and b == '.bmp') or \
                (a == '.ps' and b == '.eps') or ((a == '.jpg' or a == '.jpe')\
                and b == '.jpeg') or (a == '.tiff' and b == '.tif')):
                # look if real_ext is same type with ext_from and just have
                # different extension. eg: jpg is same as jpeg
                raise ValidationError(self.tr(
                                "File' s extensions is not %1.").arg(ext_from))
            elif ext_from == ext_to and self.output == 'original':
                raise ValidationError(self.tr(
                    'You can not convert the file extension to the existing!'))
            elif (index == 0 or index == 1) and not self.ffmpeg:
                raise ValidationError(self.tr(
                    'Program FFmpeg is not installed.\nYou will not be able '
                    'to convert video and audio files until you install it.'))
            elif index == 2 and not self.pmagick:
                raise ValidationError(self.tr(
                    'PythonMagick is not installed.\nYou will not be able to '
                    'convert image files until you install it.'))
            elif index == 3 and not (self.openoffice or self.libreoffice):
                raise ValidationError(self.tr(
                    'Open/Libre office suite is not installed.\nYou will not '
                    'be able to convert document files until you install it.'))
            elif index == 3 and not self.unoconv:
                raise ValidationError(self.tr(
                    'Program unocov is not installed.\nYou will not be able '
                    'to convert document files until you install it.'))
            return True
        except ValidationError as e:
            QMessageBox.warning(self, self.tr("FF Multi Converter - Error!"), 
                                                                    unicode(e))
            return False
            
    def convert(self):
        """Initialises the Progress dialog."""
        ext_from, ext_to = self.get_extensions()          
        if not self.ok_to_continue(ext_from, ext_to):
            return         
        
        index = self.TabWidget.currentIndex()
        delete = self.deleteCheckBox.isChecked()                             
        files_to_conv = self.files_to_conv_list()
        create_folders_list, conversion_list = self.build_lists(ext_to, 
                                                                 files_to_conv)
        if create_folders_list:
            for i in create_folders_list:
                try:
                    os.mkdir(i)
                except OSError:
                    pass
        
        dialog = Progress(self, conversion_list, ext_to, index, delete)
        dialog.show()   
        dialog.exec_()
            
    def about(self):
        """Shows an About dialog using qt standard dialog."""
        link  = 'https://github.com/Ilias95/FF-Multi-Converter/wiki/'
        link += 'FF-Multi-Converter'
        QMessageBox.about(self, self.tr("About FF Multi Converter"), self.tr( 
            '''<b> FF Multi Converter %1 </b>
            <p>Convert among several file types to other extensions
            <p><a href="%2">FF Multi Converter</a>
            <p>Copyright &copy; 2011 Ilias Stamatis  
            <br>License: GNU GPL3
            <p>Python %3 - Qt %4 - PyQt %5 on %6''').arg(__version__).arg(link)
            .arg(platform.python_version()[:5]).arg(QT_VERSION_STR)
            .arg(PYQT_VERSION_STR).arg(platform.system()))
    
    def is_installed(self, program):
        """Checks if program is installed."""
        for path in os.getenv('PATH').split(os.pathsep):
            fpath = os.path.join(path, program)
            if os.path.exists(fpath) and os.access(fpath, os.X_OK):
                return True
        return False

    def check_for_dependencies(self):
        """Checks if dependencies are installed and set dependenciesLabel 
        status."""
        missing = []
        if self.is_installed('ffmpeg'):
            self.ffmpeg = True
        else:
            self.ffmpeg = False
            missing.append('FFmpeg')
        if self.is_installed('unoconv'):
            self.unoconv = True
        else:
            self.unoconv = False  
            missing.append('unoconv')
        if self.is_installed('openoffice.org'):
            self.openoffice = True
        else:
            self.openoffice = False  
        if self.is_installed('libreoffice'):
            self.libreoffice = True
        else:
            self.libreoffice = False          
        if not self.openoffice and not self.libreoffice:
            missing.append('Open/Libre Office')        
        try:
            from PythonMagick import Image
            self.pmagick = True
        except ImportError:
            self.pmagick = False
            missing.append('PythonMagick')            
        
        missing = ", ".join(missing) if missing else self.tr('None')
        status = self.tr('Missing dependencies: ') + missing
        self.dependenciesLabel.setText(status)                            


class Progress(QDialog):
    """Does the conversions and shows progress in a dialog."""
    # There are two bars in the dialog. 
    # One that shows the progress of each file and one for total progress.
    #
    # Audio, image and document conversions don't need much time to complete 
    # so the first bar just shows 0% at the beggining and 100% when convertion 
    # done for every file.
    #    
    # Video conversions may take some time so the first bar takes values.
    # The numbers of frames are equal in input and output file.
    # To find the percentage of progress it counts the frames of output file at
    # regular intervals and compares it to the number of frames of input.
    
    def __init__(self, parent, files, ext_to, index, delete):
        """Constructs the progress dialog.
        
        Keyword arguments:
        files -- list with files to be converted
        ext_to -- the extension to convert to
        index -- number that shows file type
        delete -- boolean that shows if files must removed after conversion
        """
        super(Progress, self).__init__(parent)
        self.parent = parent

        self.files = files
        self.ext_to = ext_to
        self.index = index
        self.delete = delete
        self.step = 100 / len(files)
        self.ok = 0 
        self.error = 0        
        ext = self.ext_to
        if self.index == 0 or (self.index == 1 and (ext == 'aac' or \
                            ext == 'ac3' or ext == 'aiff' or ext == 'au' \
                            or ext == 'flac' or ext == 'mp2' or ext == 'wav')):
            self._type = 'audio'
        elif self.index == 1:
            self._type = 'video'
        elif self.index == 2:
            self._type = 'image'
        else:
            self._type = 'document'

        self.nowLabel = QLabel(self.tr('In progress: '))
        totalLabel = QLabel(self.tr('Total:'))
        self.nowBar = QProgressBar()
        self.nowBar.setValue(0)
        self.totalBar = QProgressBar()
        self.totalBar.setValue(0)  
        self.shutdownCheckBox = QCheckBox(self.tr('Shutdown after conversion'))
        self.cancelButton = QPushButton(self.tr('Cancel'))    
                
        hlayout = pyqttools.add_to_layout(QHBoxLayout(), None, self.nowLabel, 
                                                                          None)
        hlayout2 = pyqttools.add_to_layout(QHBoxLayout(), None, totalLabel,
                                                                          None)
        hlayout3 = pyqttools.add_to_layout(QHBoxLayout(), 
                                                   self.shutdownCheckBox, None)
        hlayout4 = pyqttools.add_to_layout(QHBoxLayout(), None, 
                                                             self.cancelButton)
        vlayout = pyqttools.add_to_layout(QVBoxLayout(), hlayout, 
                self.nowBar, hlayout2, self.totalBar, None, hlayout3, hlayout4)
        self.setLayout(vlayout)

        self.cancelButton.clicked.connect(self.reject)
        
        self.resize(435, 190)   
        self.setWindowTitle(self.tr('FF Multi Converter - Conversion'))
        
        self.timer = QBasicTimer()
        self.timer.start(100, self)
        
    def timerEvent(self, timeout):
        """Event handler for self.timer."""
        if not self.files:
            self.totalBar.setValue(100)
        if self.totalBar.value() >= 100:
            self.timer.stop()
            if self.shutdownCheckBox.isChecked():
                cmd = str(QString('shutdown -h now').toUtf8())
                subprocess.call(shlex.split(cmd))
            sum_files = self.ok + self.error
            QMessageBox.information(self, self.tr('Report'), 
                       self.tr('Converted: %1/%2').arg(self.ok).arg(sum_files))
            self.accept()
            return
        self.convert_a_file()
        if self._type != 'video':
            value = self.totalBar.value() + self.step
            self.totalBar.setValue(value)
                                
    def reject(self):
        """Uses standard dialog to ask whether procedure must stop or not."""
        if self._type == 'video':
            # pause the procedure
            self.convert_prcs.send_signal(signal.SIGSTOP)
        else:
            self.timer.stop()
        reply = QMessageBox.question(self, 
            self.tr('FF Multi Converter - Cancel Conversion'),
            self.tr('Are you sure you want to cancel conversion?'),
            QMessageBox.Yes|QMessageBox.Cancel)
        if reply == QMessageBox.Yes:
            QDialog.reject(self)
            ext = self.ext_to
            if self._type == 'video':
                try:
                    self.convert_prcs.kill()
                except:
                    pass
                
        if reply == QMessageBox.Cancel:
            if self._type == 'video':
                try:
                    self.convert_prcs.send_signal(signal.SIGCONT)
                except:
                    pass
            else:
                self.timer.start(100, self)
            
    def convert_a_file(self):
        """Starts the conversion procedure depending to file type."""
        if not self.files:
            return
        from_file = self.files[0].keys()[0]
        to_file = self.files[0].values()[0]
        
        text = '.../' + from_file.split('/')[-1] if len(from_file) > 40 \
                                                            else from_file
        self.nowLabel.setText(self.tr('In progress: ') + text)
        
        QApplication.processEvents() # force UI to update
        self.nowBar.setValue(0)
        
        if self._type == 'audio':
            if self.convert_audio(from_file, to_file, self.delete):
                self.ok += 1
            else:
                self.error += 1
        elif self._type == 'video':
            if self.convert_video(from_file, to_file, self.delete):
                self.ok += 1
            else:
                self.error += 1
        elif self._type == 'image':
            if self.convert_image(from_file, to_file, self.delete):
                self.ok += 1              
            else:
                self.error += 1                
        else:
            if self.convert_document_file(from_file, to_file, self.delete):
                self.ok += 1             
            else:
                self.error += 1  
        
        QApplication.processEvents()
        self.nowBar.setValue(100)
        self.files.pop(0)        
        
    def number_of_frames(self, _file):
        """Counts the number of frames in a video.
        
        Returns: integer
        """
        cmd = "ffmpeg -i {0} -vcodec copy -f rawvideo -y /dev/null".format(
                                                                         _file)
        cmd = str(QString(cmd).toUtf8())
        exec_cmd = subprocess.Popen(shlex.split(cmd), stderr=subprocess.PIPE)
        output = unicode(QString(exec_cmd.stderr.read()))
        for i in output.split('\n'):
            if 'frame=' in i:
                frames = re.sub( r'^frame=\s*([0-9]+)\s.*$', r'\1', i)
        try:
            frames = int(frames)
        except:
            frames = 0
        return frames

    def convert_video(self, from_file, to_file, delete):
        """Converts the file format of a video and update progress info
        of each file.
        
        It starts conversion with subprocess.Popen() and gets the number of 
        frames in the new video continuously.        
        Progress is calculated from the percentage of frames of the new file 
        compared to frames of the original file.
        
        Keyword arguments:
        from_file -- the file to be converted
        to_file -- the new file
        delete  -- if True, delete from_file
        
        Returns: boolean
        """
        # Add quotations to path in order to avoid error in special cases 
        # such as spaces or special characters. 
        from_file2 = '"' + from_file + '"'
        to_file = '"' + to_file + '"'        
        
        min_value = self.totalBar.value()
        max_value = min_value + self.step
        for i in range(2):
            # do it twice because number_of_frames() fails some times at first 
            total_frames = self.number_of_frames(from_file2)
        if total_frames == 0:
            self.totalBar.setValue(max_value)
            return False
            
        convert_cmd = 'ffmpeg -y -i {0} -sameq {1}'.format(from_file2, to_file)
        convert_cmd = str(QString(convert_cmd).toUtf8())        
        self.convert_prcs = subprocess.Popen(shlex.split(convert_cmd))
                
        while self.convert_prcs.poll() == None:
            time.sleep(1)       
            frames = self.number_of_frames(to_file)
            now_percent = (frames * 100) / total_frames
            total_percent = ((now_percent * self.step) / 100) + min_value                
            now_val = self.nowBar.value()
            tot_val = self.totalBar.value()
            
            # processEvents() force the UI to update
            QApplication.processEvents()
            if now_percent > now_val and not (now_percent > 100):
                self.nowBar.setValue(now_percent)                            
            if total_percent > tot_val and not (total_percent > max_value):
                self.totalBar.setValue(total_percent)
                
        self.totalBar.setValue(max_value)        
        converted = True if self.convert_prcs.poll() == 0 else False
        if converted and delete:
            os.remove(from_file)
        return converted    
    
    def convert_audio(self, from_file, to_file, delete):
        """Converts the file format of an audio via ffmpeg.
        
        Keyword arguments:
        from_file -- the file to be converted
        to_file -- the new file
        delete  -- if True, delete from_file
        
        Returns: boolean
        """
        # Add quotations to path in order to avoid error in special cases 
        # such as spaces or special characters.
        from_file2 = '"' + from_file + '"'
        to_file = '"' + to_file + '"'
        command = 'ffmpeg -y -i {0} -sameq {1}'.format(from_file2, to_file)
        command = str(QString(command).toUtf8())
        command = shlex.split(command)
        converted = True if subprocess.call(command) == 0 else False
        if converted and delete:
            os.remove(from_file)
        return converted
        
    def convert_image(self, from_file, to_file, delete):
        """Converts the file format of an image.
        
        from_file -- the file to be converted
        to_file -- the new file
        delete  -- if True, delete from_file     
        
        Returns: boolean
        """
        try:
            _from = str(QString(from_file).toUtf8())
            to = str(QString(to_file).toUtf8())
            img = Image(_from)
            img.write(to)
            converted = True
        except:
            converted = False
        if converted and delete:
            os.remove(from_file)
        return converted        
        
    def convert_document_file(self, from_file, to_file, delete):
        """Converts the file format of a document file.
        
        from_file -- the file to be converted
        to_file -- the new file
        delete  -- if True, delete from_file     
        
        Returns: boolean    
        """        
        # Add quotations to path in order to avoid error in special cases 
        # such as spaces or special characters.        
        from_file2 = '"' + from_file + '"'
        _file, extension = os.path.splitext(to_file)
        command = 'unoconv --format={0} {1}'.format(extension[1:], from_file2)
        command = str(QString(command).toUtf8())
        command = shlex.split(command)        
        converted = True if subprocess.call(command) == 0 else False
        if converted:
            # new file saved to same folder as original so it must be moved
            _file2 = os.path.splitext(from_file)[0]
            now_created = _file2 + extension
            shutil.move(now_created, to_file)
            if delete:
                os.remove(from_file)
        return converted               

class ValidationError(Exception):
    # used in FFMultiConverter.ok_to_continue()
    pass
                    
def main():
    app = QApplication(sys.argv)
    app.setOrganizationName('ffmulticonverter')
    app.setOrganizationDomain('sites.google.com/site/ffmulticonverter/')
    app.setApplicationName('FF Muli Converter')    
    app.setWindowIcon(QIcon(':/ffmulticonverter.png'))
    
    # search if there is locale translation avalaible and set the Translators
    locale = QLocale.system().name()
    locale = ''
    qtTranslator = QTranslator()
    if qtTranslator.load("qt_" + locale, ":/"):
        app.installTranslator(qtTranslator)
    appTranslator = QTranslator()
    if appTranslator.load("ffmulticonverter_" + locale, ":/"):
        app.installTranslator(appTranslator)
        
    converter = FFMultiConverter()
    converter.show()
    app.exec_()    
    
if __name__ == '__main__':
    main()

#image widgets, PythonMagick, clear, 
#TODO: check if current tab works properly
