#!/usr/bin/env python

"""
    This project does:
        1. display partial implementation vcard
        2. allow to add and remove vcard from 'db'
        3. allow to search for a number/item (do we have it in db)
        4. allow to select particular vcards and export them to file.

        Currently it's gui only, and probably will stay that way.
        Obviously multiple todos are scattered across the file.
        Uses vobject, http://vobject.skyhouseconsulting.com/ (Apache 2.0)
        hovewer vobject does not support vCard 4.0 for now.
"""

from PyQt4 import QtGui, QtCore
import codecs
# careful = vobject does not install in pip3 as of 2015-01-01
import vobject # vcard parser => sudo pip install vobject

###########################################################################

# I want to see only those
vcard_wanted_fields = ("disp_name", "name", "surname", 
                       "phone", "timestamp", "email")
# and those maps to these vcard fields...wow, names are held crappy way
# i'll need an exception to parse n to name/surname...
vcf_mapping  = {"name":"n|family", "phone":"tel", "surname":"n|given",
                "timestamp":"rev", "disp_name":"fn",
                "email":"email"}

default_filename = "contacts.vcf"

###########################################################################

def run_application(args=[], vcf_file_path=None):
    # todo: get as argv but for now i dont care.
    stored_vcards = prepare_file(vcf_file_path)
    app = QtGui.QApplication(args)
    # we actually need to know how many cards we have
    # so vobject generator is useless here.
    stored_vcards = list(vobject.readComponents(stored_vcards))
    runme = Layout(stored_vcards)
    runme(app)

###########################################################################

def prepare_file(path):
    # TODO: move this to database instead of vcf file?
    path = path if path else default_filename 
    #path = path if path else "test_vcards.vcf" # TESTING
    # skip playing with unicode py2/py3 for now and use codecs.
    db = codecs.open(path, "ab+", "utf-8")
    db.seek(0)
    return db.read()

###########################################################################

class Table(QtGui.QTableWidget):
    # TODO: get rid of table widget and implement QTableView
    def __init__(self, stored_vcards):
        QtGui.QTableWidget.__init__(self)
        self.verticalHeader().setVisible(False)
        #self.horizontalHeader().setVisible(False)
        self.resizeColumnsToContents() # TODO: might be bad idea-limit this.
        self.vcards = stored_vcards
        self.setRowCount(len(stored_vcards))
        self.setColumnCount(len(vcard_wanted_fields))
        self.setHorizontalHeaderLabels(vcard_wanted_fields)
        if self.vcards:
            self.populate_vcards()
        
    def populate_vcards(self):
        # TODO: refactor this somehow
        row = 0
        for vcard in self.vcards:
            col = 0
            for field in vcard_wanted_fields:
                #print ("=============", field)
                if field in ("name", "surname"):
                    vcf_field, subitem = vcf_mapping[field].split('|')
                    # vobject, Y U no have __getitem__ ?
                    # problem is as follows: VCard defines N:??;???;??
                    # as required arg only in version 2/3, but optional in 4
                    # still, in fn there is no separation for name/title/surn.
                    parent = getattr(vcard, vcf_field).value
                    try:
                        value = getattr(parent, subitem)
                    except AttributeError:
                        print ("({0}) Vcard has no {1} attr in {2} field"
                                  "".format(row, subitem, vcf_field))
                        value = ""
                # should also decrypt timestamp to readable thing
                else:
                    try:
                        value = getattr(vcard, vcf_mapping[field]).value
                    except AttributeError:
                        print ("({}) Vcard has no {} field".format(row, field))
                        value = ""
                item = QtGui.QTableWidgetItem(value)
                self.setItem(row, col, item)
                col += 1
            row += 1

