#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
 
 
class Sync(gtk.VBox): 
	
	__gsignals__ = {
 		'syncFinished' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,(gobject.TYPE_STRING,)),
		'syncBeforeStart' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,(gobject.TYPE_STRING,)),
 	}
	
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
		
	
	def writeSQLTupel(self,newSQLs):
		if (newSQLs==None):
			 return
		pausenzaehler=0
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
					sql="SELECT * FROM logtable WHERE rowid=? ORDER BY pcdatum DESC"
					rows=self.db.ladeSQL(sql,(newSQL[5],))
					if (rows!=None)and(len(rows)>0):
						if (rows[0][1]>newSQL[1])and(len(rows[0][5])>0):
							logging.info("newer sync entry, ignoring old one")
							print "newer sync entry, ignoring old one"
							commitSQL=False
					
				if (commitSQL==True):
					self.db.speichereSQL(newSQL[2],param,commit=False,pcdatum=newSQL[1],rowid=newSQL[5])
			else: 
				logging.error("writeSQLTupel: Error")
				
			pausenzaehler+=1
			if (pausenzaehler % 10)==0:
				pass
				while (gtk.events_pending()):
    					gtk.main_iteration();
				
		logging.info("Alle SQLs an sqlite geschickt, commiting now")
		self.db.commitSQL()
		logging.info("Alle SQLs commited")
		
	
	def doSync(self,sync_uuid,pcdatum,newSQLs,pcdatumjetzt):
		#print uuid,pcdatum,newSQLs
		self.syncStatusLabel.set_text("sync process running")
		while (gtk.events_pending()):
    			gtk.main_iteration();
		diff=time.time()-pcdatumjetzt
		if diff<0:
			diff=diff*(-1)
		if diff>30:
			return -1
		
		sql="SELECT * FROM logtable WHERE pcdatum>?"
		rows=self.db.ladeSQL(sql,(pcdatum,))
		logging.info("doSync read sqls")
		self.writeSQLTupel(newSQLs)
		logging.info("doSync wrote sqls")
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
				self.rpcserver = SimpleXMLRPCServer((ip, 50503),allow_none=True) 
				self.rpcserver.register_function(pow)
				self.rpcserver.register_function(self.getLastSyncDate)
				self.rpcserver.register_function(self.doSync)
				self.rpcserver.register_function(self.getRemoteSyncUUID)
				self.rpcserver.register_function(self.doSaveFinalTime)
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
			
		#fime save time+uuid
		sql="DELETE FROM sync WHERE uuid=?"
		self.db.speichereSQL(sql,(sync_uuid,),log=False)
		sql="INSERT INTO sync (syncpartner,uuid,pcdatum) VALUES (?,?,?)"
		self.db.speichereSQL(sql,("x",str(sync_uuid),pcdatum),log=False)
		self.emit("syncFinished","syncFinished")
		self.syncStatusLabel.set_text("no sync process (at the moment)")
		return (self.sync_uuid,pcdatum)
		
	
	def syncButton(self, widget, data=None):
		logging.info("Syncing")
		#sql="DELETE FROM logtable WHERE sql LIKE externeStundenplanung"
		#self.db.speichereSQL(sql)
		
		self.syncStatusLabel.set_text("sync process running")
		while (gtk.events_pending()):
    			gtk.main_iteration();
		self.emit("syncBeforeStart","syncBeforeStart")

		self.db.speichereDirekt("syncRemoteIP",self.comboRemoteIP.get_child().get_text())
		try:
			server = xmlrpclib.ServerProxy("http://"+self.comboRemoteIP.get_child().get_text()+":50503",allow_none=True) 
			#lastDate=server.getLastSyncDate(str(self.sync_uuid))
			server_sync_uuid=server.getRemoteSyncUUID()
			lastDate=self.getLastSyncDate(str(server_sync_uuid))
			
			print ("LastSyncDate: "+str(lastDate)+" Now: "+str(int(time.time())))
		
			sql="SELECT * FROM logtable WHERE pcdatum>?"
			rows=self.db.ladeSQL(sql,(lastDate,))
		
			newSQLs=server.doSync(self.sync_uuid,lastDate,rows,time.time())
		
			logging.info("did do sync, processing sqls now")
			if newSQLs!=-1:
				self.writeSQLTupel(newSQLs)
	
				sync_uuid, finalpcdatum=server.doSaveFinalTime(self.sync_uuid)
				self.doSaveFinalTime(sync_uuid, finalpcdatum)
			
				mbox =  gtk.MessageDialog(None,gtk.DIALOG_MODAL,gtk.MESSAGE_INFO,gtk.BUTTONS_OK,"Synchronisation erfolgreich beendet") 
 				response = mbox.run() 
 				mbox.hide() 
 				mbox.destroy() 
				self.syncStatusLabel.set_text("no sync process (at the moment)")
			else:
				logging.warning("Zeitdiff zu groß/oder anderer db-Fehler")
				mbox =  gtk.MessageDialog(None,gtk.DIALOG_MODAL,gtk.MESSAGE_INFO,gtk.BUTTONS_OK,"Zeit differiert zu viel zwischen den Systemen") 
 				response = mbox.run() 
 				mbox.hide() 
 				mbox.destroy() 
				self.syncStatusLabel.set_text("no sync process (at the moment)")
			
		except:
				logging.warning("Sync connect failed")
				mbox =  gtk.MessageDialog(None,gtk.DIALOG_MODAL,gtk.MESSAGE_INFO,gtk.BUTTONS_OK,"Sync gescheitert. Fehler:"+str(sys.exc_info()))
 				response = mbox.run() 
 				mbox.hide() 
 				mbox.destroy() 
				self.syncStatusLabel.set_text("no sync process (at the moment)")
				
	
	def __init__(self,db):
		gtk.VBox.__init__(self,homogeneous=False, spacing=0)
		
		logging.info("Sync, init")
		self.db=db
		
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

		
		frame=gtk.Frame("LokalerSync-Server (Port 50503)")
		
		
		
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
				
		frame=gtk.Frame("RemoteSync-Server (Port 50503)")
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