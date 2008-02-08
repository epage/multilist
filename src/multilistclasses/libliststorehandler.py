#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import gtk
import gobject
import libspeichern
import logging


class Liststorehandler():
	
	def get_unitsstore(self):
		if (self.unitsstore==None):
			self.unitsstore=gtk.ListStore(str, str, str,str,str,  str,str, str, str,str, str, str,str)
		self.unitsstore.clear()
		#row(3) quantities
		#row 4 units
		#row 6 priority
		self.unitsstore.append(["-1","-1","","","","","","","","","","",""])	
		self.unitsstore.append(["-1","-1","","1","g","","0","","","","","",""])	
		self.unitsstore.append(["-1","-1","","2","kg","","1","","","","","",""])	
		self.unitsstore.append(["-1","-1","","3","liter","","2","","","","","",""])	
		self.unitsstore.append(["-1","-1","","4","packs","","3","","","","","",""])	
		self.unitsstore.append(["-1","-1","","5","","","4","","","","","",""])	
		self.unitsstore.append(["-1","-1","","6","","","5","","","","","",""])	
		self.unitsstore.append(["-1","-1","","7","","","6","","","","","",""])	
		self.unitsstore.append(["-1","-1","","8","","","7","","","","","",""])	
		self.unitsstore.append(["-1","-1","","9","","","8","","","","","",""])	
		self.unitsstore.append(["-1","-1","","","","","9","","","","","",""])	
		
		return self.unitsstore
		
		
	
	
	def get_liststore(self,titlesearch=""):
		if (self.liststore==None):
			self.liststore=gtk.ListStore(str, str, str,str,str,  str,str, str, str,str, str, str,str)
		self.liststore.clear()
		
		titlesearch=titlesearch+"%"
		
		
		if (self.selection.get_status()=="0"): #only 0 and 1 (active items)
			sql="SELECT uid,status,title,quantitiy,unit,price,priority,date,private,stores,note,custom1,custom2 FROM items WHERE list=? AND category LIKE ? AND status>=? AND title like ? ORDER BY category, status, title"
			rows=self.db.ladeSQL(sql,(self.selection.get_list(),self.selection.get_category(True),self.selection.get_status(),titlesearch))
		else:
			sql="SELECT uid,status,title,quantitiy,unit,price,priority,date,private,stores,note,custom1,custom2 FROM items WHERE list=? AND category LIKE ? AND title LIKE ? ORDER BY category, title ASC"
			rows=self.db.ladeSQL(sql,(self.selection.get_list(),self.selection.get_category(True),titlesearch))
			
		#print rows
		if ((rows!=None)and(len(rows)>0)):
			for row in rows:
				uid,status,title,quantitiy,unit,price,priority,date,private,stores,note,custom1,custom2 = row
				if unit==None:
					pass
					#unit=""
				self.liststore.append([uid,status,title,quantitiy,unit,price,priority,date,private,stores,note,custom1,custom2])
			#else:
			#self.liststore.append(["-1","-1",""," ","","","","","","","","",""])	
		#import uuid
		#self.liststore.append(["-1","-1","","","","","","","","","","",""])
		
		return self.liststore
	
	
	def emptyValueExists(self):
		for child in self.liststore:
			if child[2]=="":
				return True
		return False
		
	

	def update_row(self,irow,icol,new_text):
		#print "liststore 1"
		#for x in self.liststore:
		#	print x[0],x[2]
		
		if (irow>-1)and(self.liststore[irow][0]!="-1")and(self.liststore[irow][0]!=None):
			sql = "UPDATE items SET "+self.collist[icol]+"=? WHERE uid=?"
			self.db.speichereSQL(sql,(new_text,self.liststore[irow][0]),rowid=self.liststore[irow][0])
			
			logging.info("Updated row: "+self.collist[icol]+" new text "+new_text+" Titel: "+str(self.liststore[irow][2])+" with uid "+str(self.liststore[irow][0]))
			
			self.liststore[irow][icol]=new_text 
		else:
			logging.warning("update_row: row does not exist")
			return
			#if (self.emptyValueExists()==True)and(icol<2):
			#	#print "letzter Eintrag ohne inhalt"
			#	return
			
		#print "liststore 2"
		#for x in self.liststore:
		#	print x[0],x[2]
		
		
	def checkout_rows(self):
		sql = "UPDATE items SET status=? WHERE list=? AND category=?"
		self.db.speichereSQL(sql,("-1",self.selection.get_list(),self.selection.get_category()))
		for i in range(len(self.liststore)):
			self.liststore[i][1]="-1"
			
			
		
		
	def add_row(self):
		#self.update_row(-1,1,"-1")
		#for x in self.liststore:
		#	print x[0],x[2]
		status=self.selection.get_status()
		import uuid
		uid=str(uuid.uuid4())
		sql = "INSERT INTO items (uid,list,category,status, title) VALUES (?,?,?,?,?)"
		self.db.speichereSQL(sql,(uid,self.selection.get_list(),self.selection.get_category(),status,""),rowid=uid)
		logging.info("Insertet row: status = "+status+" with uid "+str(uid))
			#self.liststore[irow][0]=str(uuid.uuid4())
			
		self.liststore.append([uid,status,""," ","","","","","","","","",""])
		self.selection.comboLists_check_for_update()
		#	if (irow>-1):
		#		self.liststore[irow][icol]=new_text
		#		self.liststore[irow][0]=uid
		#	else:
		#		self.liststore.append([uid,"-1",""," ","","","","","","","","",""])
				#print "xy",self.liststore[len(self.liststore)-1][0]
			#Check if a new list/category is opened
		#	self.selection.comboLists_check_for_update()
		
	def del_row(self,irow,row_iter):
		uid=self.liststore[irow][0]
		self.liststore.remove(row_iter)
		sql = "DELETE FROM items WHERE uid=?"
		self.db.speichereSQL(sql,(uid,))
		#
		
		
	def get_colname(self,i):
		if i<len(self.collist):
			return self.collist[i]
		else:
			return None
		
	def get_colcount(self):
		return len(self.collist)

	
	def rename_category(self,new_name):
		sql = "UPDATE items SET category=? WHERE list=? AND category=?"
		self.db.speichereSQL(sql,(new_name,self.selection.get_list(),self.selection.get_category()))
		self.selection.comboList_changed()
		self.selection.set_category(new_name)
				
	def rename_list(self,new_name):
		sql = "UPDATE items SET list=? WHERE list=?"
		self.db.speichereSQL(sql,(new_name,self.selection.get_list(),))
		self.selection.load()
		self.selection.set_list(new_name)	
	
	
	#def update_category(self,widget=None,data=None,data2=None,data3=None):
	#	self.get_liststore()
		
	def update_list(self,widget=None,data=None,data2=None,data3=None):
		self.get_liststore()
		
	def __init__(self,db,selection):
		self.db=db
		self.liststore=None
		self.unitsstore=None
		self.selection=selection
		self.collist=("uid","status","title","quantitiy","unit","price","priority","date","private","stores","note","custom1","custom2")
		
		#sql="DROP TABLE items"
		#self.db.speichereSQL(sql)
		
		sql = "CREATE TABLE items (uid TEXT, list TEXT, category TEXT, status TEXT, title TEXT, quantitiy TEXT, unit TEXT, price TEXT, priority TEXT, date TEXT, pcdate TEXT, private TEXT, stores TEXT, note TEXT, custom1 TEXT, custom2 TEXT)"
		self.db.speichereSQL(sql)
		
		
		self.selection.load()
		self.selection.connect("changed",self.update_list)
		#self.selection.connect("changedCategory",self.update_category)
		

		"""
		sql = "INSERT INTO items (uid,list,category,title) VALUES (?,?,?,?)"
		import uuid
		self.db.speichereSQL(sql,(str(uuid.uuid4()),"default","default","atitel1"))
		self.db.speichereSQL(sql,(str(uuid.uuid4()),"default","default","btitel2"))
		self.db.speichereSQL(sql,(str(uuid.uuid4()),"default","default","ctitel3"))
		
		print "inserted"
		"""

		
		