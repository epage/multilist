#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import sqlite3
import shelve
import sys
import string
import shutil
import os
import logging

class Speichern():
	def speichereDirekt(self,schluessel,daten):
		self.d[schluessel]=daten
		logging.info("speichereDirekt "+str(schluessel)+" "+str(daten)+" lesen: "+str(self.d[schluessel]))

	
	def ladeDirekt(self,schluessel,default=""):
		#print "ladeDirekt",schluessel, "Schluessel vorhanden",self.d.has_key(schluessel)
		if (self.d.has_key(schluessel)==True):
			data=self.d[schluessel]
			#print data
			return data
		else:
			return default
				
				
	def speichereSQL(self,sql,tupel=None,commit=True,host="self",log=True,pcdatum=None,rowid=""):
		#print "speichereSQL:",sql,tupel
		try:
			programSQLError=True
			if (tupel==None):
				self.cur.execute(sql)
			else:
				self.cur.execute(sql,tupel)
			programSQLError=False	
			
			#print int(time.time()), sql, pickle.dumps(tupel), host
			if (log==True):
				strtupel=[]
				if (tupel!=None):
					for t in tupel:
						strtupel.append(str(t))


				if pcdatum==None: pcdatum=int(time.time())
				self.cur.execute("INSERT INTO logtable ( pcdatum,sql,param,host,rowid ) VALUES (?,?,?,?,?)",(pcdatum, sql, string.join(strtupel," <<Tren-ner>> "), host,str(rowid) ))
 			if (commit==True): self.conn.commit()
			
			return True
		except:
			s=str(sys.exc_info())
			if (s.find(" already exists")==-1):
			#if len(s)>0:
				if (programSQLError==True):
					logging.error("speichereSQL-Exception "+str(sys.exc_info())+" "+str(sql)+" "+str(tupel))
				else:
					logging.error("speichereSQL-Exception in Logging!!!! :"+str(sys.exc_info())+" "+str(sql)+" "+str(tupel))
			return False

	def commitSQL(self):
		self.conn.commit()
		
		
	def ladeSQL(self,sql,tupel=None):
		#print sql,tupel
		try:
			if (tupel==None):
				self.cur.execute(sql)
			else:
				self.cur.execute(sql,tupel)
			return self.cur.fetchall()
		except:
			logging.error("ladeSQL-Exception "+str(sys.exc_info())+" "+str(sql)+" "+str(tupel))
			return ()
		
	def ladeHistory(self,sql_condition,param_condition):
		sql="SELECT * FROM logtable WHERE sql LIKE '%"+str(sql_condition)+"%' AND param LIKE '%"+str(param_condition)+"%'"
		rows=self.ladeSQL(sql)
		#print rows 
		i=0
		erg=[]
		while i<len(rows):
			datum=time.strftime("%d.%m.%y %H:%M:%S", (time.localtime(rows[i][1])))
			erg.append([rows[i][1],datum,rows[i][2],rows[i][3],rows[i][3].split(" <<Tren-ner>> ")])
					#pcdatum #datum #sql # Param_org #param 
			
			i+=1
			
		return erg
		
	def delHistory(self,sql_condition,param_condition,exceptTheLastXSeconds=0):
		pcdatum=int(time.time())-exceptTheLastXSeconds
		sql="DELETE FROM logtable WHERE sql LIKE '%"+str(sql_condition)+"%' AND param LIKE '%"+str(param_condition)+"%' AND pcdatum<?"
		self.speichereSQL(sql,(pcdatum,))
		
	def delHistoryWithRowID(self,rowid,sql_condition=" ",exceptTheLastXSeconds=0):
		pcdatum=int(time.time())-exceptTheLastXSeconds
		sql="DELETE FROM logtable WHERE rowid=? AND pcdatum<? AND sql LIKE '%"+str(sql_condition)+"%'"
		self.speichereSQL(sql,(rowid,pcdatum,))
		
	def openDB(self):
		try:
			self.cur.close()
		except:
			pass
		try:
			self.conn.close()
		except:
			pass
		
		db=self.ladeDirekt("datenbank")
		if db=="": 
			home_dir = os.path.expanduser('~')
			db=os.path.join(home_dir, "multilist.s3db") 
			
		
		datum=time.strftime("%Y-%m-%d--", (time.localtime(time.time())))+str(int(time.time()))+"--"
		if (os.path.exists(db))and(os.path.exists(os.path.dirname(db)+os.sep+"backup/")):
			try:
				shutil.copyfile(db,str(os.path.dirname(db))+os.sep+"backup"+os.sep+datum+os.path.basename(db))
				#logging.debug(str(os.path.dirname(db))+os.sep+"backup"+os.sep+datum+os.path.basename(db))
			except:
				logging.info("Achtung Backup-Datei NICHT (!!!) angelegt!")
				#print db,str(os.path.dirname(db))+os.sep+"backup"+os.sep+datum+os.path.basename(db)
		
		self.conn = sqlite3.connect(db)		
 		self.cur = self.conn.cursor()
		try:
			sql="CREATE TABLE logtable (id INTEGER PRIMARY KEY AUTOINCREMENT, pcdatum INTEGER ,sql TEXT, param TEXT, host TEXT, rowid TEXT)"
			self.cur.execute(sql)
 			self.conn.commit()
		except:
			pass
		
		#Add rowid line (not in old versions included)
		try:
			sql="ALTER TABLE logtable ADD rowid TEXT"
			self.cur.execute(sql)
 			self.conn.commit()
		except:
			pass
		
		
	def __init__(self):
		home_dir = os.path.expanduser('~')
		filename=os.path.join(home_dir, ".multilist.dat") 
		self.d = shelve.open(filename)
		self.openDB()

	

		
		
	def close(self):
		try:
			self.d.close()
		except:
			pass
		try:
			self.cur.close()
		except:
			pass
		try:
			self.conn.close()
		except:
			pass
		logging.info("Alle Daten gespeichert")
		
	def __del__(self):
		self.close()