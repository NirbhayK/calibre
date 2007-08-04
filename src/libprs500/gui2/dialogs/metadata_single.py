##    Copyright (C) 2006 Kovid Goyal kovid@kovidgoyal.net
##    This program is free software; you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation; either version 2 of the License, or
##    (at your option) any later version.
##
##    This program is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License along
##    with this program; if not, write to the Free Software Foundation, Inc.,
##    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
''' 
The dialog used to edit meta information for a book as well as 
add/remove formats
'''
import os

from PyQt4.QtCore import SIGNAL
from PyQt4.Qt import QObject, QPixmap, QListWidgetItem, QErrorMessage


from libprs500.gui2 import qstring_to_unicode, error_dialog, file_icon_provider, \
                           choose_files, pixmap_to_data, BOOK_EXTENSIONS, choose_images
from libprs500.gui2.dialogs import Dialog
from libprs500.gui2.dialogs.metadata_single_ui import Ui_MetadataSingleDialog

class Format(QListWidgetItem):
    def __init__(self, parent, ext, path=None):
        self.path = path
        self.ext = ext
        QListWidgetItem.__init__(self, file_icon_provider().icon_from_ext(ext), 
                                 ext.upper(), parent, QListWidgetItem.UserType)

class MetadataSingleDialog(Ui_MetadataSingleDialog, Dialog):
    
    def select_cover(self, checked):
        files = choose_images(self.window, 'change cover dialog', 
                             u'Choose cover for ' + qstring_to_unicode(self.title.text()))
        if not files:
            return
        _file = files[0]
        if _file:
            _file = os.path.abspath(_file)
            if not os.access(_file, os.R_OK):
                d = error_dialog(self.window, 'Cannot read', 
                        'You do not have permission to read the file: ' + _file)
                d.exec_()
                return
            cf, cover = None, None
            try:
                cf = open(_file, "rb")
                cover = cf.read()
            except IOError, e: 
                d = error_dialog(self.window, 'Error reading file',
                        "<p>There was an error reading from file: <br /><b>" + _file + "</b></p><br />"+str(e))
                d.exec_()
            if cover:
                pix = QPixmap()
                pix.loadFromData(cover)
                if pix.isNull():
                    d = error_dialog(self.window, _file + " is not a valid picture")
                    d.exec_()
                else:
                    self.cover_path.setText(_file)
                    self.cover.setPixmap(pix)
                    self.cover_changed = True
                    self.cpixmap = pix                  
    
    
    def add_format(self, x):
        files = choose_files(self.window, 'add formats dialog', 
                             "Choose formats for " + str(self.title.text()),
                             [('Books', BOOK_EXTENSIONS)])
        if not files: 
            return      
        for _file in files:
            _file = os.path.abspath(_file)
            if not os.access(_file, os.R_OK):
                QErrorMessage(self.window).showMessage("You do not have "+\
                                    "permission to read the file: " + _file)
                continue
            ext = os.path.splitext(_file)[1].lower()
            if '.' in ext:
                ext = ext.replace('.', '')
            for row in range(self.formats.count()):
                fmt = self.formats.item(row)
                if fmt.ext == ext:
                    self.formats.takeItem(row)
                    break
            Format(self.formats, ext, path=_file)
            self.formats_changed = True
    
    def remove_format(self, x):
        rows = self.formats.selectionModel().selectedRows(0)
        for row in rows:
            self.formats.takeItem(row.row())
            self.formats_changed = True
    
    def sync_formats(self):
        old_extensions, new_extensions, paths = set(), set(), {}
        for row in range(self.formats.count()):
            fmt = self.formats.item(row)
            ext, path = fmt.ext, fmt.path
            if 'unknown' in ext.lower():
                ext = None
            if path:
                new_extensions.add(ext)
                paths[ext] = path
            else:
                old_extensions.add(ext)
        for ext in new_extensions:
            self.db.add_format(self.row, ext, open(paths[ext], "rb"))
        db_extensions = set(self.db.formats(self.row).split(','))
        extensions = new_extensions.union(old_extensions)
        for ext in db_extensions:
            if ext not in extensions:
                self.db.remove_format(self.row, ext)
    
    def __init__(self, window, row, db):
        Ui_MetadataSingleDialog.__init__(self)
        Dialog.__init__(self, window)
        self.setupUi(self.dialog)
        self.splitter.setStretchFactor(100, 1)
        self.db = db
        self.id = db.id(row)
        self.row = row
        self.cover_data = None
        self.formats_changed = False
        self.cover_changed = False
        self.cpixmap = None
        self.changed = False
        QObject.connect(self.cover_button, SIGNAL("clicked(bool)"), \
                                                    self.select_cover)
        QObject.connect(self.add_format_button, SIGNAL("clicked(bool)"), \
                                                    self.add_format)
        QObject.connect(self.remove_format_button, SIGNAL("clicked(bool)"), \
                                                self.remove_format)
        QObject.connect(self.button_box, SIGNAL("accepted()"), \
                                                self.sync)
        
        self.title.setText(db.title(row))
        au = self.db.authors(row)
        self.authors.setText(au if au else '')
        pub = self.db.publisher(row)
        self.publisher.setText(pub if pub else '')
        tags = self.db.tags(row)
        self.tags.setText(tags if tags else '')
        rating = self.db.rating(row)
        if rating > 0: 
            self.rating.setValue(int(rating/2.))
        comments = self.db.comments(row)
        self.comments.setPlainText(comments if comments else '')
        cover = self.db.cover(row)
        if cover:
            pm = QPixmap()
            pm.loadFromData(cover)
            if not pm.isNull(): 
                self.cover.setPixmap(pm)
        exts = self.db.formats(row)
        if exts:
            exts = exts.split(',')        
            for ext in exts:
                if not ext:
                    ext = ''
                Format(self.formats, ext)
            
        if qstring_to_unicode(self.series.currentText()):
            self.enable_series_index()
            
        
        all_series = self.db.all_series()
        series_id = self.db.series_id(row)
        idx, c = None, 0
        for i in all_series:
            id, name = i
            if id == series_id:
                idx = c
            self.series.addItem(name)
            c += 1
        
        self.series.lineEdit().setText('')
        if idx is not None:
            self.series.setCurrentIndex(idx)
            
        self.series_index.setValue(self.db.series_index(row))
        QObject.connect(self.series, SIGNAL('currentIndexChanged(int)'), self.enable_series_index)
        QObject.connect(self.series, SIGNAL('editTextChanged(QString)'), self.enable_series_index)
         

        self.dialog.exec_()

    def enable_series_index(self, *args):
        self.series_index.setEnabled(True)
    
    def sync(self):
        if self.formats_changed:
            self.sync_formats()
        title = qstring_to_unicode(self.title.text())
        self.db.set_title(self.id, title)
        au = qstring_to_unicode(self.authors.text()).split(',')
        self.db.set_authors(self.id, au)
        self.db.set_rating(self.id, 2*self.rating.value())
        self.db.set_publisher(self.id, qstring_to_unicode(self.publisher.text()))
        self.db.set_tags(self.id, qstring_to_unicode(self.tags.text()).split(','))
        self.db.set_series(self.id, qstring_to_unicode(self.series.currentText()))
        self.db.set_series_index(self.id, self.series_index.value())
        self.db.set_comment(self.id, qstring_to_unicode(self.comments.toPlainText()))
        if self.cover_changed:
            self.db.set_cover(self.id, pixmap_to_data(self.cover.pixmap()))
        self.changed = True
    
    def reject(self):
        self.rejected = True
