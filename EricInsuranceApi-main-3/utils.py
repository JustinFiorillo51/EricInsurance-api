from functools import wraps

from flask import jsonify, request, current_app
from db import Session as DBSession
from models import User

def get_user_by_session_id(session_id) -> User:
    with DBSession() as session:
        user = session.query(User).filter(User.User_Session_ID == session_id).first()
        return user
    
def get_user_json_by_session_id(session_id) -> dict:
    user = get_user_by_session_id(session_id)
    return user.to_dict() if user else None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_id = request.headers.get('User-Session-ID')
        if not session_id:
            session_id = request.args.get('User-Session-ID')
            if not session_id:
                return jsonify({'error': 'No session ID provided'}), 401
        try:
            user = get_user_json_by_session_id(session_id)
            if not user:
                return jsonify({'error': 'Invalid session ID'}), 401
        except Exception as e:
            current_app.logerr(e)
            return jsonify({'error': 'An internal error has occurred'}), 500
            
        return f(user, *args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(user, *args, **kwargs):
        if user['User_Level'] != 1:
            return jsonify({'error': 'Unauthorized'}), 403
        return f(user, *args, **kwargs)
    return decorated_function


def build_where_clause(filter_criteria, sql_params):
    """
    Build SQL WHERE clause
    """
    if not filter_criteria or not filter_criteria.get('groups'):
        return '1=1'  # If no filter criteria, return all records
    
    groups = filter_criteria['groups']
    group_clauses = []
    group_logic_operators = []
    
    for i, group in enumerate(groups):
        if not group.get('conditions'):
            continue
            
        conditions = group['conditions']
        condition_clauses = []
        
        for j, condition in enumerate(conditions):
            if not condition.get('enabled', True):
                continue
                
            field = condition.get('field')
            operator = condition.get('operator')
            value = condition.get('value')
            value2 = condition.get('value2')
            
            if not field or not operator:
                continue
                
            # Validate field is valid
            if field not in FIELD_DEFINITIONS:
                continue
                
            field_def = FIELD_DEFINITIONS[field]
            if operator not in field_def['operators']:
                continue
                
            # Generate parameter names
            param_name = f"param_{len(sql_params)}"
            param_name2 = f"param_{len(sql_params) + 1}" if operator == 'between' else None
            
            # Build condition clause
            if operator == 'in':
                # For IN operator, we need to build the clause differently
                # Ensure value is a list
                if isinstance(value, list):
                    in_values = value
                elif isinstance(value, str):
                    # If it's a string, split by comma and trim whitespace
                    in_values = [v.strip() for v in value.split(',') if v.strip()]
                else:
                    # Single value
                    in_values = [value]
                condition_clause = build_in_clause(field, in_values, sql_params)
            else:
                condition_clause = build_condition_clause(field, operator, param_name, param_name2)
            
            if condition_clause:
                condition_clauses.append(condition_clause)
                
                # Add parameter values
                if operator in ['is_empty', 'is_not_empty']:
                    pass  # No parameters needed
                elif operator == 'between':
                    sql_params[param_name] = value
                    sql_params[param_name2] = value2
                elif operator == 'in':
                    # Handle IN operator - value should be a list
                    # Parameters are handled in build_in_clause function
                    pass
                    

                elif operator in ['contains', 'starts_with', 'ends_with']:
                    # Handle string search
                    if operator == 'contains':
                        sql_params[param_name] = f'%{value}%'
                    elif operator == 'starts_with':
                        sql_params[param_name] = f'{value}%'
                    elif operator == 'ends_with':
                        sql_params[param_name] = f'%{value}'
                else:
                    sql_params[param_name] = value
        
        if condition_clauses:
            # Handle logic operators between conditions
            if len(condition_clauses) == 1:
                group_clause = f" ({condition_clauses[0]})"
            else:
                # Get logic operators for each condition
                conditions = [c for c in group['conditions'] if c.get('enabled', True)]
                logic_operators = []
                for j, condition in enumerate(conditions):
                    if j > 0:  # First condition doesn't need logic operator
                        logic_operators.append(condition.get('conditionLogicOperator', 'AND'))
                
                # Build condition combination
                combined_clause = condition_clauses[0]
                for j, (clause, logic_op) in enumerate(zip(condition_clauses[1:], logic_operators)):
                    combined_clause += f" {logic_op} {clause}"
                
                group_clause = f" ({combined_clause})"
            
            group_clauses.append(group_clause)
            
            # Store the logic operator for this group (for connecting to next group)
            if i > 0:  # First group doesn't need logic operator
                group_logic_operators.append(group.get('logicOperator', 'AND'))
    
    if not group_clauses:
        return '1=1'
    
    # Combine groups with their logic operators
    if len(group_clauses) == 1:
        return group_clauses[0]
    else:
        combined_clause = group_clauses[0]
        for i, (clause, logic_op) in enumerate(zip(group_clauses[1:], group_logic_operators)):
            combined_clause += f" {logic_op} {clause}"
        return combined_clause


def build_condition_clause(field, operator, param_name, param_name2=None):
    """
    Build SQL clause for a single condition
    """
    field_name = f"T1.[{field}]"
    
    if operator == 'equals':
        return f"{field_name} = :{param_name}"
    elif operator == 'contains':
        return f"{field_name} LIKE :{param_name}"
    elif operator == 'starts_with':
        return f"{field_name} LIKE :{param_name}"
    elif operator == 'ends_with':
        return f"{field_name} LIKE :{param_name}"
    elif operator == 'greater_than':
        return f"{field_name} > :{param_name}"
    elif operator == 'less_than':
        return f"{field_name} < :{param_name}"
    elif operator == 'between':
        return f"{field_name} BETWEEN :{param_name} AND :{param_name2}"
    elif operator == 'in':
        return f"{field_name} IN :{param_name}"
    elif operator == 'is_empty':
        return f"({field_name} IS NULL OR {field_name} = '')"
    elif operator == 'is_not_empty':
        return f"({field_name} IS NOT NULL AND {field_name} != '')"
    
    return None


def build_in_clause(field, values, sql_params):
    """
    Build SQL IN clause with individual parameters for each value
    """
    field_name = f"T1.[{field}]"
    
    if not values:
        return None
    
    # Ensure values is a list
    if not isinstance(values, list):
        values = [values]
    
    if len(values) == 1:
        # Single value - use equals instead of IN
        param_name = f"param_{len(sql_params)}"
        sql_params[param_name] = values[0]
        return f"{field_name} = :{param_name}"
    
    # Multiple values - build IN clause with individual parameters
    param_names = []
    for i, value in enumerate(values):
        param_name = f"param_{len(sql_params)}"
        param_names.append(f":{param_name}")
        sql_params[param_name] = value
    
    param_list = ', '.join(param_names)
    return f"{field_name} IN ({param_list})"


# Field definitions (for validation)
FIELD_DEFINITIONS = {
    'Name': {'type': 'string', 'operators': ['equals', 'contains', 'starts_with', 'ends_with', 'in', 'is_empty', 'is_not_empty']},
    'Participant_ID': {'type': 'string', 'operators': ['equals', 'contains', 'starts_with', 'ends_with', 'in', 'is_empty', 'is_not_empty']},
    'Participant_SSN': {'type': 'string', 'operators': ['equals', 'contains', 'starts_with', 'ends_with', 'in', 'is_empty', 'is_not_empty']},
    'Participant_Group_Name': {'type': 'string', 'operators': ['equals', 'contains', 'starts_with', 'ends_with', 'in', 'is_empty', 'is_not_empty']},
    'Participant_BirthDate': {'type': 'date', 'operators': ['equals', 'greater_than', 'less_than', 'between', 'is_empty', 'is_not_empty']},
    'Participant_HireDate': {'type': 'date', 'operators': ['equals', 'greater_than', 'less_than', 'between', 'is_empty', 'is_not_empty']},
    'Participant_BLife_EffectiveDate': {'type': 'date', 'operators': ['equals', 'greater_than', 'less_than', 'between', 'is_empty', 'is_not_empty']},
    'Participant_TermDate': {'type': 'date', 'operators': ['equals', 'greater_than', 'less_than', 'between', 'is_empty', 'is_not_empty']},
    'Participant_City': {'type': 'string', 'operators': ['equals', 'contains', 'starts_with', 'ends_with', 'in', 'is_empty', 'is_not_empty']},
    'Participant_State': {'type': 'string', 'operators': ['equals', 'contains', 'starts_with', 'ends_with', 'in', 'is_empty', 'is_not_empty']},
    'Participant_Address': {'type': 'string', 'operators': ['equals', 'contains', 'starts_with', 'ends_with', 'in', 'is_empty', 'is_not_empty']},
    'Participant_Zip': {'type': 'string', 'operators': ['equals', 'contains', 'starts_with', 'ends_with', 'in', 'is_empty', 'is_not_empty']},
    'Participant_Phone_Home': {'type': 'string', 'operators': ['equals', 'contains', 'starts_with', 'ends_with', 'in', 'is_empty', 'is_not_empty']},
    'Participant_Status': {'type': 'string', 'operators': ['equals', 'contains', 'starts_with', 'ends_with', 'in', 'is_empty', 'is_not_empty']},
    'Participant_Payments_YN': {'type': 'boolean', 'operators': ['equals']},
    'Participant_Age': {'type': 'number', 'operators': ['equals', 'greater_than', 'less_than', 'between', 'in', 'is_empty', 'is_not_empty']},
    'Participant_Total_Premiums': {'type': 'number', 'operators': ['equals', 'greater_than', 'less_than', 'between', 'in', 'is_empty', 'is_not_empty']},
    'Participant_OptOut_Eligible_YN': {'type': 'boolean', 'operators': ['equals']},
    
    'Participant_BeginDate': {'type': 'date', 'operators': ['equals', 'greater_than', 'less_than', 'between', 'is_empty', 'is_not_empty']},
    'Participant_Reconcile_Date': {'type': 'date', 'operators': ['equals', 'greater_than', 'less_than', 'between', 'is_empty', 'is_not_empty']},
    'Participant_MED_EffectiveDate': {'type': 'date', 'operators': ['equals', 'greater_than', 'less_than', 'between', 'is_empty', 'is_not_empty']},
    'Participant_DEN_EffectiveDate': {'type': 'date', 'operators': ['equals', 'greater_than', 'less_than', 'between', 'is_empty', 'is_not_empty']},
    'Participant_VIS_EffectiveDate': {'type': 'date', 'operators': ['equals', 'greater_than', 'less_than', 'between', 'is_empty', 'is_not_empty']},
    'Participant_VLife_EffectiveDate': {'type': 'date', 'operators': ['equals', 'greater_than', 'less_than', 'between', 'is_empty', 'is_not_empty']},
    'Participant_Coverage_OptOut_YN': {'type': 'boolean', 'operators': ['equals']},
    'Participant_OptOut_BeginDate': {'type': 'date', 'operators': ['equals', 'greater_than', 'less_than', 'between', 'is_empty', 'is_not_empty']},
    'Participant_OptOut_EndDate': {'type': 'date', 'operators': ['equals', 'greater_than', 'less_than', 'between', 'is_empty', 'is_not_empty']},
}

# MIME types for different file extensions
MIME_TYPES = {
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'xls': 'application/vnd.ms-excel',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'txt': 'text/plain',
    'html': 'text/html'
}


def convert_sql_result_to_dict(data, row_index=0):
    """
    Convert SQL query result to dictionary format
    
    Args:
        data: SQL query results (SQLAlchemy result, list, tuple, etc.)
        row_index: Index of the row to convert (default: 0 for first row)
    
    Returns:
        dict: Dictionary representation of the data row
    """
    try:
        # Handle None or empty data
        if not data:
            return {}
        
        # If data is already a dictionary-like object
        if hasattr(data, 'keys'):
            return dict(data)
        
        # If data is iterable (like SQLAlchemy result)
        if hasattr(data, '__iter__') and not isinstance(data, str):
            data_list = list(data)
            
            if not data_list:
                return {}
            
            # Ensure row_index is within bounds
            if row_index >= len(data_list):
                return {}
            
            row_data = data_list[row_index]
            
            # Handle SQLAlchemy Row object
            if hasattr(row_data, '_asdict'):
                return row_data._asdict()
            
            # Handle dictionary-like object
            elif hasattr(row_data, 'keys'):
                return dict(row_data)
            
            # Handle tuple or list (convert to dictionary with field names if available)
            elif isinstance(row_data, (tuple, list)):
                result_dict = {}
                
                # Try to get column names from the result object
                if hasattr(data, 'keys'):
                    # SQLAlchemy result with column names
                    column_names = list(data.keys())
                    for i, value in enumerate(row_data):
                        if i < len(column_names):
                            result_dict[column_names[i]] = str(value) if value is not None else ''
                        else:
                            result_dict[f'field_{i}'] = str(value) if value is not None else ''
                else:
                    # No column names available, use generic field names
                    for i, value in enumerate(row_data):
                        result_dict[f'field_{i}'] = str(value) if value is not None else ''
                
                return result_dict
        
        # If data is a single value
        elif isinstance(data, (str, int, float, bool)):
            return {'value': str(data)}
        
        # Default case
        return {}
        
    except Exception as e:
        # Log error and return empty dict
        import logging
        logging.error(f"Error converting SQL result to dict: {str(e)}")
        return {}


def convert_sql_result_to_list_of_dicts(data):
    """
    Convert SQL query result to list of dictionaries
    
    Args:
        data: SQL query results (SQLAlchemy result, list, tuple, etc.)
    
    Returns:
        list: List of dictionaries, each representing a row
    """
    try:
        # Handle None or empty data
        if not data:
            return []
        
        # If data is already a list of dictionaries
        if isinstance(data, list) and data and hasattr(data[0], 'keys'):
            return [dict(row) for row in data]
        
        # If data is iterable (like SQLAlchemy result)
        if hasattr(data, '__iter__') and not isinstance(data, str):
            data_list = list(data)
            
            if not data_list:
                return []
            
            result_list = []
            
            # Try to get column names from the result object
            column_names = None
            if hasattr(data, 'keys'):
                column_names = list(data.keys())
            
            for row_data in data_list:
                # Handle SQLAlchemy Row object
                if hasattr(row_data, '_asdict'):
                    result_list.append(row_data._asdict())
                
                # Handle dictionary-like object
                elif hasattr(row_data, 'keys'):
                    result_list.append(dict(row_data))
                
                # Handle tuple or list
                elif isinstance(row_data, (tuple, list)):
                    row_dict = {}
                    
                    if column_names:
                        # Use column names if available
                        for i, value in enumerate(row_data):
                            if i < len(column_names):
                                row_dict[column_names[i]] = str(value) if value is not None else ''
                            else:
                                row_dict[f'field_{i}'] = str(value) if value is not None else ''
                    else:
                        # Use generic field names
                        for i, value in enumerate(row_data):
                            row_dict[f'field_{i}'] = str(value) if value is not None else ''
                    
                    result_list.append(row_dict)
            
            return result_list
        
        # If data is a single value, wrap it in a list
        elif isinstance(data, (str, int, float, bool)):
            return [{'value': str(data)}]
        
        # Default case
        return []
        
    except Exception as e:
        # Log error and return empty list
        import logging
        logging.error(f"Error converting SQL result to list of dicts: {str(e)}")
        return []


def validate_sql_query(sql_query):
    """
    Validate SQL query to ensure it only contains SELECT statements
    and prevent SQL injection attacks
    
    Args:
        sql_query (str): The SQL query to validate
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not sql_query or not isinstance(sql_query, str):
        return False, "SQL query must be a non-empty string"
    
    # Convert to uppercase for easier checking
    query_upper = sql_query.strip().upper()
    
    # Check for dangerous SQL keywords that could modify data
    # Use word boundaries to avoid false positives
    dangerous_keywords = [
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 
        'TRUNCATE', 'EXEC', 'EXECUTE', 'EXECUTE IMMEDIATE',
        'MERGE', 'UPSERT', 'REPLACE', 'GRANT', 'REVOKE'
    ]
    
    for keyword in dangerous_keywords:
        # Use word boundary check to avoid false positives like COUNT(*) containing CREATE
        import re
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, query_upper):
            return False, f"SQL query contains forbidden keyword: {keyword}"
    
    # Ensure query starts with SELECT
    if not query_upper.startswith('SELECT'):
        return False, "SQL query must start with SELECT"
    
    # Check for multiple statements (semicolon separated)
    if ';' in sql_query and sql_query.count(';') > 1:
        return False, "Multiple SQL statements are not allowed"
    
    # Check for common SQL injection patterns
    injection_patterns = [
        'UNION SELECT', 'UNION ALL SELECT', 'UNION DISTINCT SELECT',
        'OR 1=1', 'OR 1=1--', 'OR 1=1/*', 'OR 1=1#',
        'AND 1=1', 'AND 1=1--', 'AND 1=1/*', 'AND 1=1#',
        '--', '/*', '*/', 'XP_', 'SP_', 'WAITFOR',
        'BENCHMARK', 'SLEEP', 'PG_SLEEP'
    ]
    
    for pattern in injection_patterns:
        if pattern in query_upper:
            return False, f"SQL query contains potentially dangerous pattern: {pattern}"
    
    # Check for stacked queries (multiple statements)
    if ';' in sql_query:
        statements = [stmt.strip() for stmt in sql_query.split(';') if stmt.strip()]
        if len(statements) > 1:
            return False, "Multiple SQL statements are not allowed"
    
    return True, "SQL query is valid"

