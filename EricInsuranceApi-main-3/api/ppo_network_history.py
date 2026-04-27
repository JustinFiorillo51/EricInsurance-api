from flask import Blueprint, current_app, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from db import Session as DBSession
from utils import login_required
from datetime import date

ppo_network_history_bp = Blueprint('ppo_network_history', __name__)

# Get PPO Network History
@ppo_network_history_bp.route('/<string:member_pkey>/<int:member_id>', methods=['GET'])
@login_required
def get_ppo_network_history(user, member_pkey, member_id):
    with DBSession() as session:
        try:
            result = session.execute(text('''
                SELECT *
                FROM XParticipant_PPO_Networks
                WHERE PPO_Member_Pkey = :pkey
                  AND PPO_Member_ID = :member_id
                ORDER BY PPO_Change_Seq ASC
            '''), {
                'pkey': member_pkey,
                'member_id': member_id
            }).mappings().all()

            return jsonify([dict(row) for row in result]), 200

        except Exception as e:
            current_app.logger.error(e)
            return jsonify({'error': 'Failed to fetch PPO network history'}), 500


# Update PPO Network History
@ppo_network_history_bp.route('/<int:row_id>', methods=['PUT'])
@login_required
def update_ppo_network_history(user, row_id):
    data = request.get_json()

    allowed_fields = [
        'PPO_Change_Seq',
        'PPO_BeginDate',
        'PPO_EndDate',
        'PPO_Network_01',
        'PPO_AccessPoint_01',
        'PPO_Network_02',
        'PPO_AccessPoint_02',
        'PPO_Network_03',
        'PPO_AccessPoint_03',
        'PPO_Comments',
    ]

    update_fields = {k: v for k, v in data.items() if k in allowed_fields}

    if not update_fields:
        return jsonify({'error': 'No valid fields provided'}), 400

    update_fields['RowID'] = row_id

    set_clause = ", ".join([f"{field} = :{field}" for field in update_fields if field != 'RowID'])

    try:
        with DBSession() as session:
            session.execute(text(f'''
                UPDATE dbo.XParticipant_PPO_Networks
                SET {set_clause}
                WHERE RowID = :RowID
            '''), update_fields)
            session.commit()
            return jsonify({'success': True}), 200

    except SQLAlchemyError as e:
        current_app.logger.error(e)
        return jsonify({'error': 'Database update failed'}), 500


# Add New PPO Network History
@ppo_network_history_bp.route('', methods=['POST'])
@login_required
def create_ppo_network_history(user):
    data = request.get_json()

    required_fields = [
        'PPO_Change_Seq',
        'PPO_Member_Pkey',
    ]

    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400

    insert_fields = {
        'PPO_Change_Seq': data.get('PPO_Change_Seq'),
        'PPO_BeginDate': data.get('PPO_BeginDate'),
        'PPO_EndDate': data.get('PPO_EndDate'),
        'PPO_Network_01': data.get('PPO_Network_01'),
        'PPO_AccessPoint_01': data.get('PPO_AccessPoint_01'),
        'PPO_Network_02': data.get('PPO_Network_02'),
        'PPO_AccessPoint_02': data.get('PPO_AccessPoint_02'),
        'PPO_Network_03': data.get('PPO_Network_03'),
        'PPO_AccessPoint_03': data.get('PPO_AccessPoint_03'),
        'PPO_Comments': data.get('PPO_Comments'),
        'PPO_Member_Pkey': data.get('PPO_Member_Pkey'),
        'PPO_Member_ID': data.get('PPO_Member_ID'),
    }

    columns = ', '.join(insert_fields.keys())
    values = ', '.join([f":{k}" for k in insert_fields.keys()])


    try:
        with DBSession() as session:
            session.execute(text(f'''
                INSERT INTO dbo.XParticipant_PPO_Networks (
                    {columns}
                )
                VALUES (
                    {values}
                )
            '''), insert_fields)
            session.commit()
            return jsonify({'success': True}), 201

    except SQLAlchemyError as e:
        current_app.logger.error(e)
        return jsonify({'error': 'Database insert failed'}), 500


# Delete PPO Network History Record
@ppo_network_history_bp.route('/<int:row_id>', methods=['DELETE'])
@login_required
def delete_ppo_network_history(user, row_id):
    try:
        with DBSession() as session:
            session.execute(text('''
                DELETE FROM dbo.XParticipant_PPO_Networks
                WHERE RowID = :row_id
            '''), {'row_id': row_id})
            session.commit()
        return jsonify({'success': True}), 200

    except SQLAlchemyError as e:
        current_app.logger.error(e)
        return jsonify({'error': 'Database delete failed'}), 500


@ppo_network_history_bp.route('/people/<string:participant_pkey>', methods=['GET'])
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

@ppo_network_history_bp.route('/participant/<string:participant_pkey>', methods=['GET'])
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

#get dropdown values
@ppo_network_history_bp.route('/ppo_networks', methods=['GET'])
@login_required
def get_ppo_networks(user):
    with DBSession() as session:
        try:
            result = session.execute(text("""
                SELECT DISTINCT val FROM (
                    SELECT PPO_Network_01 AS val FROM XParticipant_PPO_Networks
                    UNION
                    SELECT PPO_Network_02 FROM XParticipant_PPO_Networks
                    UNION
                    SELECT PPO_Network_03 FROM XParticipant_PPO_Networks
                ) AS combined
                WHERE val IS NOT NULL
            """)).fetchall()

            cleaned = sorted(set(row[0].strip() for row in result if row[0]))

            return jsonify([{'label': val, 'value': val} for val in cleaned])
        except Exception as e:
            current_app.logger.error(e)
            return jsonify({'error': 'Failed to load PPO networks'}), 500


@ppo_network_history_bp.route('/ppo_access_points', methods=['GET'])
@login_required
def get_ppo_access_points(user):
    with DBSession() as session:
        try:
            result = session.execute(text("""
                SELECT DISTINCT val FROM (
                    SELECT PPO_AccessPoint_01 AS val FROM XParticipant_PPO_Networks
                    UNION
                    SELECT PPO_AccessPoint_02 FROM XParticipant_PPO_Networks
                    UNION
                    SELECT PPO_AccessPoint_03 FROM XParticipant_PPO_Networks
                ) AS combined
                WHERE val IS NOT NULL
            """)).fetchall()

            cleaned = sorted(set(row[0].strip() for row in result if row[0]))

            return jsonify([{'label': val, 'value': val} for val in cleaned])
        except Exception as e:
            current_app.logger.error(e)
            return jsonify({'error': 'Failed to load PPO access points'}), 500
