#!/bin/bash
sqlite3 safebox.sqlite "DROP TABLE PBox;
CREATE TABLE PBox (PBoxId INTEGER PRIMARY KEY AUTOINCREMENT, UserCCId NVARCHAR(9), UserName TEXT, PubKey TEXT);
INSERT INTO PBox (UserCCId, UserName, PubKey) VALUES (123456789, 'Miguel', 'asd' );
INSERT INTO PBox (UserCCId, UserName, PubKey) VALUES (987654321, 'Ze', 'dsa' );
SELECT * FROM PBox;
DROP TABLE File;
CREATE TABLE File (FileId INTEGER PRIMARY KEY AUTOINCREMENT, OwnerPBoxId INTEGER NOT NULL, FileName TEXT, SymKey TEXT);
INSERT INTO File (OwnerPBoxId, FileName, SymKey) VALUES (1, 'MyFile', 'asssdfd' );
INSERT INTO File (OwnerPBoxId, FileName, SymKey) VALUES (1, 'AnotherFile', 'asssfd' );
INSERT INTO File (OwnerPBoxId, FileName, SymKey) VALUES (2, 'MyFile', 'asdfsd' );
INSERT INTO File (OwnerPBoxId, FileName, SymKey) VALUES (2, 'OtherFile', 'assdfsd' );
SELECT * FROM File;
"
