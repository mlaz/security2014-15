#!/bin/bash
sqlite3 safebox.sqlite "DROP TABLE PBox;
CREATE TABLE PBox (PBoxId INTEGER PRIMARY KEY AUTOINCREMENT, UserCCId NVARCHAR(9), UserName TEXT, PubKey TEXT);
INSERT INTO Pbox (UserCCId, UserName, PubKey) VALUES (123456789, 'Miguel', 'asd' );
INSERT INTO Pbox (UserCCId, UserName, PubKey) VALUES (987654321, 'Ze', 'dsa' );
SELECT * FROM PBox;"
