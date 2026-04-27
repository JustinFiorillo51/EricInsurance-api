/****** Object:  Table [dbo].[tbl_Web_DocTemplates]    Script Date: 8/1/2025 4:26:04 AM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[tbl_Web_DocTemplates](
	[RowID] [int] IDENTITY(100,1) NOT NULL,
	[DocGuid] [uniqueidentifier] NOT NULL,
	[FileName] [nvarchar](300) NULL,
	[templateDesc] [nvarchar](300) NULL,
	[SQLquery] [varchar](500) NULL,
	[DocType] [nchar](10) NULL,
	[ImageBlob] [varbinary](max) NULL,
	[DocumentSizeInMB] [nvarchar](15) NULL,
	[UploadedDate] [datetime] NOT NULL,
	[UploadedBy] [nvarchar](100) NULL,
	[UpdatedDate] [datetime] NULL,
	[UpdatedBy] [nvarchar](100) NULL,
	[RecordStatus] [int] NOT NULL,
	[Deleted] [int] NULL,
	[DeletedDate] [datetime] NULL,
	[TemplateContent] [nvarchar](max) NULL,
 CONSTRAINT [PK_tbl_Web_DocTemplates] PRIMARY KEY CLUSTERED 
(
	[RowID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO

ALTER TABLE [dbo].[tbl_Web_DocTemplates] ADD  CONSTRAINT [DF_tbl_Web_DocTemplates_DocGuid]  DEFAULT (newid()) FOR [DocGuid]
GO

ALTER TABLE [dbo].[tbl_Web_DocTemplates] ADD  CONSTRAINT [DF_tbl_Web_DocTemplates_UploadedDate]  DEFAULT (getdate()) FOR [UploadedDate]
GO

ALTER TABLE [dbo].[tbl_Web_DocTemplates] ADD  CONSTRAINT [DF_tbl_Web_DocTemplates_UpdatedDate]  DEFAULT (getdate()) FOR [UpdatedDate]
GO

ALTER TABLE [dbo].[tbl_Web_DocTemplates] ADD  CONSTRAINT [DF_tbl_Web_DocTemplates_RecordStatus]  DEFAULT ((1)) FOR [RecordStatus]
GO

ALTER TABLE [dbo].[tbl_Web_DocTemplates] ADD  CONSTRAINT [DF_tbl_Web_DocTemplates_Deleted]  DEFAULT ((0)) FOR [Deleted]
GO

