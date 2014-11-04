#!/bin/bash
sqlite3 dummy.sqlite "DROP TABLE PBox; CREATE TABLE PBox (PBoxId INTEGER PRIMARY KEY AUTOINCREMENT, UserCC NVARCHAR(9), UserName TEXT, PubKey TEXT); INSERT INTO Pbox (UserCC, UserName, PubKey) VALUES (123456789, 'Miguel', 'asd' ); SELECT PBoxId FROM PBox WHERE UserName = 'Miguel';"
