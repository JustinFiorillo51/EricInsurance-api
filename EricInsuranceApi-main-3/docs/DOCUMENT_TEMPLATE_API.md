# Document Template API

This API provides CRUD operations for document templates stored in the `tbl_Web_DocTemplates` table.

## Base URL
```
/api/admin/document_template
```

## Authentication
All endpoints require authentication and admin privileges.

## Endpoints

### 1. Create Document Template
**POST** `/api/admin/document_template/`

Creates a new document template.

**Request Body:**
```json
{
    "FileName": "template.pdf",
    "templateDesc": "Document template description",
    "SQLquery": "SELECT * FROM table",
    "DocType": "PDF",
    "ImageBlob": "base64_encoded_binary_data",
    "DocumentSizeInMB": "2.5",
    "UploadedBy": "user_id",
    "UpdatedBy": "user_id",
    "RecordStatus": 1,
    "Deleted": 0
}
```

**Response:**
- `201`: Document template created successfully
- `400`: Invalid parameters
- `500`: Internal server error

### 2. Get All Document Templates
**GET** `/api/admin/document_template/`

Retrieves all non-deleted document templates.

**Response:**
- `200`: List of document templates
- `500`: Internal server error

### 3. Get Specific Document Template
**GET** `/api/admin/document_template/{row_id}`

Retrieves a specific document template by RowID.

**Response:**
- `200`: Document template data
- `404`: Document template not found
- `500`: Internal server error

### 4. Update Document Template
**PUT** `/api/admin/document_template/{row_id}`

Updates an existing document template.

**Request Body:**
```json
{
    "FileName": "updated_template.pdf",
    "templateDesc": "Updated description",
    "UpdatedBy": "user_id"
}
```

**Response:**
- `200`: Document template updated successfully
- `400`: No data provided
- `404`: Document template not found
- `500`: Internal server error

### 5. Delete Document Template (Soft Delete)
**DELETE** `/api/admin/document_template/{row_id}`

Performs a soft delete by setting the `Deleted` field to 1 and `DeletedDate` to current timestamp.

**Response:**
- `200`: Document template deleted successfully
- `404`: Document template not found
- `500`: Internal server error

## Database Schema

The API operates on the `tbl_Web_DocTemplates` table with the following structure:

| Column | Type | Description |
|--------|------|-------------|
| RowID | int | Primary key, auto-increment |
| DocGuid | uniqueidentifier | Unique document identifier |
| FileName | nvarchar(300) | Name of the template file |
| templateDesc | nvarchar(300) | Template description |
| SQLquery | varchar(500) | SQL query for the template |
| DocType | nchar(10) | Document type (e.g., PDF, DOC) |
| ImageBlob | varbinary(max) | Binary data of the template |
| DocumentSizeInMB | nvarchar(15) | File size in MB |
| UploadedDate | datetime | Upload timestamp |
| UploadedBy | nvarchar(100) | User who uploaded |
| UpdatedDate | datetime | Last update timestamp |
| UpdatedBy | nvarchar(100) | User who last updated |
| RecordStatus | int | Record status (1 = active) |
| Deleted | int | Soft delete flag (0 = active, 1 = deleted) |
| DeletedDate | datetime | Soft delete timestamp |

## Important Notes

1. **Soft Delete**: The delete operation is a soft delete that sets `Deleted = 1` instead of physically removing the record.

2. **Filtering**: All GET operations automatically filter out records where `Deleted = 1`.

3. **GUID Generation**: The `DocGuid` field is automatically generated using UUID4 when creating new templates.

4. **Timestamps**: `UploadedDate` and `UpdatedDate` are automatically managed by the API.

5. **Binary Data**: The `ImageBlob` field stores binary data and should be handled appropriately in client applications.

## Example Usage

### Create a template:
```bash
curl -X POST http://localhost:5001/api/admin/document_template/ \
  -H "Content-Type: application/json" \
  -d '{
    "FileName": "insurance_policy.pdf",
    "templateDesc": "Standard insurance policy template",
    "SQLquery": "SELECT * FROM policy_data WHERE status = 'active'",
    "DocType": "PDF",
    "DocumentSizeInMB": "1.2",
    "UploadedBy": "admin_user"
  }'
```

### Get all templates:
```bash
curl -X GET http://localhost:5001/api/admin/document_template/
```

### Update a template:
```bash
curl -X PUT http://localhost:5001/api/admin/document_template/100 \
  -H "Content-Type: application/json" \
  -d '{
    "FileName": "updated_policy.pdf",
    "templateDesc": "Updated insurance policy template"
  }'
```

### Delete a template:
```bash
curl -X DELETE http://localhost:5001/api/admin/document_template/100
``` 