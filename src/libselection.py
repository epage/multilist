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

import gobject
import gtk

import gtk_toolbox
import hildonize

try:
	_
except NameError:
	_ = lambda x: x


_moduleLogger = logging.getLogger(__name__)


class Selection(gtk.HBox):

	__gsignals__ = {
		'changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING, gobject.TYPE_STRING)),
		#'changedCategory': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING, gobject.TYPE_STRING))
	}

	def __init__(self, db, isHildon):
		gtk.HBox.__init__(self, homogeneous = False, spacing = 3)

		self.db = db
		self.isHildon = isHildon

		_moduleLogger.info("libSelection, init")

		label = gtk.Label(_("List:"))
		self.pack_start(label, expand = False, fill = True, padding = 0)

		self.__lists = []
		self.__listButton = gtk.Button("")
		self.__listButton.connect("clicked", self._on_list_selector)
		self.pack_start(self.__listButton, expand = True, fill = True, padding = 0)

		label = gtk.Label(_("  Category:"))
		self.pack_start(label, expand = False, fill = True, padding = 0)

		self.__categories = []
		self.__categoryButton = gtk.Button("")
		self.__categoryButton.connect("clicked", self._on_category_selector)
		self.pack_start(self.__categoryButton, expand = True, fill = True, padding = 0)

	def load(self):
		del self.__lists[:]

		sql = "SELECT DISTINCT list FROM items ORDER BY list"
		rows = self.db.ladeSQL(sql)
		if rows is not None:
			for row in rows:
				self.__lists.append(row[0])
		else:
			self.__lists.append("default")

		s = self.db.ladeDirekt("comboListText")
		if s != "":
			self.__listButton.set_label(s)
		else:
			self.__listButton.set_label(self.__lists[0])

		self.update_categories()

	@gtk_toolbox.log_exception(_moduleLogger)
	def _on_category_selector(self, *args):
		window = gtk_toolbox.find_parent_window(self)
		userSelection = hildonize.touch_selector_entry(
			window,
			"Categories",
			self.__categories,
			self.__categoryButton.get_label(),
		)
		self.set_category(userSelection)
		self.emit("changed", "category", "")
		self.db.speichereDirekt("comboCategoryText"+self.__listButton.get_label(), self.__categoryButton.get_label())
		self.update_categories()

	@gtk_toolbox.log_exception(_moduleLogger)
	def _on_list_selector(self, *args):
		window = gtk_toolbox.find_parent_window(self)
		userSelection = hildonize.touch_selector_entry(
			window,
			"Lists",
			self.__lists,
			self.__listButton.get_label(),
		)
		self.set_list(userSelection)

		self.update_categories()

		self.emit("changed", "list", "")
		self.db.speichereDirekt("comboListText", self.__listButton.get_label())

	def update_categories(self):
		del self.__categories[:]

		sql = "SELECT DISTINCT category FROM items WHERE list = ? ORDER BY category"
		rows = self.db.ladeSQL(sql, (self.get_list(), ))

		self.__categories.append(_("all"))
		if rows is not None:
			for row in rows:
				if (row[0] != _("all")):
					self.__categories.append(row[0])

		s = self.db.ladeDirekt("comboCategoryText"+self.__listButton.get_label())
		if len(s)>0:
			self.__categoryButton.set_label(s)
		else:
			self.__categoryButton.set_label(self.__categories[0])

	def comboLists_check_for_update(self):
		categoryName = self.__categoryButton.get_label()
		if categoryName not in self.__categories:
			self.__categories.append(categoryName)

		listName = self.__listButton.get_label()
		if listName not in self.__lists:
			self.__lists.append(listName)

	def lade(self):
		_moduleLogger.warning("Laden der aktuellen position noch nicht implementiert")

	def speichere(self):
		_moduleLogger.warning("Speichern der aktuellen position noch nicht implementiert")

	def getIsHildon(self):
		return self.isHildon

	def get_category(self, select = False):
		s = self.__categoryButton.get_label()
		if s == _("all"):
			if not select:
				return "undefined"
			else:
				return "%"
		else:
			return s

	def set_category(self, category):
		# @bug the old code might have relied on this firing a combo change event
		self.__categoryButton.set_label(category)

	def set_list(self, listname):
		# @bug the old code might have relied on this firing a combo change event
		self.__listButton.set_label(listname)

	def get_list(self):
		return self.__listButton.get_label()
