/*******************************************************************************
   Drop Tables
********************************************************************************/
DROP TABLE IF EXISTS [PBox];

DROP TABLE IF EXISTS [File];

DROP TABLE IF EXISTS [Share];


/*******************************************************************************
   Create Tables
********************************************************************************/
CREATE TABLE [PBox]
(
    [PBoxId] INTEGER PRIMARY KEY AUTOINCREMENT,
    [UserCCId] NVARCHAR(160)  NOT NULL,
    [PubKey] TEXT  NOT NULL,
    [UserName] NVARCHAR(160)  NOT NULL
);

CREATE TABLE [File]
(
    [FileId] INTEGER PRIMARY KEY AUTOINCREMENT,
    [OwnerPBoxId] INTEGER  NOT NULL,
    [FileName] TEXT NOT NULL,
    [IV] TEXT NOT NULL,
    [SymKey] TEXT  NOT NULL,
    FOREIGN KEY ([OwnerPBoxId]) REFERENCES [PBox] ([PBoxId])
                ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE [Share]
(
    [FileId] INTEGER  NOT NULL,
    [ForeignPBoxId] INTEGER  NOT NULL,
    [SymKey] TEXT NOT NULL,
    [IV] TEXT NOT NULL,
    [Writeable] INTEGER  DEFAULT 0,
    CONSTRAINT [PK_Share] PRIMARY KEY  ([FileId], [ForeignPBoxId]),
    FOREIGN KEY ([FileId]) REFERENCES [File] ([FileId])
		ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY ([ForeignPBoxId]) REFERENCES [PBox] ([PBoxId])
		ON DELETE CASCADE ON UPDATE NO ACTION
);
