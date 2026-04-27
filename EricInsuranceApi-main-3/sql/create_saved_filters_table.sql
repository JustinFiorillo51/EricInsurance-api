-- Create SavedFilters table for storing advanced filter configurations
-- This table stores user-specific saved filter configurations

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='SavedFilters' AND xtype='U')
BEGIN
    CREATE TABLE dbo.SavedFilters (
        Filter_ID INT IDENTITY(1,1) PRIMARY KEY,
        Filter_Name NVARCHAR(100) NOT NULL,
        Filter_Configuration NTEXT NOT NULL,  -- JSON string containing filter configuration
        User_ID NVARCHAR(10) NOT NULL,
        Created_Date DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        LastModified_Date DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        Is_Active BIT NOT NULL DEFAULT 1
    )
    
    -- Create indexes for better performance
    CREATE INDEX IX_SavedFilters_UserID ON dbo.SavedFilters(User_ID, Is_Active)
    CREATE INDEX IX_SavedFilters_LastModified ON dbo.SavedFilters(LastModified_Date DESC)
    
    PRINT 'SavedFilters table created successfully'
END
ELSE
BEGIN
    PRINT 'SavedFilters table already exists'
END

-- Add comments to the table and columns
IF EXISTS (SELECT * FROM sysobjects WHERE name='SavedFilters' AND xtype='U')
BEGIN
    EXEC sp_addextendedproperty 
        @name = N'MS_Description', 
        @value = N'Table for storing user-specific advanced filter configurations', 
        @level0type = N'SCHEMA', @level0name = N'dbo', 
        @level1type = N'TABLE', @level1name = N'SavedFilters'
    
    EXEC sp_addextendedproperty 
        @name = N'MS_Description', 
        @value = N'Primary key for the saved filter', 
        @level0type = N'SCHEMA', @level0name = N'dbo', 
        @level1type = N'TABLE', @level1name = N'SavedFilters', 
        @level2type = N'COLUMN', @level2name = N'Filter_ID'
    
    EXEC sp_addextendedproperty 
        @name = N'MS_Description', 
        @value = N'Name of the saved filter', 
        @level0type = N'SCHEMA', @level0name = N'dbo', 
        @level1type = N'TABLE', @level1name = N'SavedFilters', 
        @level2type = N'COLUMN', @level2name = N'Filter_Name'
    
    EXEC sp_addextendedproperty 
        @name = N'MS_Description', 
        @value = N'JSON string containing the filter configuration (groups, conditions, operators)', 
        @level0type = N'SCHEMA', @level0name = N'dbo', 
        @level1type = N'TABLE', @level1name = N'SavedFilters', 
        @level2type = N'COLUMN', @level2name = N'Filter_Configuration'
    
    EXEC sp_addextendedproperty 
        @name = N'MS_Description', 
        @value = N'User ID who created the filter', 
        @level0type = N'SCHEMA', @level0name = N'dbo', 
        @level1type = N'TABLE', @level1name = N'SavedFilters', 
        @level2type = N'COLUMN', @level2name = N'User_ID'
    
    EXEC sp_addextendedproperty 
        @name = N'MS_Description', 
        @value = N'Date when the filter was created', 
        @level0type = N'SCHEMA', @level0name = N'dbo', 
        @level1type = N'TABLE', @level1name = N'SavedFilters', 
        @level2type = N'COLUMN', @level2name = N'Created_Date'
    
    EXEC sp_addextendedproperty 
        @name = N'MS_Description', 
        @value = N'Date when the filter was last modified', 
        @level0type = N'SCHEMA', @level0name = N'dbo', 
        @level1type = N'TABLE', @level1name = N'SavedFilters', 
        @level2type = N'COLUMN', @level2name = N'LastModified_Date'
    
    EXEC sp_addextendedproperty 
        @name = N'MS_Description', 
        @value = N'Whether the filter is active (1) or deleted (0)', 
        @level0type = N'SCHEMA', @level0name = N'dbo', 
        @level1type = N'TABLE', @level1name = N'SavedFilters', 
        @level2type = N'COLUMN', @level2name = N'Is_Active'
END 