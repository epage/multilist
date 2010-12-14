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

from __future__ import with_statement

import sys
import os
import time
import sqlite3
import shelve
import string
import shutil
import logging

try:
	_
except NameError:
	_ = lambda x: x


_moduleLogger = logging.getLogger(__name__)


class Speichern(object):

	def __init__(self):
		home_dir = os.path.expanduser('~')
		filename = os.path.join(home_dir, ".multilist.dat")
		self.d = shelve.open(filename)
		self.openDB()

	def openDB(self):
		try:
			self.cur.close()
		except:
			pass
		try:
			self.conn.close()
		except:
			pass

		db = self.ladeDirekt("datenbank")
		if db == "":
			home_dir = os.path.expanduser('~')
			db = os.path.join(home_dir, "multilist.s3db")

		datum = time.strftime("%Y-%m-%d--", (time.localtime(time.time())))+str(int(time.time()))+"--"
		if os.path.exists(db) and os.path.exists(os.path.dirname(db)+os.sep+"backup"):
			try:
				shutil.copyfile(db, str(os.path.dirname(db))+os.sep+"backup"+os.sep+datum+os.path.basename(db))
			except:
				_moduleLogger.info("Achtung Backup-Datei NICHT (!!!) angelegt!")

		self.conn = sqlite3.connect(db)
		self.cur = self.conn.cursor()
		try:
			sql = "CREATE TABLE logtable (id INTEGER PRIMARY KEY AUTOINCREMENT, pcdatum INTEGER , sql TEXT, param TEXT, host TEXT, rowid TEXT)"
			self.cur.execute(sql)
			self.conn.commit()
		except:
			pass

		#Add rowid line (not in old versions included)
		try:
			sql = "ALTER TABLE logtable ADD rowid TEXT"
			self.cur.execute(sql)
			self.conn.commit()
		except:
			pass

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
		_moduleLogger.info("Alle Daten gespeichert")

	def __del__(self):
		self.close()

	def speichereDirekt(self, schluessel, daten):
		try:
			self.d[schluessel] = daten
		except ValueError:
			_moduleLogger.exception("Why oh why do we do this?")
		_moduleLogger.info("speichereDirekt "+str(schluessel)+" "+str(daten)+" lesen: "+str(self.d[schluessel]))

	def ladeDirekt(self, schluessel, default = ""):
		try:
			if self.d.has_key(schluessel):
				data = self.d[schluessel]
				return data
			else:
				return default
		except ValueError:
			_moduleLogger.exception(
				"Why did '%s' cause the problem? (returning default '%s')" % (schluessel, default)
			)
			return default

	def speichereSQL(self, sql, tupel = None, commit = True, host = "self", log = True, pcdatum = None, rowid = ""):
		try:
			programSQLError = True
			if tupel is None:
				self.cur.execute(sql)
			else:
				self.cur.execute(sql, tupel)
			programSQLError = False

			if log:
				strtupel = []
				if tupel is not None:
					for t in tupel:
						strtupel.append(str(t))

				if pcdatum is None:
					pcdatum = int(time.time())
				self.cur.execute("INSERT INTO logtable ( pcdatum, sql, param, host, rowid ) VALUES (?, ?, ?, ?, ?)", (pcdatum, sql, string.join(strtupel, " <<Tren-ner>> "), host, str(rowid) ))
			if commit:
				self.conn.commit()
			return True
		except:
			s = str(sys.exc_info())
			if s.find(" already exists") == -1:
				if programSQLError:
					_moduleLogger.error("speichereSQL-Exception "+str(sys.exc_info())+" "+str(sql)+" "+str(tupel))
				else:
					_moduleLogger.error("speichereSQL-Exception in Logging!!!! :"+str(sys.exc_info())+" "+str(sql)+" "+str(tupel))
			return False

	def commitSQL(self):
		self.conn.commit()

	def ladeSQL(self, sql, tupel = None):
		try:
			if tupel is None:
				self.cur.execute(sql)
			else:
				self.cur.execute(sql, tupel)
			return self.cur.fetchall()
		except:
			_moduleLogger.error("ladeSQL-Exception "+str(sys.exc_info())+" "+str(sql)+" "+str(tupel))
			return ()

	def ladeHistory(self, sql_condition, param_condition):
		sql = "SELECT * FROM logtable WHERE sql LIKE '%"+str(sql_condition)+"%' AND param LIKE '%"+str(param_condition)+"%'"
		rows = self.ladeSQL(sql)

		erg = []
		for row in rows:
			datum = time.strftime("%d.%m.%y %H:%M:%S", (time.localtime(row[1])))
			erg.append([row[1], datum, row[2], row[3], row[3].split(" <<Tren-ner>> ")])

		return erg

	def delHistory(self, sql_condition, param_condition, exceptTheLastXSeconds = 0):
		pcdatum = int(time.time())-exceptTheLastXSeconds
		sql = "DELETE FROM logtable WHERE sql LIKE '%"+str(sql_condition)+"%' AND param LIKE '%"+str(param_condition)+"%' AND pcdatum<?"
		self.speichereSQL(sql, (pcdatum, ))

	def delHistoryWithRowID(self, rowid, sql_condition = " ", exceptTheLastXSeconds = 0):
		pcdatum = int(time.time())-exceptTheLastXSeconds
		sql = "DELETE FROM logtable WHERE rowid = ? AND pcdatum<? AND sql LIKE '%"+str(sql_condition)+"%'"
		self.speichereSQL(sql, (rowid, pcdatum, ))
