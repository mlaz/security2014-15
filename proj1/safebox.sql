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
    [PBoxId] INTEGER PRIMARY KEY,
    [UserCCId] NVARCHAR(160)  NOT NULL,
    [PubKey] NVARCHAR(160)  NOT NULL,
    [UserName] NVARCHAR(160)  NOT NULL
);

CREATE TABLE [File]
(
    [FileId] INTEGER PRIMARY KEY,
    [OwnerPBoxId] INTEGER  NOT NULL,
    [SymKey] BLOB  NOT NULL,
    [FileName] NVARCHAR(120),
    FOREIGN KEY ([OwnerPBoxId]) REFERENCES [PBox] ([PBoxId])
                ON DELETE NO ACTION ON UPDATE NO ACTION
);

CREATE TABLE [Share]
(
    [FileId] INTEGER  NOT NULL,
    [ForeignPBoxId] INTEGER  NOT NULL,
    [SymKey] BLOB  NOT NULL,
    [Writeable] INTEGER  DEFAULT 0,
    CONSTRAINT [PK_Share] PRIMARY KEY  ([FileId], [ForeignPBoxId]),
    FOREIGN KEY ([FileId]) REFERENCES [File] ([FileId])
		ON DELETE NO ACTION ON UPDATE NO ACTION,
    FOREIGN KEY ([ForeignPBoxId]) REFERENCES [PBox] ([PBoxId])
		ON DELETE NO ACTION ON UPDATE NO ACTION
);
