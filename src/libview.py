#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This file is part of Multilist.

Multilist is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Multilist is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Multilist.  If not, see <http://www.gnu.org/licenses/>.

Copyright (C) 2008 Christoph Würstle
"""

import logging

import gtk
import gobject

import gtk_toolbox


try:
	_
except NameError:
	_ = lambda x: x


_moduleLogger = logging.getLogger(__name__)


class TripleToggleCellRenderer(gtk.CellRendererToggle):

	__gproperties__ = {
		"status": (gobject.TYPE_STRING, "Status",
		"Status", "", gobject.PARAM_READWRITE),
	}

	__gsignals__ = {
		'status_changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT, gobject.TYPE_STRING)),
	}

	def __init__(self):
		gtk.CellRendererToggle.__init__(self)
		self.set_property("activatable", True)
		self.connect('toggled', self._on_toggled)
		self.status = -1

	@gtk_toolbox.log_exception(_moduleLogger)
	def do_set_property(self, property, value):
		if getattr(self, property.name) == value or value is None:
			return

		setattr(self, property.name, value)

		if property.name == "status":
			active, inconsistent = {
				"-1": (False, True),
				"0": (False, False),
				"1": (True, False),
			}[value]
			self.set_property("active", active)
			self.set_property("inconsistent", inconsistent)

	@gtk_toolbox.log_exception(_moduleLogger)
	def do_get_property(self, property):
		return getattr(self, property.name)

	@gtk_toolbox.log_exception(_moduleLogger)
	def _on_toggled(self, widget, path):
		self.emit("status_changed", int(path), "-1")


gobject.type_register(TripleToggleCellRenderer)


class View(gtk.VBox):

	def __init__(self, db, liststorehandler, parent_window):
		self.db = db
		self.parent_window = parent_window
		self.liststorehandler = liststorehandler

		gtk.VBox.__init__(self, homogeneous = False, spacing = 0)

		logging.info("libview, init")

		self.scrolled_window = None
		self.reload_view()

	def loadList(self):
		ls = self.liststorehandler.get_liststore()
		self.treeview.set_model(ls)

	def del_active_row(self):
		path, col = self.treeview.get_cursor()
		if path is not None:
			irow = path[0]
			row_iter = self.treeview.get_model().get_iter(path)
			self.liststorehandler.del_row(irow, row_iter)

	def reload_view(self):
		# create the TreeView using liststore
		self.modelsort = gtk.TreeModelSort(self.liststorehandler.get_liststore())
		self.modelsort.set_sort_column_id(2, gtk.SORT_ASCENDING)

		self.treeview = gtk.TreeView(self.modelsort)
		self.treeview.set_headers_visible(True)
		self.treeview.set_reorderable(False)

		self.cell = range(self.liststorehandler.get_colcount())
		self.tvcolumn = range(self.liststorehandler.get_colcount())

		m = self.liststorehandler.get_unitsstore()

		for i in range(self.liststorehandler.get_colcount()):
			if i in [1, 2]:
				default = "1"
			else:
				default = "0"
			if self.db.ladeDirekt("showcol_"+str(self.liststorehandler.get_colname(i)), default) == "1":
				if i in [1]:
					self.cell[i] = TripleToggleCellRenderer()
					self.tvcolumn[i] = gtk.TreeViewColumn("", self.cell[i])
					self.cell[i].connect( 'status_changed', self._on_col_toggled)
					self.tvcolumn[i].set_attributes( self.cell[i], status = i)
				elif i in [3, 6]:
					self.cell[i] = gtk.CellRendererCombo()
					self.tvcolumn[i] = gtk.TreeViewColumn(self.liststorehandler.get_colname(i), self.cell[i])
					self.cell[i].set_property("model", m)
					self.cell[i].set_property('text-column', i)
					self.cell[i].set_property('editable', True)
					self.cell[i].connect("edited", self._on_col_edited, i)
					self.tvcolumn[i].set_attributes( self.cell[i], text = i)
				else:
					self.cell[i] = gtk.CellRendererText()
					self.tvcolumn[i] = gtk.TreeViewColumn(self.liststorehandler.get_colname(i), self.cell[i])
					self.cell[i].set_property('editable', True)
					self.cell[i].set_property('editable-set', True)
					self.cell[i].connect("edited", self._on_col_edited, i)
					self.tvcolumn[i].set_attributes(self.cell[i], text = i)

				self.cell[i].set_property('cell-background', 'lightgray')
				self.tvcolumn[i].set_sort_column_id(i)
				self.tvcolumn[i].set_resizable(True)
				self.treeview.append_column(self.tvcolumn[i])

		if self.scrolled_window is not None:
			self.scrolled_window.destroy()

		self.scrolled_window = gtk.ScrolledWindow()
		self.scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

		self.scrolled_window.add(self.treeview)
		self.pack_start(self.scrolled_window, expand = True, fill = True, padding = 0)
		self.loadList()

		self.show_all()

	@gtk_toolbox.log_exception(_moduleLogger)
	def _on_col_edited(self, cell, irow, new_text, icol = None):
		if (irow != 4):
			self.liststorehandler.update_row(irow, icol, new_text)
		else:
			print cell, irow, new_text, icol

	@gtk_toolbox.log_exception(_moduleLogger)
	def _on_col_toggled(self, widget, irow, status):
		ls = self.treeview.get_model()

		if self.liststorehandler.get_filter() == self.liststorehandler.SHOW_ACTIVE:
			if ls[irow][1] == "0":
				self.liststorehandler.update_row(irow, 1, "1")
			else:
				self.liststorehandler.update_row(irow, 1, "0")
		else:
			if ls[irow][1] == "1":
				self.liststorehandler.update_row(irow, 1, "-1")
			elif ls[irow][1] == "0":
				self.liststorehandler.update_row(irow, 1, "1")
			else:
				self.liststorehandler.update_row(irow, 1, "0")
