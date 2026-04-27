# Saved Filters Database Implementation

## Overview

This implementation replaces the localStorage-based saved filters with a SQL Server database solution, providing better data persistence, user isolation, and management capabilities.

## Database Schema

### SavedFilters Table

```sql
CREATE TABLE dbo.SavedFilters (
    Filter_ID INT IDENTITY(1,1) PRIMARY KEY,
    Filter_Name NVARCHAR(100) NOT NULL,
    Filter_Configuration NTEXT NOT NULL,  -- JSON string
    User_ID NVARCHAR(10) NOT NULL,
    Created_Date DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    LastModified_Date DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    Is_Active BIT NOT NULL DEFAULT 1
)
```

### Indexes
- `IX_SavedFilters_UserID` on (User_ID, Is_Active)
- `IX_SavedFilters_LastModified` on (LastModified_Date DESC)

## API Endpoints

### GET /participants/saved_filters
- **Description**: Get all saved filters for the current user
- **Authentication**: Required
- **Response**: Array of filter objects

### POST /participants/saved_filters
- **Description**: Save a new filter
- **Authentication**: Required
- **Body**: 
  ```json
  {
    "name": "Filter Name",
    "groups": [/* filter configuration */]
  }
  ```

### PUT /participants/saved_filters/{filter_id}
- **Description**: Update an existing filter
- **Authentication**: Required
- **Body**: Same as POST

### DELETE /participants/saved_filters/{filter_id}
- **Description**: Delete a filter (soft delete)
- **Authentication**: Required

### GET /participants/saved_filters/{filter_id}
- **Description**: Get a specific filter by ID
- **Authentication**: Required

## Frontend Changes

### ParticipantsAdvanceFilter.jsx
- Replaced localStorage operations with API calls
- Added error handling for API operations
- Implemented automatic filter reloading

### FilterBuilder.jsx
- Updated to work with database-stored filters
- Added delete functionality with confirmation
- Enhanced UI with dropdown menus for filter actions
- Added filter selection tracking

## Key Features

### 1. User Isolation
- Each user can only see and manage their own saved filters
- Filters are associated with User_ID from the authentication system

### 2. Soft Delete
- Filters are marked as inactive rather than physically deleted
- Preserves data integrity and allows for potential recovery

### 3. Audit Trail
- Created_Date and LastModified_Date track filter lifecycle
- Useful for debugging and user support

### 4. Data Validation
- Server-side validation ensures data integrity
- Prevents duplicate filter names per user
- Validates filter configuration structure

### 5. Error Handling
- Comprehensive error handling on both frontend and backend
- User-friendly error messages
- Graceful fallback for network issues

## Migration from localStorage

### Automatic Migration
The system automatically loads filters from the database on page load. No manual migration is required.

### Data Structure Compatibility
The filter configuration structure remains the same, ensuring compatibility with existing filter logic.

## Security Considerations

### Authentication Required
All saved filter operations require user authentication.

### User Isolation
Users can only access their own saved filters.

### Input Validation
Server-side validation prevents malicious data injection.

### SQL Injection Protection
Uses parameterized queries to prevent SQL injection attacks.

## Performance Considerations

### Indexing
Database indexes optimize queries by User_ID and LastModified_Date.

### Pagination
Large filter lists can be paginated if needed in the future.

### Caching
Consider implementing Redis caching for frequently accessed filters.

## Usage Examples

### Saving a Filter
```javascript
const filterData = {
    name: "Active Users in NYC",
    groups: [{
        logicOperator: "AND",
        conditions: [{
            field: "Participant_Status",
            operator: "equals",
            value: "Active",
            enabled: true
        }, {
            field: "Participant_City",
            operator: "equals", 
            value: "New York",
            enabled: true
        }]
    }]
};

await axios.post('/participants/saved_filters', filterData);
```

### Loading Filters
```javascript
const response = await axios.get('/participants/saved_filters');
const filters = response.data.map(filter => ({
    ...filter,
    groups: JSON.parse(filter.Filter_Configuration)
}));
```

### Deleting a Filter
```javascript
await axios.delete(`/participants/saved_filters/${filterId}`);
```

## Troubleshooting

### Common Issues

1. **Filter not saving**
   - Check user authentication
   - Verify filter name is unique for the user
   - Check network connectivity

2. **Filters not loading**
   - Verify API endpoint is accessible
   - Check user permissions
   - Review browser console for errors

3. **Filter configuration errors**
   - Validate JSON structure
   - Check field and operator validity
   - Review server logs for validation errors

### Debug Information
- Check browser network tab for API calls
- Review server logs for backend errors
- Verify database table exists and has correct structure

## Future Enhancements

### Potential Improvements
1. **Filter Sharing**: Allow users to share filters with other users
2. **Filter Categories**: Add categorization for better organization
3. **Filter Templates**: Pre-defined filter templates for common use cases
4. **Filter Analytics**: Track filter usage and popularity
5. **Bulk Operations**: Delete multiple filters at once
6. **Filter Export/Import**: Export filters to JSON and import from JSON

### Performance Optimizations
1. **Caching**: Implement Redis caching for frequently accessed filters
2. **Pagination**: Add pagination for users with many saved filters
3. **Compression**: Compress filter configuration data
4. **Cleanup**: Periodic cleanup of inactive filters 