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

import libspeichern
import sqldialog
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

		#Haupt vbox für alle Elemente
		self.window = gtk.Window()
		self.vbox = gtk.VBox(homogeneous = False, spacing = 0)

		self.selection = libselection.Selection(self.db, isHildon)
		self.liststorehandler = libliststorehandler.Liststorehandler(self.db, self.selection)
		self.view = libview.View(self.db, self.liststorehandler, self.window)
		self.bottombar = libbottombar.Bottombar(self.db, self.view, isHildon)

		#Menue
		if hildonize.GTK_MENU_USED:
			dateimenu = gtk.Menu()

			menu_items = gtk.MenuItem(_("Choose database file"))
			dateimenu.append(menu_items)
			menu_items.connect("activate", self.select_db_dialog, None)

			menu_items = gtk.MenuItem(_("SQL history"))
			dateimenu.append(menu_items)
			menu_items.connect("activate", self.view_sql_history, None)

			menu_items = gtk.MenuItem(_("SQL optimize"))
			dateimenu.append(menu_items)
			menu_items.connect("activate", self.optimizeSQL, None)

			menu_items = gtk.MenuItem(_("Sync items"))
			dateimenu.append(menu_items)
			menu_items.connect("activate", self.sync_notes, None)

			menu_items = gtk.MenuItem(_("Quit"))
			dateimenu.append(menu_items)
			menu_items.connect("activate", self.destroy, None)
			#menu_items.show()

			datei_menu = gtk.MenuItem(_("File"))
			datei_menu.show()
			datei_menu.set_submenu(dateimenu)

			toolsmenu = gtk.Menu()

			menu_items = gtk.MenuItem(_("Choose columns"))
			toolsmenu.append(menu_items)
			menu_items.connect("activate", self.show_columns_dialog, None)

			menu_items = gtk.MenuItem(_("Rename Category"))
			toolsmenu.append(menu_items)
			menu_items.connect("activate", self.bottombar.rename_category, None)

			menu_items = gtk.MenuItem(_("Rename List"))
			toolsmenu.append(menu_items)
			menu_items.connect("activate", self.bottombar.rename_list, None)

			tools_menu = gtk.MenuItem(_("Tools"))
			tools_menu.show()
			tools_menu.set_submenu(toolsmenu)

			hilfemenu = gtk.Menu()
			menu_items = gtk.MenuItem(_("About"))
			hilfemenu.append(menu_items)
			menu_items.connect("activate", self.show_about, None)

			hilfe_menu = gtk.MenuItem(_("Help"))
			hilfe_menu.show()
			hilfe_menu.set_submenu(hilfemenu)

			menu_bar = gtk.MenuBar()
			menu_bar.show()
			menu_bar.append (datei_menu)
			menu_bar.append (tools_menu)
			# unten -> damit als letztes menu_bar.append (hilfe_menu)
			#Als letztes menü
			menu_bar.append (hilfe_menu)

			self.vbox.pack_start(menu_bar, False, False, 0)
		else:
			menuBar = gtk.MenuBar()
			menuBar.show()
			self.vbox.pack_start(menuBar, False, False, 0)

		#add to vbox below (to get it on top)
		self.vbox.pack_end(self.bottombar, expand = False, fill = True, padding = 0)
		self.vbox.pack_end(self.view, expand = True, fill = True, padding = 0)
		self.vbox.pack_end(self.selection, expand = False, fill = True, padding = 0)

		#Get the Main Window, and connect the "destroy" event
		self.window.add(self.vbox)

		self.window = hildonize.hildonize_window(self, self.window)
		hildonize.set_application_title(self.window, "%s" % constants.__pretty_app_name__)
		menu_bar = hildonize.hildonize_menu(
			self.window,
			menu_bar,
		)
		if hildonize.IS_FREMANTLE_SUPPORTED:
			pass

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

		self.window.connect("delete_event", self.delete_event)
		self.window.connect("destroy", self.destroy)
		self.window.connect("key-press-event", self.on_key_press)
		self.window.connect("window-state-event", self.on_window_state_change)

		self.window.show_all()
		self.prepare_sync_dialog()
		self.ladeAlles()

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
		#elif event.keyval == gtk.keysyms.f and isCtrl:
		#	self._toggle_search()
		#	return True
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

	def on_window_state_change(self, widget, event, *args):
		if event.new_window_state & gtk.gdk.WINDOW_STATE_FULLSCREEN:
			self.window_in_fullscreen = True
		else:
			self.window_in_fullscreen = False

	def speichereAlles(self, data = None, data2 = None):
		logging.info("Speichere alles")

	def ladeAlles(self, data = None, data2 = None):
		logging.info("Lade alles")

	def beforeSync(self, data = None, data2 = None):
		logging.info("Lade alles")

	def sync_finished(self, data = None, data2 = None):
		self.selection.comboList_changed()
		self.selection.comboCategory_changed()
		self.liststorehandler.update_list()

	def prepare_sync_dialog(self):
		self.sync_dialog = gtk.Dialog(_("Sync"), None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

		self.sync_dialog.set_position(gtk.WIN_POS_CENTER)
		sync = libsync.Sync(self.db, self.window, 50503)
		sync.connect("syncFinished", self.sync_finished)
		self.sync_dialog.vbox.pack_start(sync, True, True, 0)
		self.sync_dialog.set_size_request(500, 350)
		self.sync_dialog.vbox.show_all()
		sync.connect("syncFinished", self.sync_finished)

	def sync_notes(self, widget = None, data = None):
		if self.sync_dialog == None:
			self.prepare_sync_dialog()
		self.sync_dialog.run()
		self.sync_dialog.hide()

	def show_columns_dialog(self, widget = None, data = None):
		col_dialog = gtk.Dialog(_("Choose columns"), self.window, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

		col_dialog.set_position(gtk.WIN_POS_CENTER)
		cols = libview.Columns_dialog(self.db, self.liststorehandler)

		col_dialog.vbox.pack_start(cols, True, True, 0)
		col_dialog.set_size_request(500, 350)
		col_dialog.vbox.show_all()

		resp = col_dialog.run()
		col_dialog.hide()
		if resp == gtk.RESPONSE_ACCEPT:
			logging.info("changing columns")
			cols.save_column_setting()
			self.view.reload_view()
			#children = self.vbox.get_children()
			#while len(children)>1:
			#	self.vbox.remove(children[1])

			#self.vbox.pack_end(self.bottombar, expand = True, fill = True, padding = 0)
			#self.vbox.pack_end(view, expand = True, fill = True, padding = 0)
			#self.vbox.pack_end(self.selection, expand = False, fill = True, padding = 0)

		col_dialog.destroy()

	def destroy(self, widget = None, data = None):
		try:
			self.speichereAlles()
			self.db.close()
			try:
				self._osso_c.close()
			except AttributeError:
				pass # Either None or close was removed (in Fremantle)
		finally:
			gtk.main_quit()

	def delete_event(self, widget, event, data = None):
		#print "delete event occurred"
		return False

	def dlg_delete(self, widget, event, data = None):
		return False

	def show_about(self, widget = None, data = None):
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

	def on_info1_activate(self, menuitem):
		self.show_about(menuitem)

	def view_sql_history(self, widget = None, data = None, data2 = None):
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

	def optimizeSQL(self, widget = None, data = None, data2 = None):
		#optimiere sql
		self.db.speichereSQL("VACUUM", log = False)

	def select_db_dialog(self, widget = None, data = None, data2 = None):
		if (isHildon == False):
			dlg = gtk.FileChooserDialog(parent = self.window, action = gtk.FILE_CHOOSER_ACTION_SAVE)
			dlg.add_button( gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
			dlg.add_button( gtk.STOCK_OK, gtk.RESPONSE_OK)
		else:
			#dlg = hildon.FileChooserDialog(parent = self.window, action = gtk.FILE_CHOOSER_ACTION_SAVE)
			dlg = hildon.FileChooserDialog(self.window, gtk.FILE_CHOOSER_ACTION_SAVE)

		if self.db.ladeDirekt('datenbank'):
			dlg.set_filename(self.db.ladeDirekt('datenbank'))
		dlg.set_title(_("Choose your database file"))
		if dlg.run() == gtk.RESPONSE_OK:
			fileName = dlg.get_filename()
			self.db.speichereDirekt('datenbank', fileName)
			self.speichereAlles()
			self.db.openDB()
			self.ladeAlles()
		dlg.destroy()


def run_multilist():
	if hildonize.IS_HILDON_SUPPORTED:
		gtk.set_application_name(constants.__pretty_app_name__)
	app = Multilist()
	if not PROFILE_STARTUP:
		gtk.main()


if __name__ == "__main__":
	logging.basicConfig(level = logging.DEBUG)
	run_multilist()
