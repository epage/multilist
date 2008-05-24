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

#/scratchbox/login
#Xephyr :2 -host-cursor -screen 800x480x16 -dpi 96 -ac
#af-sb-init.sh start
#run-standalone.sh ./eggtimer.py
#
#https://stage.maemo.org/svn/maemo/projects/haf/trunk/
#http://www.maemo.org/platform/docs/pymaemo/pyosso_context.html
#http://maemo-hackers.org/apt/

import time
import os
import sys
import logging

try:
        import gtk
        #import gtk.glade
except:
	print "gtk import failed"
        sys.exit(1)
	
try:
	import hildon
	import osso
	isHildon=True
except:
	isHildon=False
	class hildon():
		def __init__(self):
			print "PseudoClass hildon"
		class Program():
			def __init__(self):
				print "PseudoClass hildon.Program"

#import libextdatei
import libspeichern
import libsqldialog
import libselection
import libview
import libliststorehandler
import libsync
import libbottombar

version = "0.3.0"
app_name = "multilist"

		
	

class multilistclass(hildon.Program):
		
	def on_key_press(self, widget, event, *args):
		#Hildon Fullscreen Modus
		if (isHildon==False): return
		if event.keyval == gtk.keysyms.F6: 
 			# The "Full screen" hardware key has been pressed 
 			if self.window_in_fullscreen: 
 				self.window.unfullscreen () 
 			else: 
 				self.window.fullscreen () 
		
	def on_window_state_change(self, widget, event, *args): 
		if event.new_window_state & gtk.gdk.WINDOW_STATE_FULLSCREEN: 
			self.window_in_fullscreen = True 
 		else: 
 			self.window_in_fullscreen = False 

	
	def speichereAlles(self,data=None,data2=None):
		logging.info("Speichere alles")


	def ladeAlles(self,data=None,data2=None):
		logging.info("Lade alles")
		
	def beforeSync(self,data=None,data2=None):
		logging.info("Lade alles")


	def sync_finished(self,data=None,data2=None):
		self.selection.comboList_changed()
		self.selection.comboCategory_changed()
		self.liststorehandler.update_list()
		
	
	def prepare_sync_dialog(self):
		self.sync_dialog = gtk.Dialog("Sync",None,gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,(gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
		
        	self.sync_dialog.set_position(gtk.WIN_POS_CENTER)
		sync=libsync.Sync(self.db,self.window,50503)
		sync.connect("syncFinished",self.sync_finished)
		self.sync_dialog.vbox.pack_start(sync, True, True, 0)
		self.sync_dialog.set_size_request(500,350)
		self.sync_dialog.vbox.show_all()
		sync.connect("syncFinished",self.sync_finished)
	
	
	def sync_notes(self,widget=None,data=None):
		if self.sync_dialog==None:
			self.prepare_sync_dialog()
		self.sync_dialog.run()
        	self.sync_dialog.hide()


	def show_columns_dialog(self,widget=None,data=None):
		col_dialog = gtk.Dialog("Choose columns",self.window,gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
		
        	col_dialog.set_position(gtk.WIN_POS_CENTER)
		cols=libview.Columns_dialog(self.db,self.liststorehandler)

		col_dialog.vbox.pack_start(cols, True, True, 0)
		col_dialog.set_size_request(500,350)
		col_dialog.vbox.show_all()
		
		resp=col_dialog.run()
		col_dialog.hide()
		if resp==gtk.RESPONSE_ACCEPT:
			logging.info("changing columns")
			cols.save_column_setting()
			self.view.reload_view()
			#children=self.vbox.get_children()
			#while len(children)>1:
			#	self.vbox.remove(children[1])

			#self.vbox.pack_end(self.bottombar, expand=True, fill=True, padding=0)
			#self.vbox.pack_end(view, expand=True, fill=True, padding=0)
			#self.vbox.pack_end(self.selection, expand=False, fill=True, padding=0)
			

		col_dialog.destroy()
		


	def __init__(self):
		home_dir = os.path.expanduser('~')
		dblog=os.path.join(home_dir, "multilist.log") 
		logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%a, %d %b %Y %H:%M:%S', filename=dblog,filemode='a')
		#logging.getLogger('').addHandler(console)
		
		# define a Handler which writes INFO messages or higher to the sys.stderr
		console = logging.StreamHandler()
		console.setLevel(logging.INFO)
		# set a format which is simpler for console use
		formatter = logging.Formatter('%(asctime)s  %(levelname)-8s %(message)s')
		# tell the handler to use this format
		console.setFormatter(formatter)
		# add the handler to the root logger
		logging.getLogger('').addHandler(console)
		
		logging.info('Starting Multilist')
		
		if (isHildon==True): 
			logging.info('Hildon erkannt, rufe Hildon constructor auf')
			hildon.Program.__init__(self)
				
                #Get the Main Window, and connect the "destroy" event
		if (isHildon==False):
                	self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
			self.window.set_default_size(700,500)
		else:
			self.window = hildon.Window()
			self.add_window(self.window)
			
		#print "1b: ",time.clock() 
		
                if (self.window):
			self.window.connect("delete_event", self.delete_event)
			self.window.connect("destroy", self.destroy)
			self.window.set_title("Multilist")
			
			
			
			if (isHildon==True): self.window.connect("key-press-event", self.on_key_press) 
			self.window.connect("window-state-event", self.on_window_state_change) 
 			self.window_in_fullscreen = False #The window isn't in full screen mode initially.


		self.db=libspeichern.Speichern()
		
		self.selection=libselection.Selection(self.db,isHildon)
		self.liststorehandler=libliststorehandler.Liststorehandler(self.db,self.selection)
		self.view=libview.View(self.db,self.liststorehandler,self.window)
		self.bottombar=libbottombar.Bottombar(self.db,self.view,isHildon)
		
		#Haupt vbox für alle Elemente
		self.vbox = gtk.VBox(homogeneous=False, spacing=0)
		
		
		
		#Menue
		dateimenu = gtk.Menu()
		
		menu_items = gtk.MenuItem("DB auswählen")
		dateimenu.append(menu_items)
		menu_items.connect("activate", self.select_db_dialog, None)
		
		menu_items = gtk.MenuItem("SQL History anschauen")
		dateimenu.append(menu_items)
		menu_items.connect("activate", self.view_sql_history, None)
		
		menu_items = gtk.MenuItem("SQL optimieren")
		dateimenu.append(menu_items)
		menu_items.connect("activate", self.optimizeSQL, None)
		
		menu_items = gtk.MenuItem("Sync items")
		self.prepare_sync_dialog()
		dateimenu.append(menu_items)
		menu_items.connect("activate", self.sync_notes, None)
		
		
		menu_items = gtk.MenuItem("Beenden")
		dateimenu.append(menu_items)
		menu_items.connect("activate", self.destroy, None)
		#menu_items.show()
		
		datei_menu = gtk.MenuItem("Datei")
		datei_menu.show()
		datei_menu.set_submenu(dateimenu)
		
		
		toolsmenu = gtk.Menu()
		
		
		menu_items = gtk.MenuItem("Choose columns")
		toolsmenu.append(menu_items)
		menu_items.connect("activate", self.show_columns_dialog, None)
		
		menu_items = gtk.MenuItem("Rename Category")
		toolsmenu.append(menu_items)
		menu_items.connect("activate", self.bottombar.rename_category, None)
		
		menu_items = gtk.MenuItem("Rename List")
		toolsmenu.append(menu_items)
		menu_items.connect("activate", self.bottombar.rename_list, None)
		
		tools_menu = gtk.MenuItem("Tools")
		tools_menu.show()
		tools_menu.set_submenu(toolsmenu)
		
		
		hilfemenu = gtk.Menu()
		menu_items = gtk.MenuItem("Über")
		hilfemenu.append(menu_items)
		menu_items.connect("activate", self.show_about, None)
		
		hilfe_menu = gtk.MenuItem("Hilfe")
		hilfe_menu.show()
		hilfe_menu.set_submenu(hilfemenu)
		
		menu_bar = gtk.MenuBar()
		menu_bar.show()
		menu_bar.append (datei_menu)
		menu_bar.append (tools_menu)
		# unten -> damit als letztes menu_bar.append (hilfe_menu)
		#Als letztes menü
		menu_bar.append (hilfe_menu)
		
		if (isHildon==True):
			menu = gtk.Menu() 
			for child in menu_bar.get_children():
				child.reparent(menu) 
			self.window.set_menu(menu)
			menu_bar.destroy()
		else:
			self.vbox.pack_start(menu_bar, False, False, 2)
		
		
		

		#add to vbox below (to get it on top)
		
		
		
		self.vbox.pack_end(self.bottombar, expand=False, fill=True, padding=0)
		self.vbox.pack_end(self.view, expand=True, fill=True, padding=0)
		self.vbox.pack_end(self.selection, expand=False, fill=True, padding=0)
		

		if (isHildon==True): self.osso_c = osso.Context(app_name, version, False)
		self.window.add(self.vbox)
		self.window.show_all()
		
		#print "8a"
		self.ladeAlles()
		
		
		#print "9: ",time.clock()
			
	def main(self):
		gtk.main()
		if (isHildon==True): self.osso_c.close()
		
	def destroy(self, widget=None, data=None):
		self.speichereAlles()
		self.db.close()
		gtk.main_quit()
		
		
	def delete_event(self, widget, event, data=None):
		#print "delete event occurred"
		return False
	
	def dlg_delete(self,widget,event,data=None):
		return False


	def show_about(self, widget=None,data=None):
        	dialog = gtk.AboutDialog()
        	dialog.set_position(gtk.WIN_POS_CENTER)
        	dialog.set_name(app_name)
        	dialog.set_version(version)
        	dialog.set_copyright("")
		dialog.set_website("http://axique.de/f=Multilist")
        	comments = "%s is a program to handle multiple lists." % app_name
        	dialog.set_comments(comments)        
        	dialog.run()     
        	dialog.destroy()
	
	def on_info1_activate(self,menuitem):
		self.show_about(menuitem)

  
	def view_sql_history(self,widget=None,data=None,data2=None):
		sqldiag=libsqldialog.sqlDialog(self.db)
		res=sqldiag.run()
		sqldiag.hide()
		if res==444:
			logging.info("exporting sql")
			
			if (isHildon==False):
        			dlg = gtk.FileChooserDialog(parent = self.window, action = gtk.FILE_CHOOSER_ACTION_SAVE)
				dlg.add_button( gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        			dlg.add_button( gtk.STOCK_OK, gtk.RESPONSE_OK)
			else:
				#dlg = hildon.FileChooserDialog(parent = self.window, action = gtk.FILE_CHOOSER_ACTION_SAVE)
				dlg=hildon.FileChooserDialog(self.window, gtk.FILE_CHOOSER_ACTION_SAVE)
			
			dlg.set_title("Wähle SQL-Export-Datei")
        		if dlg.run() == gtk.RESPONSE_OK:
				fileName = dlg.get_filename()
				dlg.destroy()
				sqldiag.exportSQL(fileName)
			else:
				dlg.destroy()
				
		sqldiag.destroy()

		
	def optimizeSQL(self,widget=None,data=None,data2=None):	
		#optimiere sql
		self.db.speichereSQL("VACUUM",log=False)
		
  

  
	def select_db_dialog(self,widget=None,data=None,data2=None):
		if (isHildon==False):
        		dlg = gtk.FileChooserDialog(parent = self.window, action = gtk.FILE_CHOOSER_ACTION_SAVE)
			dlg.add_button( gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        		dlg.add_button( gtk.STOCK_OK, gtk.RESPONSE_OK)
		else:
			#dlg = hildon.FileChooserDialog(parent = self.window, action = gtk.FILE_CHOOSER_ACTION_SAVE)
			dlg=hildon.FileChooserDialog(self.window, gtk.FILE_CHOOSER_ACTION_SAVE)
			
        	
        	if self.db.ladeDirekt('datenbank'):
			dlg.set_filename(self.db.ladeDirekt('datenbank'))
		dlg.set_title("Wähle Datenbank-Datei")
        	if dlg.run() == gtk.RESPONSE_OK:
			fileName = dlg.get_filename()
			self.db.speichereDirekt('datenbank',fileName)
			self.speichereAlles()
			self.db.openDB()
			self.ladeAlles()
        	dlg.destroy()
		
		
		

