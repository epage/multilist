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


class Liststorehandler(object):

	SHOW_ALL = "all"
	SHOW_NEW = "-1"
	SHOW_ACTIVE = "0"
	SHOW_COMPLETE = "1"
	ALL_FILTERS = (SHOW_ALL, SHOW_NEW, SHOW_ACTIVE, SHOW_COMPLETE)

	def __init__(self, db, selection):
		self.db = db
		self.__filter = self.SHOW_ALL
		self.liststore = None
		self.unitsstore = None
		self.selection = selection
		self.collist = ("uid", "status", "title", "quantity", "unit", "price", "priority", "date", "private", "stores", "note", "custom1", "custom2")

		sql = "CREATE TABLE items (uid TEXT, list TEXT, category TEXT, status TEXT, title TEXT, quantity TEXT, unit TEXT, price TEXT, priority TEXT, date TEXT, pcdate TEXT, private TEXT, stores TEXT, note TEXT, custom1 TEXT, custom2 TEXT)"
		self.db.speichereSQL(sql)

		self.selection.load()
		self.selection.connect("changed", self.update_list)
		#self.selection.connect("changedCategory", self.update_category)

	def set_filter(self, filter):
		assert filter in self.ALL_FILTERS
		self.__filter = filter
		self.update_list()

	def get_filter(self):
		return self.__filter

	def get_unitsstore(self):
		if self.unitsstore is None:
			self.unitsstore = gtk.ListStore(str, str, str, str, str,  str, str, str, str, str, str, str, str)
		self.unitsstore.clear()
		#row(3) quantities
		#row 4 units
		#row 6 priority
		self.unitsstore.append(["-1", "-1", "", "", "", "", "", "", "", "", "", "", ""])
		self.unitsstore.append(["-1", "-1", "", "1", "g", "", "0", "", "", "", "", "", ""])
		self.unitsstore.append(["-1", "-1", "", "2", "kg", "", "1", "", "", "", "", "", ""])
		self.unitsstore.append(["-1", "-1", "", "3", "liter", "", "2", "", "", "", "", "", ""])
		self.unitsstore.append(["-1", "-1", "", "4", "packs", "", "3", "", "", "", "", "", ""])
		self.unitsstore.append(["-1", "-1", "", "5", "", "", "4", "", "", "", "", "", ""])
		self.unitsstore.append(["-1", "-1", "", "6", "", "", "5", "", "", "", "", "", ""])
		self.unitsstore.append(["-1", "-1", "", "7", "", "", "6", "", "", "", "", "", ""])
		self.unitsstore.append(["-1", "-1", "", "8", "", "", "7", "", "", "", "", "", ""])
		self.unitsstore.append(["-1", "-1", "", "9", "", "", "8", "", "", "", "", "", ""])
		self.unitsstore.append(["-1", "-1", "", "", "", "", "9", "", "", "", "", "", ""])

		return self.unitsstore

	def __calculate_status(self):
		if self.__filter == self.SHOW_ALL:
			status = self.SHOW_NEW
		else:
			status = self.__filter
		return status

	def get_liststore(self, titlesearch = ""):
		if (self.liststore == None):
			self.liststore = gtk.ListStore(str, str, str, str, str,  str, str, str, str, str, str, str, str)
		self.liststore.clear()

		titlesearch = titlesearch+"%"

		if self.__filter != self.SHOW_ALL:
			status = self.__calculate_status()
			sql = "SELECT uid, status, title, quantity, unit, price, priority, date, private, stores, note, custom1, custom2 FROM items WHERE list = ? AND category LIKE ? AND status = ? AND title like ? ORDER BY category, status, title"
			rows = self.db.ladeSQL(sql, (self.selection.get_list(), self.selection.get_category(True), status, titlesearch))
		else:
			sql = "SELECT uid, status, title, quantity, unit, price, priority, date, private, stores, note, custom1, custom2 FROM items WHERE list = ? AND category LIKE ? AND title LIKE ? ORDER BY category, title ASC"
			rows = self.db.ladeSQL(sql, (self.selection.get_list(), self.selection.get_category(True), titlesearch))

		if rows is not None:
			for row in rows:
				uid, status, title, quantity, unit, price, priority, date, private, stores, note, custom1, custom2 = row
				if unit == None:
					pass
					#unit = ""
				self.liststore.append([uid, status, title, quantity, unit, price, priority, date, private, stores, note, custom1, custom2])

		return self.liststore

	def emptyValueExists(self):
		for child in self.liststore:
			if child[2] == "":
				return True
		return False

	def update_row(self, irow, icol, new_text):
		if -1 < irow and self.liststore[irow][0] != "-1" and self.liststore[irow][0] is not None:
			sql = "UPDATE items SET "+self.collist[icol]+" = ? WHERE uid = ?"
			self.db.speichereSQL(sql, (new_text, self.liststore[irow][0]), rowid = self.liststore[irow][0])

			_moduleLogger.info("Updated row: "+self.collist[icol]+" new text "+new_text+" Titel: "+str(self.liststore[irow][2])+" with uid "+str(self.liststore[irow][0]))

			self.liststore[irow][icol] = new_text
		else:
			_moduleLogger.warning("update_row: row does not exist")
			return

	def checkout_rows(self):
		sql = "UPDATE items SET status = ? WHERE list = ? AND category LIKE ? AND status = ?"
		self.db.speichereSQL(sql, (self.SHOW_NEW, self.selection.get_list(), self.selection.get_category(True), self.SHOW_COMPLETE))
		for i in range(len(self.liststore)):
			if self.liststore[i][1] == self.SHOW_COMPLETE:
				self.liststore[i][1] = self.SHOW_NEW

	def add_row(self, title = ""):
		status = self.__calculate_status()
		import uuid
		uid = str(uuid.uuid4())
		sql = "INSERT INTO items (uid, list, category, status, title) VALUES (?, ?, ?, ?, ?)"
		self.db.speichereSQL(sql, (uid, self.selection.get_list(), self.selection.get_category(), status, title), rowid = uid)
		_moduleLogger.info("Insertet row: status = "+status+" with uid "+str(uid))

		self.liststore.append([uid, status, title, " ", "", "", "", "", "", "", "", "", ""])
		self.selection.comboLists_check_for_update()

	def del_row(self, irow, row_iter):
		uid = self.liststore[irow][0]
		self.liststore.remove(row_iter)
		sql = "DELETE FROM items WHERE uid = ?"
		self.db.speichereSQL(sql, (uid, ))

	def get_colname(self, i):
		if i < len(self.collist):
			return self.collist[i]
		else:
			return None

	def get_colcount(self):
		return len(self.collist)

	def rename_category(self, new_name):
		sql = "UPDATE items SET category = ? WHERE list = ? AND category = ?"
		self.db.speichereSQL(sql, (new_name, self.selection.get_list(), self.selection.get_category()))
		self.selection.update_categories()
		self.selection.set_category(new_name)

	def rename_list(self, new_name):
		sql = "UPDATE items SET list = ? WHERE list = ?"
		self.db.speichereSQL(sql, (new_name, self.selection.get_list(), ))
		self.selection.load()
		self.selection.set_list(new_name)

	#@gtk_toolbox.log_exception(_moduleLogger)
	#def update_category(self, widget = None, data = None, data2 = None, data3 = None):
	#	self.get_liststore()

	@gtk_toolbox.log_exception(_moduleLogger)
	def update_list(self, widget = None, data = None, data2 = None, data3 = None):
		self.get_liststore()
