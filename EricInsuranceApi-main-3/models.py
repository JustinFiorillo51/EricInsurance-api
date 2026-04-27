from db import Model
from sqlalchemy import Column, String, Float, Boolean, DateTime, Integer, Text, LargeBinary, Date
from sqlalchemy.orm import Mapped, mapped_column
import datetime
import base64

# Model for Table_Security
class User(Model):
    __tablename__ = 'Table_Security'
    
    User_ID = Column(String(10), primary_key=True)
    User_Password = Column(String(10), nullable=True)
    User_Level = Column(Float, nullable=True)
    User_LoggedOn = Column(Boolean, nullable=False, default=False)
    User_Timestamp = Column(DateTime, nullable=True)
    User_Sync = Column(Boolean, nullable=False, default=False)
    User_FirstName = Column(String(25), nullable=True)
    User_LastName = Column(String(25), nullable=True)
    User_Dept = Column(String(50), nullable=True)
    User_Workfile_Location = Column(String(75), nullable=True)
    User_Session_ID = Column(String(32), nullable=True)

    def to_dict(self):
        return {
            'User_ID': self.User_ID,
            # 'User_Password': self.User_Password,
            'User_Level': self.User_Level,
            'User_LoggedOn': self.User_LoggedOn,
            'User_Timestamp': self.User_Timestamp.isoformat() if self.User_Timestamp else None,
            'User_Sync': self.User_Sync,
            'User_FirstName': self.User_FirstName,
            'User_LastName': self.User_LastName,
            'User_Dept': self.User_Dept,
            'User_Workfile_Location': self.User_Workfile_Location,
            'User_Session_ID': self.User_Session_ID
        }


class Rate(Model):
    __tablename__ = 'Table_Rates'
    
    Row_ID = Column(Integer, primary_key=True)
    Rate_Date = Column(DateTime, nullable=False)
    Rate_PolicyID = Column(String(255), nullable=False)
    Rate_Lookup = Column(String(255), nullable=True)
    Rate_Comments = Column(String(255), nullable=True)
    Rate_Basic_Prem = Column(Float, nullable=True)
    Rate_Basic_Prem_ADD = Column(Float, nullable=True)
    Rate_Basic_Prem_Dep = Column(Float, nullable=True)
    Rate_VLife_Wkly_Deduct = Column(Float, nullable=True)
    Rate_VLife_Prem_Child = Column(Float, nullable=True)
    Rate_Basic_Volume_Emp = Column(Float, nullable=True)
    Rate_Basic_Volume_Spouse = Column(Float, nullable=True)
    Rate_Basic_Volume_Child = Column(Float, nullable=True)

    def to_dict(self):
        return {
            'Row_ID': self.Row_ID,
            'Rate_Date': self.Rate_Date.isoformat() if self.Rate_Date else None,
            'Rate_PolicyID': self.Rate_PolicyID,
            'Rate_Lookup': self.Rate_Lookup,
            'Rate_Comments': self.Rate_Comments,
            'Rate_Basic_Prem': self.Rate_Basic_Prem,
            'Rate_Basic_Prem_ADD': self.Rate_Basic_Prem_ADD,
            'Rate_Basic_Prem_Dep': self.Rate_Basic_Prem_Dep,
            'Rate_VLife_Wkly_Deduct': self.Rate_VLife_Wkly_Deduct,
            'Rate_VLife_Prem_Child': self.Rate_VLife_Prem_Child,
            'Rate_Basic_Volume_Emp': self.Rate_Basic_Volume_Emp,
            'Rate_Basic_Volume_Spouse': self.Rate_Basic_Volume_Spouse,
            'Rate_Basic_Volume_Child': self.Rate_Basic_Volume_Child
        }


