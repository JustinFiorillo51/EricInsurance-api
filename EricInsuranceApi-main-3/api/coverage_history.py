from flask import Blueprint, current_app, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from db import Session as DBSession
from utils import login_required
from datetime import date

coverage_history_bp = Blueprint('coverage_history', __name__)

#get coverage history
@coverage_history_bp.route('/<string:participant_pkey>/<int:participant_id>', methods=['GET'])
@login_required
def get_coverage_history(user, participant_pkey, participant_id):
    with DBSession() as session:
        try:
            result = session.execute(text('''
                SELECT *
                FROM XParticipant_Coverage_History
                WHERE Coverage_Participant_Pkey = :pkey
                  AND Coverage_Participant_ID = :participant_id
                ORDER BY Coverage_Change_Seq ASC
            '''), {
                'pkey': participant_pkey,
                'participant_id': participant_id
            }).mappings().all()

            return jsonify([dict(row) for row in result]), 200

        except Exception as e:
            current_app.logger.error(e)
            return jsonify({'error': 'Failed to fetch coverage history'}), 500



#update coverage history
@coverage_history_bp.route('/<int:row_id>', methods=['PUT'])
@login_required
def update_coverage_history(user, row_id):
    data = request.get_json()

    allowed_fields = [
        'Coverage_Change_SEQ',
        'Coverage_SingleOrFam',
        'Coverage_Type',
        'Coverage_Type_BeginDate',
        'Coverage_Type_EndDate',
        'Coverage_Medical_BeginDate',
        'Coverage_Medical_EndDate',
        'Coverage_Dental_BeginDate',
        'Coverage_Dental_EndDate',
        'Coverage_Vision_BeginDate',
        'Coverage_Vision_EndDate',
        'Coverage_Notes',
    ]

    update_fields = {k: v for k, v in data.items() if k in allowed_fields}

    if not update_fields:
        return jsonify({'error': 'No valid fields provided'}), 400

    #updated by
    update_fields['Coverage_LastUpdated_By'] = user.get('name') or 'System'
    update_fields['RowID'] = row_id

    set_clause = ", ".join([f"{field} = :{field}" for field in update_fields if field != 'RowID'])

    try:
        with DBSession() as session:
            query = text(f'''
                UPDATE dbo.XParticipant_Coverage_History
                SET {set_clause},
                    Coverage_LastUpdated_Date = GETDATE()
                WHERE RowID = :RowID
            ''')
            session.execute(query, update_fields)
            session.commit()
        return jsonify({'success': True}), 200

    except SQLAlchemyError as e:
        current_app.logerr(e)
        return jsonify({'error': 'Database update failed'}), 500

#add new

@coverage_history_bp.route('', methods=['POST'])  
@login_required
def create_coverage_history(user):
    current_app.logger.warning(f"User object: {user}")
    data = request.get_json()

    required_fields = [
        'Coverage_Change_Seq',
        'Coverage_SingleOrFam',
        'Coverage_Type',
        'Coverage_Participant_Pkey'
    ]

    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400

    insert_fields = {
        'Coverage_Change_Seq': data.get('Coverage_Change_Seq'),
        'Coverage_SingleOrFam': data.get('Coverage_SingleOrFam'),
        'Coverage_Type': data.get('Coverage_Type'),
        'Coverage_Type_BeginDate': data.get('Coverage_Type_BeginDate'),
        'Coverage_Type_EndDate': data.get('Coverage_Type_EndDate'),
        'Coverage_Medical_BeginDate': data.get('Coverage_Medical_BeginDate'),
        'Coverage_Medical_EndDate': data.get('Coverage_Medical_EndDate'),
        'Coverage_Dental_BeginDate': data.get('Coverage_Dental_BeginDate'),
        'Coverage_Dental_EndDate': data.get('Coverage_Dental_EndDate'),
        'Coverage_Vision_BeginDate': data.get('Coverage_Vision_BeginDate'),
        'Coverage_Vision_EndDate': data.get('Coverage_Vision_EndDate'),
        'Coverage_BLife_BeginDate': data.get('Coverage_BLife_BeginDate'),
        'Coverage_BLife_EndDate': data.get('Coverage_BLife_EndDate'),
        'Coverage_VLife_BeginDate': data.get('Coverage_VLife_BeginDate'),
        'Coverage_VLife_EndDate': data.get('Coverage_VLife_EndDate'),
        'Coverage_Notes': data.get('Coverage_Notes'),
        'Coverage_Participant_Pkey': data.get('Coverage_Participant_Pkey'),
        'Coverage_Participant_ID': data.get('Coverage_Participant_ID'),
        'Coverage_LastUpdated_By': user.get('name') or 'System'

    }

    columns = ', '.join(insert_fields.keys())
    values = ', '.join([f":{k}" for k in insert_fields])

    try:
        with DBSession() as session:
            session.execute(text(f'''
                INSERT INTO dbo.XParticipant_Coverage_History (
                    {columns},
                    Coverage_LastUpdated_Date
                )
                VALUES (
                    {values},
                    GETDATE()
                )
            '''), insert_fields)
            session.commit()
            return jsonify({'success': True}), 201

    except SQLAlchemyError as e:
        current_app.logerr(e)
        return jsonify({'error': 'Database insert failed'}), 500




