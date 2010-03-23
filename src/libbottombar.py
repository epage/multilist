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

import gtk_toolbox

try:
	_
except NameError:
	_ = lambda x: x


_moduleLogger = logging.getLogger(__name__)


class Bottombar(gtk.VBox):

	__gsignals__ = {
	}

	def __init__(self, db, view, isHildon):
		gtk.VBox.__init__(self, homogeneous = False, spacing = 3)

		self.db = db
		self.isHildon = isHildon
		self.view = view

		_moduleLogger.info("libBottomBar, init")

		buttonHBox = gtk.HBox()
		self.pack_start(buttonHBox, expand = False, fill = True, padding = 3)

		button = gtk.Button(stock = gtk.STOCK_ADD)
		button.connect("clicked", self.new_item, None)
		buttonHBox.pack_start(button, expand = True, fill = True, padding = 3)

		button = gtk.Button(stock = gtk.STOCK_DELETE)
		button.connect("clicked", self.del_item, None)
		buttonHBox.pack_start(button, expand = True, fill = True, padding = 3)

	@gtk_toolbox.log_exception(_moduleLogger)
	def new_item(self, widget = None, data1 = None, data2 = None):
		dialog = gtk.Dialog(
			_("New item name:"),
			None,
			gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
			(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
		)

		entryKlasse = gtk.Entry()
		entryKlasse.set_text("")
		dialog.vbox.pack_start(entryKlasse, True, True, 0)

		dialog.vbox.show_all()
		if dialog.run() == gtk.RESPONSE_ACCEPT:
			self.view.liststorehandler.add_row(entryKlasse.get_text())
		dialog.destroy()

	@gtk_toolbox.log_exception(_moduleLogger)
	def del_item(self, widget = None, data1 = None, data2 = None):
		path, col = self.view.treeview.get_cursor()
		if path is None:
			mbox = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, _("No item selected!"))
			response = mbox.run()
			mbox.hide()
			mbox.destroy()
			return

		mbox = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, _("Delete current item?"))
		response = mbox.run()
		mbox.hide()
		mbox.destroy()
		if response == gtk.RESPONSE_YES:
			self.view.del_active_row()

	def rename_category(self, widget = None, data1 = None, data2 = None):
		dialog = gtk.Dialog(
			_("New category name:"),
			None,
			gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
			(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
		)

		entryKlasse = gtk.Entry()
		entryKlasse.set_text(self.view.liststorehandler.selection.get_category())
		dialog.vbox.pack_start(entryKlasse, True, True, 0)

		dialog.vbox.show_all()
		if dialog.run() == gtk.RESPONSE_ACCEPT:
			_moduleLogger.info("new category name "+entryKlasse.get_text())
			self.view.liststorehandler.rename_category(entryKlasse.get_text())
		else:
			pass
		dialog.destroy()

	def rename_list(self, widget = None, data1 = None, data2 = None):
		dialog = gtk.Dialog(
			_("New list name:"),
			None,
			gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
			(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
		)

		dialog.set_position(gtk.WIN_POS_CENTER)
		entryKlasse = gtk.Entry()
		entryKlasse.set_text(self.view.liststorehandler.selection.get_list())
		dialog.vbox.pack_start(entryKlasse, True, True, 0)

		dialog.vbox.show_all()
		if dialog.run() == gtk.RESPONSE_ACCEPT:
			_moduleLogger.info("new list name "+entryKlasse.get_text())
			self.view.liststorehandler.rename_list(entryKlasse.get_text())
		else:
			pass
		dialog.destroy()
