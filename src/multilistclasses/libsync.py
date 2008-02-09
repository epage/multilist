#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import gobject
import time
import string
from SimpleXMLRPCServer import SimpleXMLRPCServer 
import random
import socket 
socket.setdefaulttimeout(60) # Timeout auf 60 sec. setzen 
import xmlrpclib 
import select
#import fcntl
import struct
import gtk
import uuid
import sys
import logging

import libspeichern 
 
 
class ProgressDialog(gtk.Dialog):
	
	def pulse(self):
		#self.progressbar.pulse()
		pass
	
	def __init__(self,title="Sync process", parent=None):
		gtk.Dialog.__init__(self,title,parent,gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,())
		
		logging.info("ProgressDialog, init")
		
		label=gtk.Label("Sync process running...please wait")
		self.vbox.pack_start(label, True, True, 0)
		label=gtk.Label("(this can take some minutes)")
		self.vbox.pack_start(label, True, True, 0)
		
		#self.progressbar=gtk.ProgressBar()
		#self.vbox.pack_start(self.progressbar, True, True, 0)
		
		#self.set_keep_above(True)
  		self.vbox.show_all()
		self.show()
 
class Sync(gtk.VBox): 
	
	__gsignals__ = {
 		'syncFinished' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,(gobject.TYPE_STRING,)),
		'syncBeforeStart' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,(gobject.TYPE_STRING,)),
 	}
	
	def changeSyncStatus(self,active,title):
		self.syncStatusLabel.set_text(title)
		if active==True:
			if self.progress==None:
				self.progress=ProgressDialog(parent=self.parentwindow)
				self.emit("syncBeforeStart","syncBeforeStart")
				
				
		else:
			if self.progress!=None:
				self.progress.hide()		
				self.progress.destroy()
				self.progress=None
				self.emit("syncFinished","syncFinished")
	
	def pulse(self):
		if self.progress!=None:
			self.progress.pulse()
		#if self.server!=None:
		#	self.server.pulse()
		
	
	def getUeberblickBox(self):
		frame=gtk.Frame("Abfrage")
		return frame
			
	def handleRPC(self):
		try:
			if (self.rpcserver==None): return False
		except:
			return False
			
		while (len(self.poll.poll(0))>0):
			self.rpcserver.handle_request()
		return True

	def get_ip_address(self,ifname):
		return socket.gethostbyname(socket.gethostname())
		#try:
		#	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		#	ip=socket.inet_ntoa(fcntl.ioctl(s.fileno(),0x8915,struct.pack('256s', ifname[:15]))[20:24])
		#	s.close()
		#except:
		#	ip=socket.gethostbyname(socket.gethostname())
		#	s.close()
		
		#return ip FixME
		
	def getLastSyncDate(self,sync_uuid):
		sql="SELECT syncpartner,pcdatum FROM sync WHERE uuid=?"
		rows=self.db.ladeSQL(sql,(sync_uuid,))
		if (rows!=None)and(len(rows)==1): 
			syncpartner,pcdatum = rows[0]
		else:
			pcdatum=-1
		logging.info("LastSyncDatum: "+str(pcdatum)+" Jetzt "+str(int(time.time())))
		return pcdatum
		
		
	def check4commit(self,newSQL,lastdate):
		logging.info("check4commit 1")
		if self.concernedRows==None:
			logging.info("check4commit Updatung concernedRows")
			sql="SELECT pcdatum,rowid FROM logtable WHERE pcdatum>? ORDER BY pcdatum DESC"
			self.concernedRows=self.db.ladeSQL(sql,(lastdate,))
			
			
		if (self.concernedRows!=None)and(len(self.concernedRows)>0):
			#logging.info("check4commit 2")
			id1, pcdatum,sql, param, host, rowid = newSQL
			
			if len(rowid)>0:
				for x in self.concernedRows:
					#logging.info("check4commit 3")
					if (x[1]==rowid):
						if (x[0]>pcdatum):
							logging.info("newer sync entry, ignoring old one")
							#logging.info("check4commit 9.1")
							return False
						else:
							#logging.info("check4commit 9.2")
							return True
							
		#logging.info("check4commit 9.3")
		return True
	
	def writeSQLTupel(self,newSQLs,lastdate):
		if (newSQLs==None):
			 return
		
		self.concernedRows=None
		pausenzaehler=0
		logging.info("writeSQLTupel got "+str(len(newSQLs))+" sql tupels")
		for newSQL in newSQLs:
			#print ""
			#print "SQL1: ",newSQL[1]
			#print "SQL2: ",newSQL[2]
			#print "SQL3: ",newSQL[3]
			#print "Param:",string.split(newSQL[3]," <<Tren-ner>> ")
			#print ""
			if (newSQL[3]!=""):
				param=string.split(newSQL[3]," <<Tren-ner>> ")
			else:
				param=None
		
			if (len(newSQL)>2):
				commitSQL=True

				if (newSQL[5]!=None)and(len(newSQL[5])>0):
					commitSQL=self.check4commit(newSQL,lastdate)
					
				if (commitSQL==True):
					self.db.speichereSQL(newSQL[2],param,commit=False,pcdatum=newSQL[1],rowid=newSQL[5])
			else: 
				logging.error("writeSQLTupel: Error")
				
			pausenzaehler+=1
			if (pausenzaehler % 10)==0:
				self.pulse()
				while (gtk.events_pending()):
    					gtk.main_iteration();
				
		logging.info("Alle SQLs an sqlite geschickt, commiting now")
		self.db.commitSQL()
		logging.info("Alle SQLs commited")
		
	
	def doSync(self,sync_uuid,pcdatum,newSQLs,pcdatumjetzt):
		#print uuid,pcdatum,newSQLs
		#logging.info("doSync 0")
		self.changeSyncStatus(True,"sync process running")
		self.pulse()
		#logging.info("doSync 1")
		
		while (gtk.events_pending()):
    			gtk.main_iteration();
		diff=time.time()-pcdatumjetzt
		if diff<0:
			diff=diff*(-1)
		if diff>30:
			return -1
		
		logging.info("doSync read sqls")
		sql="SELECT * FROM logtable WHERE pcdatum>?"
		rows=self.db.ladeSQL(sql,(pcdatum,))
		logging.info("doSync read sqls")
		self.writeSQLTupel(newSQLs,pcdatum)
		logging.info("doSync wrote "+str(len(newSQLs))+" sqls")
		logging.info("doSync sending "+str(len(rows))+" sqls")
		i=0
		return rows
		
	def getRemoteSyncUUID(self):
		return self.sync_uuid
	
	
	def startServer(self, widget, data=None):
		#Starte RPCServer
		self.db.speichereDirekt("syncServerIP",self.comboIP.get_child().get_text())
		
		if (widget.get_active()==True):
			logging.info("Starting Server")
			
			try:
				ip=self.comboIP.get_child().get_text()
				self.rpcserver = SimpleXMLRPCServer((ip, self.port),allow_none=True) 
				self.rpcserver.register_function(pow)
				self.rpcserver.register_function(self.getLastSyncDate)
				self.rpcserver.register_function(self.doSync)
				self.rpcserver.register_function(self.getRemoteSyncUUID)
				self.rpcserver.register_function(self.doSaveFinalTime)
				self.rpcserver.register_function(self.pulse)
				self.poll=select.poll()
				self.poll.register(self.rpcserver.fileno())
				gobject.timeout_add(1000, self.handleRPC)
				self.syncServerStatusLabel.set_text("Syncserver running...")
			
				#save
				self.db.speichereDirekt("startSyncServer",True)
			
			except:
				s=str(sys.exc_info())
				logging.error("libsync: could not start server. Error: "+s)
				mbox=gtk.MessageDialog(None,gtk.DIALOG_MODAL,gtk.MESSAGE_ERROR,gtk.BUTTONS_OK,"Konnte Sync-Server nicht starten. Bitte IP und Port überprüfen.") #gtk.DIALOG_MODAL
				mbox.set_modal(False)
				response=mbox.run() 
 				mbox.hide() 
 				mbox.destroy() 
				widget.set_active(False)
				
		else:
			logging.info("Stopping Server")
			try:
				del self.rpcserver	
			except:
				pass
			self.syncServerStatusLabel.set_text("Syncserver not running...")
			#save
			self.db.speichereDirekt("startSyncServer",False)
		
	def doSaveFinalTime(self,sync_uuid,pcdatum=None):
		if (pcdatum==None): pcdatum=int(time.time())
		if (time.time()>pcdatum):
			pcdatum=int(time.time()) #größere Zeit nehmen
			
		self.pulse()
		
		#fime save time+uuid
		sql="DELETE FROM sync WHERE uuid=?"
		self.db.speichereSQL(sql,(sync_uuid,),log=False)
		sql="INSERT INTO sync (syncpartner,uuid,pcdatum) VALUES (?,?,?)"
		self.db.speichereSQL(sql,("x",str(sync_uuid),pcdatum),log=False)
		self.pulse()
		self.changeSyncStatus(False,"no sync process (at the moment)")
		return (self.sync_uuid,pcdatum)
		
	
	def syncButton(self, widget, data=None):
		logging.info("Syncing")
		#sql="DELETE FROM logtable WHERE sql LIKE externeStundenplanung"
		#self.db.speichereSQL(sql)
		
		self.changeSyncStatus(True,"sync process running")
		while (gtk.events_pending()):
    			gtk.main_iteration();

		self.db.speichereDirekt("syncRemoteIP",self.comboRemoteIP.get_child().get_text())
		try:
			self.server = xmlrpclib.ServerProxy("http://"+self.comboRemoteIP.get_child().get_text()+":"+str(self.port),allow_none=True) 
			#lastDate=server.getLastSyncDate(str(self.sync_uuid))
			server_sync_uuid=self.server.getRemoteSyncUUID()
			lastDate=self.getLastSyncDate(str(server_sync_uuid))
			
			#print ("LastSyncDate: "+str(lastDate)+" Now: "+str(int(time.time())))
		
			sql="SELECT * FROM logtable WHERE pcdatum>?"
			rows=self.db.ladeSQL(sql,(lastDate,))
			
			logging.info("loaded concerned rows")
		
			newSQLs=self.server.doSync(self.sync_uuid,lastDate,rows,time.time())
		
			logging.info("did do sync, processing sqls now")
			if newSQLs!=-1:
				self.writeSQLTupel(newSQLs,lastDate)
	
				sync_uuid, finalpcdatum=self.server.doSaveFinalTime(self.sync_uuid)
				self.doSaveFinalTime(sync_uuid, finalpcdatum)
			
				self.changeSyncStatus(False,"no sync process (at the moment)")
				
				mbox =  gtk.MessageDialog(None,gtk.DIALOG_MODAL,gtk.MESSAGE_INFO,gtk.BUTTONS_OK,"Synchronisation erfolgreich beendet") 
 				response = mbox.run() 
 				mbox.hide() 
 				mbox.destroy() 
			else:
				logging.warning("Zeitdiff zu groß/oder anderer db-Fehler")
				self.changeSyncStatus(False,"no sync process (at the moment)")
				mbox =  gtk.MessageDialog(None,gtk.DIALOG_MODAL,gtk.MESSAGE_INFO,gtk.BUTTONS_OK,"Zeit differiert zu viel zwischen den Systemen") 
 				response = mbox.run() 
 				mbox.hide() 
 				mbox.destroy() 
		except:
				logging.warning("Sync connect failed")
				self.changeSyncStatus(False,"no sync process (at the moment)")
				mbox =  gtk.MessageDialog(None,gtk.DIALOG_MODAL,gtk.MESSAGE_INFO,gtk.BUTTONS_OK,"Sync gescheitert. Fehler:"+str(sys.exc_info()))
 				response = mbox.run() 
 				mbox.hide() 
 				mbox.destroy() 
				self.server=None
		self.server=None
				

			
	
	def __init__(self,db,parentwindow,port):
		gtk.VBox.__init__(self,homogeneous=False, spacing=0)
		
		logging.info("Sync, init")
		self.db=db
		self.progress=None
		self.server=None
		self.port=int(port)
		self.parentwindow=parentwindow
		self.concernedRows=None
		
		#print "Sync, 2"
		#sql = "DROP TABLE sync"
		#self.db.speichereSQL(sql,log=False)
		
		sql = "CREATE TABLE sync (id INTEGER PRIMARY KEY, syncpartner TEXT, uuid TEXT, pcdatum INTEGER)"
		self.db.speichereSQL(sql,log=False)
		
		#print "Sync, 3"
		
		sql="SELECT uuid,pcdatum FROM sync WHERE syncpartner=?"
		rows=self.db.ladeSQL(sql,("self",)) #Eigene Id feststellen
		
		#print "Sync, 3a"
		if (rows==None)or(len(rows)!=1):
			sql="DELETE FROM sync WHERE syncpartner=?"
			self.db.speichereSQL(sql,("self",),log=False)
			#uuid1=uuid()
			#print "Sync, 3b"
			
			#print "Sync, 3bb"
			self.sync_uuid=str(uuid.uuid4())
			sql="INSERT INTO sync (syncpartner,uuid,pcdatum) VALUES (?,?,?)"
			self.db.speichereSQL(sql,("self",str(self.sync_uuid),int(time.time())),log=False)
			#print "Sync, 3c"
		else:
			sync_uuid,pcdatum = rows[0]
			self.sync_uuid=sync_uuid
		#print "x1"
		
		
		
		#print "Sync, 4"

		
		frame=gtk.Frame("LokalerSync-Server (Port "+str(self.port)+")")
		
		
		
		self.comboIP=gtk.combo_box_entry_new_text()
		
		
		self.comboIP.append_text("") #self.get_ip_address("eth0"))
		#self.comboIP.append_text(self.get_ip_address("eth1")) #fixme
		#self.comboIP.append_text(self.get_ip_address("eth2"))
		#self.comboIP.append_text(self.get_ip_address("eth3"))
		#print "Sync, 4d"
		#self.comboIP.append_text(self.get_ip_address("wlan0"))
		#self.comboIP.append_text(self.get_ip_address("wlan1"))
		
		#print "Sync, 4e"
		
		frame.add(self.comboIP)
		serverbutton=gtk.ToggleButton("SyncServer starten")
		serverbutton.connect("clicked",self.startServer,(None,))
		self.pack_start(frame, expand=False, fill=True, padding=1)
		self.pack_start(serverbutton, expand=False, fill=True, padding=1)
		self.syncServerStatusLabel=gtk.Label("Syncserver not running")
		self.pack_start(self.syncServerStatusLabel, expand=False, fill=True, padding=1)		
				
		frame=gtk.Frame("RemoteSync-Server (Port "+str(self.port)+")")
		self.comboRemoteIP=gtk.combo_box_entry_new_text()
		self.comboRemoteIP.append_text("192.168.0.?")
		self.comboRemoteIP.append_text("192.168.1.?")
		self.comboRemoteIP.append_text("192.168.176.?")
		frame.add(self.comboRemoteIP)
		syncbutton=gtk.Button("Verbinde zu Remote-SyncServer")
		syncbutton.connect("clicked",self.syncButton,(None,))
		self.pack_start(frame, expand=False, fill=True, padding=1)
		self.pack_start(syncbutton, expand=False, fill=True, padding=1)
		self.syncStatusLabel=gtk.Label("no sync process (at the moment)")
		self.pack_start(self.syncStatusLabel, expand=False, fill=True, padding=1)


		#self.comboRemoteIP.set_text_column("Test")
		self.comboRemoteIP.get_child().set_text(self.db.ladeDirekt("syncRemoteIP"))
		self.comboIP.get_child().set_text(self.db.ladeDirekt("syncServerIP"))
		
		#load
		if (self.db.ladeDirekt("startSyncServer",False)==True):
			serverbutton.set_active(True)
			
		#print "Sync, 9"