#get drop down values
@coverage_history_bp.route('/options', methods=['GET'])
@login_required
def get_coverage_history_options(user):
    with DBSession() as session:
        try:
            categories_result = session.execute(text("""
                SELECT DISTINCT Coverage_Type
                FROM XParticipant_Coverage_History
                WHERE Coverage_Type IS NOT NULL
                ORDER BY Coverage_Type
            """)).fetchall()

            types_result = session.execute(text("""
                SELECT DISTINCT Coverage_SingleOrFam
                FROM XParticipant_Coverage_History
                WHERE Coverage_SingleOrFam IS NOT NULL
                ORDER BY Coverage_SingleOrFam
            """)).fetchall()
                                    #for weird extra values in singleorfam
            valid_type_labels = {
                'S': 'Single',
                'F': 'Family',
            }

            type_options = [
                {'value': val, 'label': valid_type_labels[val]}
                for (val,) in types_result
                if val in valid_type_labels
            ]

            category_options = [
                {'value': val, 'label': val}
                for (val,) in categories_result
            ]

            return jsonify({
                'categories': category_options,
                'types': type_options
            })

        except Exception as e:
            current_app.logger.error(e)
            return jsonify({'error': 'Failed to load coverage history options'}), 500

#delete 

@coverage_history_bp.route('/<int:row_id>', methods=['DELETE'])
@login_required
def delete_coverage_history(user, row_id):
    try:
        with DBSession() as session:
            session.execute(text('''
                DELETE FROM dbo.XParticipant_Coverage_History
                WHERE RowID = :row_id
            '''), {'row_id': row_id})
            session.commit()
        return jsonify({'success': True}), 200
    except SQLAlchemyError as e:
        current_app.logerr(e)
        return jsonify({'error': 'Database delete failed'}), 500

#get for top values

@coverage_history_bp.route('/people/<string:participant_pkey>', methods=['GET'])
@login_required
def get_all_people(user, participant_pkey):
    with DBSession() as session:
        try:
            participant_result = session.execute(text("""
                SELECT
                    Participant_Pkey AS Pkey,
                    NULL AS RowID,
                    Participant_FirstName AS FirstName,
                    Participant_MiddleInit AS MiddleName,
                    Participant_LastName AS LastName,
                    'Employee' AS Role,
                    Participant_BirthDate AS BirthDate,
                    Participant_Gender AS Gender,
                    Participant_SSN AS SSN
                FROM XParticipant
                WHERE Participant_Pkey = :pkey
            """), {'pkey': participant_pkey}).mappings().fetchone()

            people = []
            if participant_result:
                birth = participant_result['BirthDate']
                people.append({
                    'RowID': None,
                    'Pkey': participant_result['Pkey'],
                    'FirstName': participant_result['FirstName'],
                    'MiddleName': participant_result['MiddleName'],
                    'LastName': participant_result['LastName'],
                    'Role': 'Employee',
                    'BirthDate': birth.strftime('%m/%d/%Y') if birth else None,
                    'Age': calculate_age(birth) if birth else None,
                    'Gender': participant_result['Gender'],
                    'SSN': str(int(participant_result['SSN'])).zfill(9) if participant_result['SSN'] else None,
                })

            dependent_result = session.execute(text("""
                SELECT
                    RowID,
                    Depend_Pkey AS Pkey,
                    Depend_FirstName AS FirstName,
                    Depend_MiddleName AS MiddleName,
                    Depend_LastName AS LastName,
                    Depend_Relation AS Role,
                    Depend_BirthDate AS BirthDate,
                    Depend_Gender AS Gender,
                    Depend_SSN AS SSN
                FROM XParticipant_Dependents
                WHERE Depend_Pkey = :pkey
            """), {'pkey': participant_pkey}).mappings()

            for row in dependent_result:
                birth = row['BirthDate']
                people.append({
                    'RowID': row['RowID'],
                    'Pkey': row['Pkey'],
                    'FirstName': row['FirstName'],
                    'MiddleName': row['MiddleName'],
                    'LastName': row['LastName'],
                    'Role': row['Role'],
                    'BirthDate': birth.strftime('%m/%d/%Y') if birth else None,
                    'Age': calculate_age(birth) if birth else None,
                    'Gender': row['Gender'],
                    'SSN': str(int(row['SSN'])).zfill(9) if row['SSN'] else None,
                })

            return jsonify(people), 200

        except Exception as e:
            current_app.logger.error(f"Failed to load participant and dependents: {e}", exc_info=True)
            return jsonify({'error': 'Failed to load family members'}), 500
        
def calculate_age(birthdate):
    today = date.today()
    return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

#get header

@coverage_history_bp.route('/participant/<string:participant_pkey>', methods=['GET'])
@login_required
def get_participant_info(user, participant_pkey):
    with DBSession() as session:
        try:
            result = session.execute(text('''
                SELECT *
                FROM XParticipant
                WHERE Participant_Pkey = :pkey
            '''), {'pkey': participant_pkey}).mappings().fetchone()

            if not result:
                return jsonify({'error': 'Participant not found'}), 404

            participant = dict(result)
            participant['Participant_ID'] = 0 
            participant['Participant_Age'] = calculate_age(result['Participant_BirthDate']) if result['Participant_BirthDate'] else None
            participant['Participant_BirthDate'] = result['Participant_BirthDate'].strftime('%m/%d/%Y') if result['Participant_BirthDate'] else None
            participant['Participant_Hire_Date'] = result['Participant_HireDate'].strftime('%m/%d/%Y') if result['Participant_HireDate'] else None
            participant['Coverage_Begin_Date'] = result['Participant_BeginDate'].strftime('%m/%d/%Y') if result['Participant_BeginDate'] else None
            participant['Coverage_Term_Date'] = result['Participant_TermDate'].strftime('%m/%d/%Y') if result['Participant_TermDate'] else None

            return jsonify(participant), 200
        except Exception as e:
            current_app.logger.error(e)
            return jsonify({'error': 'Failed to fetch participant info'}), 500
