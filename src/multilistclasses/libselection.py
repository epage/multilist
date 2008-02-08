#!/usr/bin/env python
# -*- coding: utf-8 -*- 


import gobject
import time
import logging

import gtk

class Selection(gtk.HBox):
	
	__gsignals__ = {
 		'changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,(gobject.TYPE_STRING,gobject.TYPE_STRING)),
		#'changedCategory': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,(gobject.TYPE_STRING,gobject.TYPE_STRING))
 	}

	def load(self):
		model=self.comboList.get_model()
		model.clear()
		#self.comboList.remove(0)
			
		
		sql="SELECT DISTINCT list FROM items ORDER BY list"
		rows=self.db.ladeSQL(sql)
		if ((rows!=None)and(len(rows)>0)):
			for row in rows:
				self.comboList.append_text(row[0])
		else:
			self.comboList.append_text("default")
			
		s=self.db.ladeDirekt("comboListText")
		if s!="":
			self.comboList.get_child().set_text(s)
		else:
			self.comboList.set_active(0)

	def comboList_changed(self, widget=None, data=None):
		#self.comboCategory.set_model(None)
		#print "reload categories"
		while len(self.comboCategory.get_model())>0:
			self.comboCategory.remove_text(0)
		
		sql="SELECT DISTINCT category FROM items WHERE list=? ORDER BY category"
		rows=self.db.ladeSQL(sql,(self.get_list(),))
		
		self.comboCategory.append_text("all")
		if ((rows!=None)and(len(rows)>0)):
			for row in rows:
				if (row[0]!="all"):
					self.comboCategory.append_text(row[0])
		
		s=self.db.ladeDirekt("comboCategoryText"+self.comboList.get_child().get_text())
		if len(s)>0:
			self.comboCategory.get_child().set_text(s)
		else:
			self.comboCategory.set_active(0)
		
		self.emit("changed","list","")
		self.db.speichereDirekt("comboListText",self.comboList.get_child().get_text())
		

		
	def comboCategory_changed(self, widget=None, data=None):
		#logging.info("Klasse geaendert zu ")
		#self.hauptRegister.set_current_page(0)
		self.emit("changed","category","")
		if self.comboCategory.get_active()>-1:
			self.db.speichereDirekt("comboCategoryText"+self.comboList.get_child().get_text(),self.comboCategory.get_child().get_text())
		
	def radioActive_changed(self, widget, data=None):
		self.emit("changed","radio","")

	def comboLists_check_for_update(self):
		if self.comboCategory.get_active()==-1:
			model=self.comboCategory.get_model()
			found=False
			cat=self.get_category()
			for x in model:
				if x[0]==cat:
					found=True
			if found==False:
				self.comboCategory.append_text(self.get_category())
				self.comboCategory.set_active(len(self.comboCategory.get_model())-1)
		if self.comboList.get_active()==-1:
			model=self.comboList.get_model()
			found=False
			list=self.get_list()
			for x in model:
				if x[0]==list:
					found=True
			if found==False:
				self.comboList.append_text(self.get_list())
				self.comboList.set_active(len(self.comboList.get_model())-1)
		

	def lade(self):
		logging.warning("Laden der aktuellen position noch nicht implementiert")

	
	def speichere(self):
		logging.warning("Speichern der aktuellen position noch nicht implementiert")
	
	
	def getIsHildon(self):
		return self.isHildon
	
	def get_category(self,select=False):
		s=self.comboCategory.get_child().get_text()
		if s=="all":
			if (select==False):
				return "undefined"
			else:
				return "%"
		else:
			return s
	def set_category(self,category):
		self.comboCategory.get_child().set_text(category)
			
	def set_list(self,listname):
		self.comboList.get_child().set_text(listname)
		
	def get_list(self):
		return self.comboList.get_child().get_text()


	
	def get_status(self):
		#return self.comboCategory.get_child().get_text()
		if self.radio_all.get_active()==True:
			return "-1"
		else:
			return "0"
		
	
	def __init__(self,db,isHildon):
		gtk.HBox.__init__(self,homogeneous=False, spacing=3)
		
		self.db=db
		self.isHildon=isHildon
		
		logging.info("libSelection, init")
			
		
		label=gtk.Label("List:")
		self.pack_start(label, expand=False, fill=True, padding=0)
		
		self.comboList = gtk.combo_box_entry_new_text()
		self.comboList.set_size_request(180,-1)
		self.pack_start(self.comboList, expand=False, fill=True, padding=0)
			
		label=gtk.Label("  Category:")
		self.pack_start(label, expand=False, fill=True, padding=0)
		
		self.comboCategory = gtk.combo_box_entry_new_text()
		self.comboCategory.set_size_request(180,-1)
		self.pack_start(self.comboCategory, expand=False, fill=True, padding=0)
		
		self.comboList.connect("changed", self.comboList_changed, None)
		self.comboCategory.connect("changed", self.comboCategory_changed, None)
		
		label=gtk.Label("  View:")
		self.pack_start(label, expand=False, fill=True, padding=0)
		
		self.radio_all=gtk.RadioButton(group=None, label="All", use_underline=True)
		self.pack_start(self.radio_all, expand=False, fill=True, padding=0)
		self.radio_active=gtk.RadioButton(group=self.radio_all, label="Active", use_underline=True)
		self.pack_start(self.radio_active, expand=False, fill=True, padding=0)
		self.radio_all.connect("toggled",self.radioActive_changed, None)
		
		
		