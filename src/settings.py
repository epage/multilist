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

import hildonize


try:
	_
except NameError:
	_ = lambda x: x


_moduleLogger = logging.getLogger(__name__)


class SettingsDialog(object):

	def __init__(self, parent, db, liststorehandler):
		self.__listStore = liststorehandler

		self.__columnsSection = gtk.VBox()
		for i, name in enumerate(self._iter_columns()):
			checkbutton = gtk.CheckButton(name)

			if i in [0, 1]:
				default = "1"
			else:
				default = "0"
			if db.ladeDirekt("showcol_"+name, default) == "1":
				checkbutton.set_active(True)

			self.__columnsSection.pack_start(checkbutton)

		columnsFrame = gtk.Frame(_("Visible Columns"))
		columnsFrame.add(self.__columnsSection)

		self.__rotationSection = gtk.VBox()

		self.__isPortraitCheckbutton = gtk.CheckButton(_("Portrait Mode"))
		self.__rotationSection.pack_start(self.__isPortraitCheckbutton)

		rotationFrame = gtk.Frame(_("Rotation"))
		rotationFrame.add(self.__rotationSection)

		settingsBox = gtk.VBox()
		settingsBox.pack_start(rotationFrame)
		settingsBox.pack_start(columnsFrame)
		settingsView = gtk.Viewport()
		settingsView.add(settingsBox)
		settingsScrollView = gtk.ScrolledWindow()
		settingsScrollView.add(settingsView)
		settingsScrollView.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		parent.pack_start(settingsScrollView)

		settingsScrollView = hildonize.hildonize_scrollwindow(settingsScrollView)

	def set_portrait_state(self, isPortrait):
		self.__isPortraitCheckbutton.set_active(isPortrait)

	def is_portrait(self):
		return self.__isPortraitCheckbutton.get_active()

	def is_col_selected(self, icol):
		children = self.__columnsSection.get_children()
		if icol < len(children):
			return children[icol].get_active()
		else:
			return None

	def save(self, db):
		for i, name in enumerate(self._iter_columns()):
			if self.is_col_selected(i) == True:
				db.speichereDirekt("showcol_"+name, "1")
			else:
				db.speichereDirekt("showcol_"+name, "0")

	def _iter_columns(self):
		for i in xrange(self.__listStore.get_colcount()):
			name = self.__listStore.get_colname(i)
			assert name is not None
			if name == "uid":
				continue

			yield name