class Fields(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QHBoxLayout()
        self.populate_fields()
        self.setLayout(self.layout)

    def populate_fields(self):
        items = vcard_wanted_fields
        for item in items:
            setattr(self, item, QtGui.QLineEdit(self))
            getattr(self, item).setPlaceholderText(item)
            self.layout.addWidget(getattr(self, item))

class Controls(QtGui.QWidget):
    def __init__(self, other_widgets):
        QtGui.QWidget.__init__(self)
        self.other_widgets = other_widgets
        self.layout = QtGui.QHBoxLayout()
        self.populate_controls()
        self.setLayout(self.layout)

    def populate_controls(self):
        items = {"Add row":                self.do_add,
                 "Remove selected row(s)": self.do_remove,
                 "Export selected row(s)": self.do_export,
                 "Search":                 self.do_search,
                 "Save":                   self.do_save,
                 "Select all":             self.select_all,
                 "Select none":            self.select_none,
                }
        items_keys = sorted(list(items.keys()))
        for item in items_keys:
            setattr(self, item, QtGui.QPushButton(item, self))
            getattr(self, item).clicked.connect(items[item])
            self.layout.addWidget(getattr(self, item))

        # search = QtGui.QAction(QtGui.QIcon(), 'Search', self)
        # search.setShortcut('Ctrl+f')
        # self.connect(search, QtCore.SIGNAL('search_sig()'),
        #   QtCore.SLOT('search_slot()'))
        
        # TODO:  sort, setSortingEnabled(True) ?
        # TODO:  filter (excel like)

    def do_add(self):
        
        row = self.other_widgets["table"].rowCount() # +1 ok
        self.other_widgets["table"].insertRow(row)   # -1 ok
        for col, field in enumerate(vcard_wanted_fields):
            # if field in ("name", "surname"):
            #     vcf_field, subitem = vcf_mapping[field].split('|')
            #     value = getattr(vcard, vcf_mapping[field]).value
            item = QtGui.QTableWidgetItem(getattr(self.other_widgets["fields"], field).text())
            self.other_widgets["table"].setItem(row, col, item)


    def do_save(self):
        self.select_all()
        self.do_export(default_filename)
        self.select_none()

    def do_remove(self):
        for item in self.other_widgets["table"].selectedItems():
            self.other_widgets["table"].removeRow(item.row())

    def do_search(self):
        # TODO:actually this searches whole table, whereas i want to
        #      search column only, or multiple columns at once.
        #      I could check column number and drop all results not matching,
        #      or i could think of some better logic here. Right now it just 
        #      adds multiple searches, so this is boolean OR not AND for cols.
        count = 0
        #results = []
        found = ""
        for column in vcard_wanted_fields:
            query = getattr(self.other_widgets["fields"], column).text()
            if not query:
                continue # dont search empty fields
            found = self.other_widgets["table"].findItems(
                                query,
                                QtCore.Qt.MatchExactly) # TODO - button for loose match
            if found:
                count += len(found)
                # TODO: for now just infobox...should run filter or table, selectItem
                #       or at least scrollToItem()
                items = ["".join(["row:", str(item.row()), ' ', 
                                  "col:", str(item.column())]) for item in found]
                found = "<br>".join(items)
                #results.append(found)
            
        msg = "{} hit(s) <br>{}".format(count, found)
        QtGui.QMessageBox.information(self, 'Search Results', msg)
        # TODO: look also at displayRole
        # TODO: WTF Segfaults occasionaly here ?!


    def do_export(self, path):
        # can select cells but we want to export (probably?) whole row (set)
        rows = {item.row() 
                for item in self.other_widgets["table"].selectedItems()}
        # TODO: QItemSelectionModel ... read and understand
        
        # TODO: check how does exactly clicked pass False as second argument to this
        if not path:
            path="export.vcf"

        # TODO: by the gods, somebody kill this monstrosity
        if rows:
            with codecs.open(path, "wb+", "utf-8") as fp:
                for row in rows:
                    vcard = vobject.vCard()
                    for colno, col in enumerate(vcard_wanted_fields):
                        item = self.other_widgets["table"].item(row, colno)
                        if col in ("name", "surname"):
                            subkey = vcf_mapping[col].split('|')[1]
                            value = unicode(item.text())
                            # this...is...nasty. but look at Vobject docs :|
                            if hasattr(vcard, 'n'):
                                store_first_part.update({subkey:value})
                                # now 'store_first_part' has 2 parts, and is complete...
                                vcard.n.value = vobject.vcard.Name(**store_first_part)
                            else:
                                vcard.add("n")
                                store_first_part = {subkey:value}
                        else:
                            name = vcf_mapping[col]
                            vcard.add(name)
                            # craziness again...
                            setattr(getattr(vcard, name), "value", unicode(item.text()))
                    fp.write(vcard.serialize().decode("utf-8"))
                    fp.write('\n')

    def select_all(self):
        cols = self.other_widgets["table"].columnCount()-1
        rows = self.other_widgets["table"].rowCount()-1
        sel_range = QtGui.QTableWidgetSelectionRange(0, 0, rows, cols)
        self.other_widgets["table"].setRangeSelected(sel_range, True)
    def select_none(self):
        cols = self.other_widgets["table"].columnCount()-1
        rows = self.other_widgets["table"].rowCount()-1
        sel_range = QtGui.QTableWidgetSelectionRange(0, 0, rows, cols)
        self.other_widgets["table"].setRangeSelected(sel_range, False)

class Layout(QtGui.QWidget):
    def __call__(self, app):
        self.show()
        app.exec_()
    def __init__(self, stored_vcards):
        QtGui.QWidget.__init__(self)
        self.setWindowTitle("Vcards db")
        self.vcards = stored_vcards
        self.layout = QtGui.QVBoxLayout()
        self.populate_layout()
        self.setLayout(self.layout)

    def populate_layout(self):
        # too lazy to use slot/signal here, so here we go (1)
        other_widgets = {"table":None, "fields":None}
        # create buttons
        controls = Controls(other_widgets)
        #self.layout.addLayout(controls)
        self.layout.addWidget(controls)
        self.layout.addStretch(1)

        # create fields
        fields = Fields()
        self.layout.addWidget(fields)
        self.layout.addStretch(1)

        # # create table
        table = Table(self.vcards)
        self.layout.addStretch(1)
        self.layout.addWidget(table)

        # update handle to table...lazy 'ipc' between widgets (2)
        other_widgets.update({"table":table, "fields":fields})

if __name__ == "__main__":
    run_application()