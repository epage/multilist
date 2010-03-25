#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import sqlite3
import uuid


def copydb(db):
	conn = sqlite3.connect(db)
	cur = conn.cursor()

	sql = "UPDATE sync SET syncpartner=? WHERE syncpartner=?"
	cur.execute(sql, (str(uuid.uuid4()), "self")) #Eigene Id ändern feststellen
	conn.commit()

	sql = "DELETE FROM sync WHERE syncpartner=?"
	cur.execute(sql, ("self", ))
	conn.commit()

	sql = "INSERT INTO sync (syncpartner,uuid,pcdatum) VALUES (?,?,?)"
	cur.execute(sql, ("self", str(uuid.uuid4()), int(time.time())))

	sql = "UPDATE sync SET pcdatum=?"
	cur.execute(sql, (int(time.time()), ))

	conn.commit()


if __name__ == "__main__":
	dbPath = "/home/chris/Documents/Schule/Schule/schulplaner/schuljahr200708enni.s3db"
	copydb(dbPath)
