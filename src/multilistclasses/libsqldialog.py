#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gobject
import time
import string
import gtk
import sys
import logging

import libspeichern 
 
 
class sqlDialog(gtk.Dialog):
	
	def exportSQL(self,filename):
		f = open(filename, 'w')
		msgstring=""
		sql="SELECT pcdatum,sql,param FROM logtable WHERE pcdatum>? ORDER BY pcdatum DESC"
		rows=self.db.ladeSQL(sql,(time.time()-2*24*3600,))
		for row in rows:
			pcdatum,sql,param = row
			datum=str(time.strftime("%d.%m.%y %H:%M:%S ", (time.localtime(pcdatum))))
			f.write( datum +"\t" + sql + "\t\t" + param+ "\n")
			
			
		f.close()
		
	
	def __init__(self,db):
		self.db=db
		
		logging.info("sqldialog, init")
		
		gtk.Dialog.__init__(self,"SQL History (der letzten 2 Tage (max. 50)):",None,gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,(gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
		
		
		self.add_button("Export", 444)
        	self.set_position(gtk.WIN_POS_CENTER)
		
		
		self.liststore = gtk.ListStore(str, str, str)

        	# create the TreeView using liststore
        	self.treeview = gtk.TreeView(self.liststore)
		
		# create a CellRenderers to render the data
        	self.cell1 = gtk.CellRendererText()
        	self.cell2 = gtk.CellRendererText()
		self.cell3 = gtk.CellRendererText()
		#self.cell1.set_property('markup', 1)
		
        	# create the TreeViewColumns to display the data
        	self.tvcolumn1 = gtk.TreeViewColumn('Datum')
        	self.tvcolumn2 = gtk.TreeViewColumn('SQL')
		self.tvcolumn3 = gtk.TreeViewColumn('Parameter')
		
        	# add columns to treeview
        	self.treeview.append_column(self.tvcolumn1)
        	self.treeview.append_column(self.tvcolumn2)
		self.treeview.append_column(self.tvcolumn3)
		
		
		self.tvcolumn1.pack_start(self.cell1, True)
        	self.tvcolumn2.pack_start(self.cell2, True)
		self.tvcolumn3.pack_start(self.cell3, True)
		
		self.tvcolumn1.set_attributes(self.cell1, text=0) #Spalten setzten hier!!!!
		self.tvcolumn2.set_attributes(self.cell2, text=1)
		self.tvcolumn3.set_attributes(self.cell3, text=2)

        	# make treeview searchable
        	#self.treeview.set_search_column(0)
		#self.tvcolumn.set_sort_column_id(0)
        	
		# Allow NOT drag and drop reordering of rows
        	self.treeview.set_reorderable(False)
		
		scrolled_window = gtk.ScrolledWindow()
		scrolled_window.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
		scrolled_window.add(self.treeview)
		#self.pack_start(scrolled_window, expand=True, fill=True, padding=0)
		
		
		self.vbox.pack_start(scrolled_window, True, True, 0)
		
  		self.vbox.show_all()
		
		msgstring=""
		sql="SELECT pcdatum,sql,param FROM logtable WHERE pcdatum>? ORDER BY pcdatum DESC"
		rows=db.ladeSQL(sql,(time.time()-3*24*3600,))
		i=0
		for row in rows:
			pcdatum,sql,param = row
			datum=str(time.strftime("%d.%m.%y %H:%M:%S ", (time.localtime(pcdatum))))
			if len(param)>100:
				param=param[:20]+" (Parameter gekürzt) "+param[20:]
			self.liststore.append([datum, sql,param])
			i+=1
			if (i>50):
				break
			
		self.set_size_request(500,400)
		
		
		
