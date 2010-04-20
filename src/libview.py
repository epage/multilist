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

import sys
import logging

import gobject
import gtk
import pango

import hildonize
import gtk_toolbox
import libliststorehandler


try:
	_
except NameError:
	_ = lambda x: x


_moduleLogger = logging.getLogger(__name__)


class TripleToggleCellRenderer(gtk.CellRendererToggle):

	__gproperties__ = {
		"status": (gobject.TYPE_STRING, "Status", "Status", "", gobject.PARAM_READWRITE),
	}

	__gsignals__ = {
		'status_changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT, gobject.TYPE_STRING)),
	}

	def __init__(self):
		gtk.CellRendererToggle.__init__(self)
		self.set_property("activatable", True)
		self.connect('toggled', self._on_toggled)
		self.status = libliststorehandler.Liststorehandler.SHOW_NEW

	@gtk_toolbox.log_exception(_moduleLogger)
	def do_set_property(self, property, value):
		if getattr(self, property.name) == value or value is None:
			return

		setattr(self, property.name, value)

		if property.name == "status":
			active, inconsistent = {
				libliststorehandler.Liststorehandler.SHOW_NEW: (False, False),
				libliststorehandler.Liststorehandler.SHOW_ACTIVE: (False, True),
				libliststorehandler.Liststorehandler.SHOW_COMPLETE: (True, False),
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


class CellRendererTriple(gtk.GenericCellRenderer):
	__gproperties__ = {
		"status": (gobject.TYPE_STRING, "Status", "Status", "", gobject.PARAM_READWRITE),
	}

	__gsignals__ = {
		'status_changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,(gobject.TYPE_INT,gobject.TYPE_STRING)),
	}

	def __init__(self):
		gtk.GenericCellRenderer.__init__(self)
		self.status = -1
		self.last_cell = None

		self.set_property('mode', gtk.CELL_RENDERER_MODE_ACTIVATABLE)
		self.set_property('visible', True)

	def do_set_property(self,property,value):
		setattr(self, property.name, value)

	def do_get_property(self, property):
		return getattr(self, property.name)

	def _get_layout(self, widget):
		'''Gets the Pango layout used in the cell in a TreeView widget.'''

		layout = pango.Layout(widget.get_pango_context())
		layout.set_width(-1) # Do not wrap text.

		layout.set_text('  ')

		return layout

	def on_get_size(self, widget, cell_area=None):
		layout = self._get_layout(widget)
		width, height = layout.get_pixel_size()

		xpad = 2
		ypad = 2

		xalign = 0
		yalign = 0.5

		x_offset = xpad
		y_offset = ypad

		if cell_area is not None:
			x_offset = xalign * (cell_area.width - width)
			x_offset = max(x_offset, xpad)
			x_offset = int(round(x_offset, 0))

			y_offset = yalign * (cell_area.height - height)
			y_offset = max(y_offset, ypad)
			y_offset = int(round(y_offset, 0))

		width = width + (xpad * 2)
		height = height + (ypad * 2)

		return x_offset, y_offset, width, height

	def on_render(self, window, widget, background_area, cell_area, expose_area, flags ):
		self.last_cell = cell_area

		x = cell_area.x
		y = cell_area.y
		width = cell_area.width
		height = cell_area.height

		if False:
			# This is how it should work but due to theme issues on Maemo, it doesn't work
			if widget.state == gtk.STATE_INSENSITIVE:
				state = gtk.STATE_INSENSITIVE
			elif flags & gtk.CELL_RENDERER_SELECTED:
				if widget.is_focus():
					state = gtk.STATE_SELECTED
				else:
					state = gtk.STATE_ACTIVE
			else:
				state = gtk.STATE_NORMAL

		if self.status == libliststorehandler.Liststorehandler.SHOW_COMPLETE:
			shadow = gtk.SHADOW_IN
			state = gtk.STATE_NORMAL
		elif self.status == libliststorehandler.Liststorehandler.SHOW_ACTIVE:
			shadow = gtk.SHADOW_ETCHED_IN
			state = gtk.STATE_NORMAL
		elif self.status == libliststorehandler.Liststorehandler.SHOW_NEW:
			shadow = gtk.SHADOW_OUT
			state = gtk.STATE_SELECTED
		else:
			raise NotImplementedError(self.status)

		widget.style.paint_check(window, state, shadow, cell_area, widget, "cellcheck",x,y,width,height)

	def on_activate(self, event, widget, path, background_area, cell_area, flags):
		self.emit("status_changed", int(path), "-1")
		return False


gobject.type_register(CellRendererTriple)


class View(gtk.VBox):

	def __init__(self, db, liststorehandler, parent_window):
		self.db = db
		self.parent_window = parent_window
		self.liststorehandler = liststorehandler

		gtk.VBox.__init__(self, homogeneous = False, spacing = 0)

		logging.info("libview, init")

		self.treeview = None
		self.scrolled_window = gtk.ScrolledWindow()
		self.scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.pack_start(self.scrolled_window, expand = True, fill = True, padding = 0)

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

		if self.treeview is not None:
			self.scrolled_window.remove(self.treeview)
		self.treeview = gtk.TreeView(self.modelsort)
		self.treeview.set_headers_visible(True)
		self.treeview.set_reorderable(False)

		self.cell = range(self.liststorehandler.get_colcount())
		self.tvcolumn = range(self.liststorehandler.get_colcount())

		m = self.liststorehandler.get_unitsstore()

		for i in range(self.liststorehandler.get_colcount()):
			if i in [1, 2]: # status, title
				default = "1"
			else:
				default = "0"
			if self.db.ladeDirekt("showcol_"+str(self.liststorehandler.get_colname(i)), default) == "1":
				if i in [1]: # status
					# HACK Hildon has theme issues with inconsistent items, so
					# we have a hacked together toggle to make it work on
					# hildon
					if hildonize.IS_HILDON_SUPPORTED:
						self.cell[i] = CellRendererTriple()
					else:
						self.cell[i] = TripleToggleCellRenderer()
					self.cell[i].connect('status_changed', self._on_col_toggled)
					self.tvcolumn[i] = gtk.TreeViewColumn("", self.cell[i])
					self.tvcolumn[i].set_attributes( self.cell[i], status = i)
				elif i in [3, 5]: # quantity, price
					self.cell[i] = gtk.CellRendererSpin()
					adjustment = gtk.Adjustment(0, -sys.float_info.max, sys.float_info.max, 1)
					self.cell[i].set_property('adjustment', adjustment)
					self.cell[i].set_property('digits', 2 if i == 5 else 0)
					self.cell[i].set_property('editable', True)
					self.cell[i].connect("edited", self._on_col_edited, i)
					self.tvcolumn[i] = gtk.TreeViewColumn(
						self.liststorehandler.get_colname(i), self.cell[i]
					)
					self.tvcolumn[i].set_attributes( self.cell[i], text = i)
				elif i in [4, 6]: # unit, priority
					self.cell[i] = gtk.CellRendererCombo()
					self.cell[i].set_property("model", m)
					self.cell[i].set_property('text-column', i)
					self.cell[i].set_property('editable', True)
					self.cell[i].connect("edited", self._on_col_edited, i)
					self.tvcolumn[i] = gtk.TreeViewColumn(
						self.liststorehandler.get_colname(i), self.cell[i]
					)
					self.tvcolumn[i].set_attributes( self.cell[i], text = i)
				else:
					self.cell[i] = gtk.CellRendererText()
					self.cell[i].set_property('editable', True)
					self.cell[i].set_property('editable-set', True)
					self.cell[i].connect("edited", self._on_col_edited, i)
					self.tvcolumn[i] = gtk.TreeViewColumn(
						self.liststorehandler.get_colname(i), self.cell[i]
					)
					self.tvcolumn[i].set_attributes(self.cell[i], text = i)

				self.tvcolumn[i].set_sort_column_id(i)
				self.tvcolumn[i].set_resizable(True)
				self.treeview.append_column(self.tvcolumn[i])

		self.scrolled_window.add(self.treeview)
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
