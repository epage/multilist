#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement

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

import os
import logging

import gtk

try:
	import hildon
	isHildon = True
except:
	isHildon = False

try:
	import osso
except ImportError:
	osso = None

import constants
import hildonize
import gtk_toolbox

import libspeichern
import search
import sqldialog
import settings
import libselection
import libview
import libliststorehandler
import libsync
import libbottombar

try:
	_
except NameError:
	_ = lambda x: x


_moduleLogger = logging.getLogger(__name__)
PROFILE_STARTUP = False


class Multilist(hildonize.get_app_class()):

	_user_data = os.path.join(os.path.expanduser("~"), ".%s" % constants.__app_name__)
	_user_settings = "%s/settings.ini" % _user_data

	def __init__(self):
		super(Multilist, self).__init__()
		self._clipboard = gtk.clipboard_get()

		logging.info('Starting Multilist')

		try:
			os.makedirs(self._user_data)
		except OSError, e:
			if e.errno != 17:
				raise

		self.db = libspeichern.Speichern()
		self.window_in_fullscreen = False #The window isn't in full screen mode initially.
		self.__isLandscape = True

		#Haupt vbox für alle Elemente
		self.window = gtk.Window()
		self.vbox = gtk.VBox(homogeneous = False, spacing = 0)

		self.selection = libselection.Selection(self.db, isHildon)
		self._search = search.Search()
		self.liststorehandler = libliststorehandler.Liststorehandler(self.db, self.selection)
		self.view = libview.View(self.db, self.liststorehandler, self.window)
		self.bottombar = libbottombar.Bottombar(self.db, self.view, isHildon)

		#Menue
		if hildonize.GTK_MENU_USED:
			fileMenu = gtk.Menu()

			menu_items = gtk.MenuItem(_("Choose database file"))
			menu_items.connect("activate", self._on_select_db, None)
			fileMenu.append(menu_items)

			menu_items = gtk.MenuItem(_("SQL history"))
			menu_items.connect("activate", self._on_view_sql_history, None)
			fileMenu.append(menu_items)

			menu_items = gtk.MenuItem(_("SQL optimize"))
			menu_items.connect("activate", self._on_optimize_sql, None)
			fileMenu.append(menu_items)

			menu_items = gtk.MenuItem(_("Sync items"))
			menu_items.connect("activate", self.sync_notes, None)
			fileMenu.append(menu_items)

			menu_items = gtk.MenuItem(_("Quit"))
			menu_items.connect("activate", self._on_destroy, None)
			fileMenu.append(menu_items)

			fileMenuItem = gtk.MenuItem(_("File"))
			fileMenuItem.show()
			fileMenuItem.set_submenu(fileMenu)

			listmenu = gtk.Menu()

			menu_items = gtk.MenuItem(_("Search"))
			menu_items.connect("activate", self._on_toggle_search)
			listmenu.append(menu_items)

			menu_items = gtk.MenuItem(_("Checkout All"))
			menu_items.connect("activate", self._on_checkout_all)
			listmenu.append(menu_items)

			menu_items = gtk.MenuItem(_("Rename List"))
			menu_items.connect("activate", self.bottombar.rename_list, None)
			listmenu.append(menu_items)

			menu_items = gtk.MenuItem(_("Rename Category"))
			menu_items.connect("activate", self.bottombar.rename_category, None)
			listmenu.append(menu_items)

			listMenuItem = gtk.MenuItem(_("List"))
			listMenuItem.show()
			listMenuItem.set_submenu(listmenu)

			viewMenu = gtk.Menu()

			menu_items = gtk.MenuItem(_("Show Active"))
			menu_items.connect("activate", self._on_toggle_filter, None)
			viewMenu.append(menu_items)

			menu_items = gtk.MenuItem(_("Settings"))
			menu_items.connect("activate", self._on_settings, None)
			viewMenu.append(menu_items)

			viewMenuItem = gtk.MenuItem(_("View"))
			viewMenuItem.show()
			viewMenuItem.set_submenu(viewMenu)

			helpMenu = gtk.Menu()
			menu_items = gtk.MenuItem(_("About"))
			helpMenu.append(menu_items)
			menu_items.connect("activate", self._on_about, None)

			helpMenuItem = gtk.MenuItem(_("Help"))
			helpMenuItem.show()
			helpMenuItem.set_submenu(helpMenu)

			menuBar = gtk.MenuBar()
			menuBar.show()
			menuBar.append (fileMenuItem)
			menuBar.append (listMenuItem)
			menuBar.append (viewMenuItem)
			# unten -> damit als letztes menuBar.append (helpMenuItem)
			#Als letztes menü
			menuBar.append (helpMenuItem)

			self.vbox.pack_start(menuBar, False, False, 0)
		else:
			menuBar = gtk.MenuBar()
			menuBar.show()
			self.vbox.pack_start(menuBar, False, False, 0)

		#add to vbox below (to get it on top)
		self.vbox.pack_end(self._search, expand = False, fill = True)
		self.vbox.pack_end(self.bottombar, expand = False, fill = True, padding = 0)
		self.vbox.pack_end(self.view, expand = True, fill = True, padding = 0)
		self.vbox.pack_end(self.selection, expand = False, fill = True, padding = 0)

		#Get the Main Window, and connect the "destroy" event
		self.window.add(self.vbox)

		self.window = hildonize.hildonize_window(self, self.window)
		hildonize.set_application_title(self.window, "%s" % constants.__pretty_app_name__)
		menuBar = hildonize.hildonize_menu(
			self.window,
			menuBar,
		)
		if hildonize.IS_FREMANTLE_SUPPORTED:
			button = hildonize.hildon.GtkRadioButton(gtk.HILDON_SIZE_AUTO, None)
			button.set_label("All")
			menuBar.add_filter(button)
			button.connect("clicked", self._on_click_menu_filter, self.liststorehandler.SHOW_ALL)
			button.set_mode(False)
			filterGroup = button

			button = hildonize.hildon.GtkRadioButton(gtk.HILDON_SIZE_AUTO, filterGroup)
			button.set_label("Active")
			menuBar.add_filter(button)
			button.connect("clicked", self._on_click_menu_filter, self.liststorehandler.SHOW_ACTIVE)
			button.set_mode(False)

			renameListButton= gtk.Button(_("Rename List"))
			renameListButton.connect("clicked", self.bottombar.rename_list)
			menuBar.append(renameListButton)

			renameCategoryButton = gtk.Button(_("Rename Category"))
			renameCategoryButton.connect("clicked", self.bottombar.rename_category)
			menuBar.append(renameCategoryButton)

			searchButton= gtk.Button(_("Search Category"))
			searchButton.connect("clicked", self._on_toggle_search)
			menuBar.append(searchButton)

			searchButton= gtk.Button(_("Settings"))
			searchButton.connect("clicked", self._on_settings)
			menuBar.append(searchButton)

			menuBar.show_all()

		if not hildonize.IS_HILDON_SUPPORTED:
			_moduleLogger.info("No hildonization support")

		if osso is not None:
			self.osso_c = osso.Context(
				constants.__app_name__,
				constants.__version__,
				False
			)
		else:
			_moduleLogger.info("No osso support")
			self._osso_c = None

		self.window.connect("delete_event", self._on_delete_event)
		self.window.connect("destroy", self._on_destroy)
		self.window.connect("key-press-event", self.on_key_press)
		self.window.connect("window-state-event", self._on_window_state_change)
		self._search.connect("search_changed", self._on_search)

		self.window.show_all()
		self._search.hide()
		self._prepare_sync_dialog()

	def _toggle_search(self):
		if self._search.get_property("visible"):
			self._search.hide()
		else:
			self._search.show()

	def set_orientation(self, orientation):
		if orientation == gtk.ORIENTATION_VERTICAL:
			hildonize.window_to_portrait(self.window)
			self.bottombar.set_orientation(gtk.ORIENTATION_VERTICAL)
			self.selection.set_orientation(gtk.ORIENTATION_VERTICAL)
			self.__isLandscape = False
		elif orientation == gtk.ORIENTATION_HORIZONTAL:
			hildonize.window_to_landscape(self.window)
			self.bottombar.set_orientation(gtk.ORIENTATION_HORIZONTAL)
			self.selection.set_orientation(gtk.ORIENTATION_HORIZONTAL)
			self.__isLandscape = True
		else:
			raise NotImplementedError(orientation)

	def get_orientation(self):
		return gtk.ORIENTATION_HORIZONTAL if self.__isLandscape else gtk.ORIENTATION_VERTICAL

	def _toggle_rotate(self):
		if self.__isLandscape:
			self.set_orientation(gtk.ORIENTATION_VERTICAL)
		else:
			self.set_orientation(gtk.ORIENTATION_HORIZONTAL)

	@gtk_toolbox.log_exception(_moduleLogger)
	def _on_checkout_all(self, widget):
		self.liststorehandler.checkout_rows()

	@gtk_toolbox.log_exception(_moduleLogger)
	def _on_search(self, widget):
		self.liststorehandler.get_liststore(self._search.get_search_pattern())

	@gtk_toolbox.log_exception(_moduleLogger)
	def _on_click_menu_filter(self, button, val):
		self.liststorehandler.set_filter(val)

	@gtk_toolbox.log_exception(_moduleLogger)
	def _on_toggle_search(self, *args):
		self._toggle_search()

	@gtk_toolbox.log_exception(_moduleLogger)
	def _on_toggle_filter(self, *args):
		if self.liststorehandler.get_filter() == self.liststorehandler.SHOW_ALL:
			self.liststorehandler.set_filter(self.liststorehandler.SHOW_ACTIVE)
		elif self.liststorehandler.get_filter() == self.liststorehandler.SHOW_ACTIVE:
			self.liststorehandler.set_filter(self.liststorehandler.SHOW_ALL)
		else:
			assert False, "Unknown"

	@gtk_toolbox.log_exception(_moduleLogger)
	def on_key_press(self, widget, event, *args):
		RETURN_TYPES = (gtk.keysyms.Return, gtk.keysyms.ISO_Enter, gtk.keysyms.KP_Enter)
		isCtrl = bool(event.get_state() & gtk.gdk.CONTROL_MASK)
		if (
			event.keyval == gtk.keysyms.F6 or
			event.keyval in RETURN_TYPES and isCtrl
		):
			# The "Full screen" hardware key has been pressed 
			if self.window_in_fullscreen:
				self.window.unfullscreen ()
			else:
				self.window.fullscreen ()
			return True
		elif event.keyval == gtk.keysyms.r and isCtrl:
			self._toggle_rotate()
			return True
		elif event.keyval == gtk.keysyms.f and isCtrl:
			self._toggle_search()
			return True
		elif (
			event.keyval in (gtk.keysyms.w, gtk.keysyms.q) and
			event.get_state() & gtk.gdk.CONTROL_MASK
		):
			self.window.destroy()
		elif event.keyval == gtk.keysyms.l and event.get_state() & gtk.gdk.CONTROL_MASK:
			with open(constants._user_logpath_, "r") as f:
				logLines = f.xreadlines()
				log = "".join(logLines)
				self._clipboard.set_text(str(log))
			return True

	@gtk_toolbox.log_exception(_moduleLogger)
	def _on_window_state_change(self, widget, event, *args):
		if event.new_window_state & gtk.gdk.WINDOW_STATE_FULLSCREEN:
			self.window_in_fullscreen = True
		else:
			self.window_in_fullscreen = False

	@gtk_toolbox.log_exception(_moduleLogger)
	def _on_sync_finished(self, data = None, data2 = None):
		self.selection.comboList_changed()
		self.selection.comboCategory_changed()
		self.liststorehandler.update_list()

	def _prepare_sync_dialog(self):
		self.sync_dialog = gtk.Dialog(_("Sync"), None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

		self.sync_dialog.set_position(gtk.WIN_POS_CENTER)
		sync = libsync.Sync(self.db, self.window, 50503)
		sync.connect("syncFinished", self._on_sync_finished)
		self.sync_dialog.vbox.pack_start(sync, True, True, 0)
		self.sync_dialog.set_size_request(500, 350)
		self.sync_dialog.vbox.show_all()

	@gtk_toolbox.log_exception(_moduleLogger)
	def sync_notes(self, widget = None, data = None):
		if self.sync_dialog is None:
			self._prepare_sync_dialog()
		self.sync_dialog.run()
		self.sync_dialog.hide()

	@gtk_toolbox.log_exception(_moduleLogger)
	def _on_settings(self, *args):
		col_dialog = gtk.Dialog(
			_("Settings"),
			self.window,
			gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
			(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
		)

		cols = settings.SettingsDialog(col_dialog.vbox, self.db, self.liststorehandler)
		col_dialog.show_all()

		resp = col_dialog.run()
		try:
			col_dialog.hide()
			if resp == gtk.RESPONSE_ACCEPT:
				logging.info("changing columns")
				cols.save(self.db)
				self.view.reload_view()
		finally:
			col_dialog.destroy()

	@gtk_toolbox.log_exception(_moduleLogger)
	def _on_destroy(self, widget = None, data = None):
		try:
			self.db.close()
			try:
				self._osso_c.close()
			except AttributeError:
				pass # Either None or close was removed (in Fremantle)
		finally:
			gtk.main_quit()

	@gtk_toolbox.log_exception(_moduleLogger)
	def _on_delete_event(self, widget, event, data = None):
		return False

	@gtk_toolbox.log_exception(_moduleLogger)
	def _on_view_sql_history(self, widget = None, data = None, data2 = None):
		sqldiag = sqldialog.SqlDialog(self.db)
		res = sqldiag.run()
		sqldiag.hide()

		try:
			if res != gtk.RESPONSE_OK:
				return
			logging.info("exporting sql")

			if not isHildon:
				dlg = gtk.FileChooserDialog(
					parent = self.window,
					action = gtk.FILE_CHOOSER_ACTION_SAVE
				)
				dlg.add_button( gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
				dlg.add_button( gtk.STOCK_OK, gtk.RESPONSE_OK)
			else:
				dlg = hildon.FileChooserDialog(self.window, gtk.FILE_CHOOSER_ACTION_SAVE)

			dlg.set_title(_("Select SQL export file"))
			exportFileResponse = dlg.run()
			try:
				if exportFileResponse == gtk.RESPONSE_OK:
					fileName = dlg.get_filename()
					sqldiag.exportSQL(fileName)
			finally:
				dlg.destroy()
		finally:
			sqldiag.destroy()

	@gtk_toolbox.log_exception(_moduleLogger)
	def _on_optimize_sql(self, widget = None, data = None, data2 = None):
		#optimiere sql
		self.db.speichereSQL("VACUUM", log = False)

	@gtk_toolbox.log_exception(_moduleLogger)
	def _on_select_db(self, widget = None, data = None, data2 = None):
		dlg = hildon.FileChooserDialog(parent=self._window, action=gtk.FILE_CHOOSER_ACTION_SAVE)

		if self.db.ladeDirekt('datenbank'):
			dlg.set_filename(self.db.ladeDirekt('datenbank'))
		dlg.set_title(_("Choose your database file"))
		resp = dlg.run()
		try:
			if resp == gtk.RESPONSE_OK:
				fileName = dlg.get_filename()
				self.db.speichereDirekt('datenbank', fileName)
				self.db.openDB()
		finally:
			dlg.destroy()

	@gtk_toolbox.log_exception(_moduleLogger)
	def _on_about(self, widget = None, data = None):
		dialog = gtk.AboutDialog()
		dialog.set_position(gtk.WIN_POS_CENTER)
		dialog.set_name(constants.__pretty_app_name__)
		dialog.set_version(constants.__version__)
		dialog.set_copyright("")
		dialog.set_website("http://axique.de/f = Multilist")
		comments = "%s is a program to handle multiple lists." % constants.__pretty_app_name__
		dialog.set_comments(comments)
		dialog.set_authors(["Christoph Wurstle <n800@axique.net>", "Ed Page <eopage@byu.net> (Blame him for the most recent bugs)"])
		dialog.run()
		dialog.destroy()


def run_multilist():
	if hildonize.IS_HILDON_SUPPORTED:
		gtk.set_application_name(constants.__pretty_app_name__)
	app = Multilist()
	if not PROFILE_STARTUP:
		gtk.main()


if __name__ == "__main__":
	logging.basicConfig(level = logging.DEBUG)
	run_multilist()
