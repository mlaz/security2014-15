#!/bin/bash
sqlite3 safebox.sqlite "DROP TABLE IF EXISTS PBox;
CREATE TABLE PBox (PBoxId INTEGER PRIMARY KEY AUTOINCREMENT, UserCCId NVARCHAR(9), UserName TEXT, PubKey TEXT);
INSERT INTO PBox (UserCCId, UserName, PubKey) VALUES (123456789, 'Miguel', 'asd' );
INSERT INTO PBox (UserCCId, UserName, PubKey) VALUES (987654321, 'Ze', 'dsa' );
SELECT * FROM PBox;
DROP TABLE IF EXISTS File;
CREATE TABLE File (FileId INTEGER PRIMARY KEY AUTOINCREMENT, OwnerPBoxId INTEGER NOT NULL, FileName TEXT NOT NULL, IV TEXT NOT NULL, SymKey TEXT NOT NULL, FOREIGN KEY (OwnerPBoxID) REFERENCES PBox (PBoxId) ON DELETE CASCADE);
INSERT INTO File (OwnerPBoxId, FileName, IV, SymKey) VALUES (1, 'MyFile', 'asssdfd', 'sdfsdf');
INSERT INTO File (OwnerPBoxId, FileName, IV, SymKey) VALUES (1, 'AnotherFile', 'asssfd', 'sdff');
INSERT INTO File (OwnerPBoxId, FileName, IV, SymKey) VALUES (2, 'MyFile', 'asdfsd', 'sdfs');
INSERT INTO File (OwnerPBoxId, FileName, IV, SymKey) VALUES (2, 'OtherFile', 'assdfsd', 'fsdf');
SELECT * FROM File;
DROP TABLE IF EXISTS Share;
CREATE TABLE Share (FileId INTEGER NOT NULL, ForeignPBoxId INTEGER NOT NULL, SymKey TEXT NOT NULL, IV TEXT NOT NULL, Writeable INTEGER DEFAULT 0, PRIMARY KEY (FileId, ForeignPBoxId), FOREIGN KEY (FileId) REFERENCES File (FileId) ON DELETE CASCADE, FOREIGN KEY (ForeignPBoxId) REFERENCES PBox (PBoxId) ON DELETE CASCADE);
INSERT INTO Share VALUES (1, 2, 'asd', 'fgh', 1);
INSERT INTO Share VALUES (2, 2, 'zxc', 'vbn', 1);
SELECT * FROM Share;
SELECT FileName, File.FileId, OwnerPBoxId, ForeignPBoxId FROM File, Share WHERE File.FileId = Share.FileId;
"