class RatesLookup(Model):
    __tablename__ = 'Table_VLifeAgeRates'
    
    Row_ID = Column(Integer, primary_key=True)
    Age_Bracket = Column(String(15), nullable=True)
    Rate_VLife = Column(Float, nullable=True)
    LastUpdated_Date = Column(DateTime, nullable=True, default=datetime.datetime.now)
    Group_Name = Column(String(50), nullable=True)
    Group_PolicyNum = Column(String(10), nullable=True)

    def to_dict(self):
        return {
            'Row_ID': self.Row_ID,
            'Age_Bracket': self.Age_Bracket,
            'Rate_VLife': self.Rate_VLife,
            'LastUpdated_Date': self.LastUpdated_Date.isoformat() if self.LastUpdated_Date else None,
            'Group_Name': self.Group_Name,
            'Group_PolicyNum': self.Group_PolicyNum
        }


class Group(Model):
    __tablename__ = 'tGroup'
    
    Group_ID = Column(String(6), primary_key=True, name="Group ID")
    Group_Name = Column(String(15), nullable=True, name="Group Name")
    Group_FullName = Column(String(50), nullable=True)
    Group_Contact_FName = Column(String(25), nullable=True)
    Group_Contact_LName = Column(String(35), nullable=True)
    Group_FEIN = Column(String(25), nullable=True)
    Group_Address = Column(String(100), nullable=True)
    Group_Phone = Column(String(10), nullable=True)
    Group_City = Column(String(25), nullable=True)
    Group_State = Column(String(25), nullable=True)
    Group_Zip = Column(String(12), nullable=True)
    Group_Country = Column(String(15), nullable=True)
    Group_Comments = Column(Text, nullable=True)
    Group_EMail = Column(String(100), nullable=True)

    def to_dict(self):
        return {
            'Group_ID': self.Group_ID,
            'Group_Name': self.Group_Name,
            'Group_FullName': self.Group_FullName,
            'Group_Contact_FName': self.Group_Contact_FName,
            'Group_Contact_LName': self.Group_Contact_LName,
            'Group_FEIN': self.Group_FEIN,
            'Group_Address': self.Group_Address,
            'Group_Phone': self.Group_Phone,
            'Group_City': self.Group_City,
            'Group_State': self.Group_State,
            'Group_Zip': self.Group_Zip,
            'Group_Country': self.Group_Country,
            'Group_Comments': self.Group_Comments,
            'Group_EMail': self.Group_EMail
        }
    
#for deleting dependent
class Dependent(Model):
    __tablename__ = 'XParticipant_Dependents'
    __table_args__ = {'schema': 'dbo'} 

    RowID = Column(Integer, primary_key=True)


class SavedFilter(Model):
    __tablename__ = 'SavedFilters'
    __table_args__ = {'schema': 'dbo'}
    
    Filter_ID = Column(Integer, primary_key=True, autoincrement=True)
    Filter_Name = Column(String(100), nullable=False)
    Filter_Configuration = Column(Text, nullable=False)  # JSON string
    User_ID = Column(String(10), nullable=False)
    Created_Date = Column(DateTime, nullable=False, default=datetime.datetime.now)
    LastModified_Date = Column(DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    Is_Active = Column(Boolean, nullable=False, default=True)

    def to_dict(self):
        return {
            'Filter_ID': self.Filter_ID,
            'Filter_Name': self.Filter_Name,
            'Filter_Configuration': self.Filter_Configuration,
            'User_ID': self.User_ID,
            'Created_Date': self.Created_Date.isoformat() if self.Created_Date else None,
            'LastModified_Date': self.LastModified_Date.isoformat() if self.LastModified_Date else None,
            'Is_Active': self.Is_Active
        }


class DocumentTemplate(Model):
    __tablename__ = 'tbl_Web_DocTemplates'
    
    RowID = Column(Integer, primary_key=True, autoincrement=True)
    DocGuid = Column(String(36), nullable=False)  # uniqueidentifier in SQL Server
    TemplateName = Column(String(64), nullable=False)
    FileName = Column(String(300), nullable=True)
    templateDesc = Column(String(300), nullable=True)
    SQLquery = Column(String(500), nullable=True)
    DocType = Column(String(10), nullable=True)
    SourceType = Column(String(20), nullable=True)
    ImageBlob = Column(LargeBinary, nullable=True)  # varbinary(max) in SQL Server
    DocumentSizeInMB = Column(String(15), nullable=True)
    UploadedDate = Column(DateTime, nullable=False, default=datetime.datetime.now)
    UploadedBy = Column(String(100), nullable=True)
    UpdatedDate = Column(DateTime, nullable=True, default=datetime.datetime.now)
    UpdatedBy = Column(String(100), nullable=True)
    RecordStatus = Column(Integer, nullable=False, default=1)
    Deleted = Column(Integer, nullable=True, default=0)
    DeletedDate = Column(DateTime, nullable=True)
    TemplateContent = Column(Text, nullable=True)  # nvarchar(max) in SQL Server

    def to_dict(self, include_blob=False):
        result = {
            'RowID': self.RowID,
            'DocGuid': self.DocGuid,
            'TemplateName': self.TemplateName,
            'FileName': self.FileName,
            'templateDesc': self.templateDesc,
            'SQLquery': self.SQLquery,
            'DocType': self.DocType,
            'SourceType': self.SourceType,
            'DocumentSizeInMB': self.DocumentSizeInMB,
            'UploadedDate': self.UploadedDate.isoformat() if self.UploadedDate else None,
            'UploadedBy': self.UploadedBy,
            'UpdatedDate': self.UpdatedDate.isoformat() if self.UpdatedDate else None,
            'UpdatedBy': self.UpdatedBy,
            'RecordStatus': self.RecordStatus,
            'Deleted': self.Deleted,
            'DeletedDate': self.DeletedDate.isoformat() if self.DeletedDate else None,
            'TemplateContent': self.TemplateContent
        }
        
        # Only include ImageBlob if explicitly requested
        if include_blob:
            result['ImageBlob'] = base64.b64encode(self.ImageBlob).decode('utf-8') if self.ImageBlob else None
            
        return result


class ParticipantCommunication(Model):
    __tablename__ = 'XParticipant_Communications'
    __table_args__ = {'schema': 'dbo'}

    RowID = Column(Integer, primary_key=True, autoincrement=True)
    Participant_Pkey = Column(String(20), nullable=False)
    EventDate = Column(Date, nullable=True)
    ComType = Column(String(10), nullable=True)
    Subject = Column(String(200), nullable=True)
    ComContent = Column(Text, nullable=True)
    ImageBlob = Column(LargeBinary, nullable=True)
    FileName = Column(String(300), nullable=True)
    Receiver = Column(String(100), nullable=True)
    CreatedDate = Column(DateTime, nullable=False)
    CreatedBy = Column(String(100), nullable=True)
    UpdatedDate = Column(DateTime, nullable=True)
    UpdatedBy = Column(String(100), nullable=True)
    RecordStatus = Column(Integer, nullable=False)
    DeletedFlag = Column(Boolean, nullable=True)

    def to_dict(self, include_blob=False):
        result = {
            'RowID': self.RowID,
            'Participant_Pkey': self.Participant_Pkey,
            'EventDate': self.EventDate.isoformat() if self.EventDate else None,
            'ComType': self.ComType,
            'Subject': self.Subject,
            'ComContent': self.ComContent,
            'FileName': self.FileName,
            'Receiver': self.Receiver,
            'CreatedDate': self.CreatedDate.isoformat() if self.CreatedDate else None,
            'CreatedBy': self.CreatedBy,
            'UpdatedDate': self.UpdatedDate.isoformat() if self.UpdatedDate else None,
            'UpdatedBy': self.UpdatedBy,
            'RecordStatus': self.RecordStatus,
            'DeletedFlag': self.DeletedFlag
        }

        # if include_blob:
        #     result['ImageBlob'] = base64.b64encode(self.ImageBlob).decode('utf-8') if self.ImageBlob else None

        return result
