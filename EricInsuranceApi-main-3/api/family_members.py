from re import search
from flask import Blueprint, current_app, request, jsonify
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from db import Session as DBSession
from datetime import date
from models import Dependent
import sys

from utils import login_required


family_members_bp = Blueprint('family_members', __name__)


# get all members
@family_members_bp.route('/<string:participant_pkey>', methods=['GET'])
@login_required
def get_all_members_by_participant(user, participant_pkey):
    with DBSession() as session:
        db_user = session.execute(text("SELECT SYSTEM_USER")).scalar()
        current_app.logger.warning(f"Connected to SQL Server as: {db_user}")
        try:
            result = session.execute(text('''
                SELECT 
                    v.*, 
                    d.Depend_Coverage_Status
                FROM vw_FamilyMembers v
                LEFT JOIN XParticipant_Dependents d
                    ON v.RowID = d.RowID
                WHERE v.Depend_Pkey = :pkey
            '''), {'pkey': participant_pkey}).mappings()

            members = []
            for row in result.fetchall():
                members.append({
                    'RowID': row.get('RowID'),
                    'Depend_FirstName': row['Depend_FirstName'],
                    'Depend_MiddleName': row['Depend_MiddleName'],
                    'Depend_LastName': row['Depend_LastName'],
                    'Depend_ID': row['Depend_ID'],
                    'Depend_AutoNum': row.get('Depend_AutoNum'),
                    'Depend_Relation': row['Depend_Relation'],
                    'Depend_BirthDate': row['Depend_BirthDate'].strftime('%m/%d/%Y') if row['Depend_BirthDate'] else None,
                    'Age': calculate_age(row['Depend_BirthDate']) if row['Depend_BirthDate'] else None,
                    'Depend_SSN': str(int(row['Depend_SSN'])).zfill(9) if row['Depend_SSN'] else None,
                    'Depend_Gender': row['Depend_Gender'],
                    'Depend_Coverage_Status': row.get('Depend_Coverage_Status'),  
                    'Depend_MED_Effective': row['Depend_MED_Effective'].strftime('%m/%d/%Y') if row['Depend_MED_Effective'] else None,
                    'Depend_MED_EndDate': row['Depend_MED_EndDate'].strftime('%m/%d/%Y') if row['Depend_MED_EndDate'] else None,
                    'Depend_DEN_Effective': row['Depend_DEN_Effective'].strftime('%m/%d/%Y') if row['Depend_DEN_Effective'] else None,
                    'Depend_DEN_EndDate': row['Depend_DEN_EndDate'].strftime('%m/%d/%Y') if row['Depend_DEN_EndDate'] else None,
                    'Depend_VIS_Effective': row['Depend_VIS_Effective'].strftime('%m/%d/%Y') if row['Depend_VIS_Effective'] else None,
                    'Depend_VIS_EndDate': row['Depend_VIS_EndDate'].strftime('%m/%d/%Y') if row['Depend_VIS_EndDate'] else None,
                    'Depend_Pkey': row['Depend_Pkey']
                })

            members = sorted(members, key=lambda x: (x['Depend_ID'] is None, x['Depend_ID']))
            return jsonify(members), 200

        except SQLAlchemyError as e:
            session.rollback()
            current_app.logerr(e)
            return jsonify({'error': 'Database error.'}), 500

        except Exception as e:
            current_app.logerr(e)
            return jsonify({'error': 'Unexpected error.'}), 500

        
        #edit/add new
@family_members_bp.route('/<string:participant_pkey>', methods=['PUT'])
@login_required
def update_family_members(user, participant_pkey):
    data = request.json
    with DBSession() as session:
        try:
            if not isinstance(data, list):
                return jsonify({'error': 'Expected a list of member objects.'}), 400

            for member in data:
                if member.get('Depend_Relation') == 'Employee':
                    #update employee (unused at the moment)
                    session.execute(text('''
                        UPDATE XParticipant SET
                            Participant_FirstName = :first,
                            Participant_MiddleInit = :middle,
                            Participant_LastName = :last,
                            Participant_Gender = :gender,
                            Participant_BirthDate = :birth,
                            Participant_SSN = :ssn,
                            Participant_Coverage_Status = :coverage,
                            Participant_MED_EffectiveDate = :med_start
                        WHERE Participant_Pkey = :pkey
                    '''), {
                        'first': member.get('Depend_FirstName'),
                        'middle': member.get('Depend_MiddleName'),
                        'last': member.get('Depend_LastName'),
                        'gender': member.get('Depend_Gender'),
                        'birth': member.get('Depend_BirthDate'),
                        'ssn': member.get('Depend_SSN'),
                        'coverage': member.get('Depend_Coverage_Status'),
                        'med_start': member.get('Depend_MED_Effective'),
                        'pkey': participant_pkey
                    })
                else:
                    depend_id = member.get('Depend_ID')
                    row_id = member.get('RowID')  

                    common_values = {
                        'first': member.get('Depend_FirstName'),
                        'middle': member.get('Depend_MiddleName'),
                        'last': member.get('Depend_LastName'),
                        'gender': member.get('Depend_Gender'),
                        'birth': member.get('Depend_BirthDate'),
                        'ssn': member.get('Depend_SSN'),
                        'coverage': member.get('Depend_Coverage_Status'),
                        'relation': member.get('Depend_Relation'),
                        'med_start': member.get('Depend_MED_Effective'),
                        'med_end': member.get('Depend_MED_EndDate'),
                        'den_start': member.get('Depend_DEN_Effective'),
                        'den_end': member.get('Depend_DEN_EndDate'),
                        'vis_start': member.get('Depend_VIS_Effective'),
                        'vis_end': member.get('Depend_VIS_EndDate'),
                    }
                        #determine if update or insert
                    if row_id:
                        existing = session.execute(text('''
                            SELECT 1 FROM XParticipant_Dependents
                            WHERE RowID = :row_id
                        '''), {'row_id': row_id}).fetchone()
                    else:
                        existing = None
                    #update dependent
                    if row_id and existing:
                        session.execute(text('''
                            UPDATE XParticipant_Dependents SET
                                Depend_FirstName = :first,
                                Depend_MiddleName = :middle,
                                Depend_LastName = :last,
                                Depend_ID = :depend_id,
                                Depend_Gender = :gender,
                                Depend_BirthDate = :birth,
                                Depend_SSN = :ssn,
                                Depend_Coverage_Status = :coverage,
                                Depend_Relation = :relation,
                                Depend_MED_Effective = :med_start,
                                Depend_MED_EndDate = :med_end,
                                Depend_DEN_Effective = :den_start,
                                Depend_DEN_EndDate = :den_end,
                                Depend_VIS_Effective = :vis_start,
                                Depend_VIS_EndDate = :vis_end
                            WHERE RowID = :row_id
                        '''), {
                            **common_values,
                            'row_id': row_id,
                            'depend_id': depend_id
                        })
                    elif row_id and not existing:
                        return jsonify({'error': f'No record found for RowID {row_id}'}), 400
                        #insert new dependent
                    else:
                        result = session.execute(text('''
                            INSERT INTO XParticipant_Dependents (
                                Depend_Pkey,
                                Depend_FirstName,
                                Depend_MiddleName,
                                Depend_LastName,
                                Depend_ID,
                                Depend_Gender,
                                Depend_BirthDate,
                                Depend_SSN,
                                Depend_Coverage_Status,
                                Depend_Relation,
                                Depend_MED_Effective,
                                Depend_MED_EndDate,
                                Depend_DEN_Effective,
                                Depend_DEN_EndDate,
                                Depend_VIS_Effective,
                                Depend_VIS_EndDate
                            ) OUTPUT INSERTED.RowID
                            VALUES (
                                :pkey, :first, :middle, :last, :id, :gender, :birth, :ssn, :coverage,
                                :relation, :med_start, :med_end, :den_start, :den_end, :vis_start, :vis_end
                            )
                        '''), {
                            **common_values,
                            'pkey': participant_pkey,
                            'id': depend_id
                        })

                        new_row_id = result.fetchone()[0]

            session.commit()
            return jsonify({'success': True}), 200

        except SQLAlchemyError as e:
            session.rollback()
            current_app.logerr(e)
            return jsonify({'error': 'Database error.'}), 500
        except Exception as e:
            session.rollback()
            current_app.logerr(e)
            return jsonify({'error': 'Unexpected error.'}), 500

#delete
@family_members_bp.route('/<string:participant_pkey>', methods=['DELETE'])
@login_required
def delete_members(user, participant_pkey):
    try:
        data = request.get_json()

        if not data or not isinstance(data, list):
            return jsonify({'error': 'Expected a list of members to delete.'}), 400

        with DBSession() as session:
            for member in data:
                relation = member.get('Depend_Relation')
                try:
                    row_id = int(member.get('RowID'))
                except (TypeError, ValueError):
                    current_app.logger.warning(f"Invalid or missing RowID in payload: {member}")
                    continue

                if relation != 'Employee':
                    current_app.logger.warning(f"Trying to delete RowID: {row_id} (type={type(row_id)})")

                    dependent = session.query(Dependent).filter_by(RowID=row_id).first()

                    if dependent:
                        current_app.logger.warning(f"Deleting Dependent: {dependent}")
                        session.delete(dependent)
                    else:
                        current_app.logger.warning(f"No dependent found with RowID: {row_id}")

            session.commit()
            return jsonify({'message': 'Delete successful.'}), 200

    except SQLAlchemyError as e:
        current_app.logger.error(f"SQLAlchemyError occurred: {str(e)}", exc_info=True)
        return jsonify({'error': 'Database error occurred.'}), 500

    except Exception as e:
        current_app.logerr(e)
        return jsonify({'error': 'Unexpected error occurred.'}), 500

def calculate_age(birthdate):
    today = date.today()
    return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

@family_members_bp.route('/options/genders', methods=['GET'])
@login_required
def get_gender_options(user):
    with DBSession() as session:
        try:
            result = session.execute(text("""
                SELECT DISTINCT Depend_Gender
                FROM XParticipant_Dependents
                WHERE Depend_Gender IS NOT NULL
                ORDER BY Depend_Gender
            """)).fetchall()
            return jsonify([row[0] for row in result])
        except Exception as e:
            current_app.logger.error(e)
            return jsonify({'error': 'Failed to load gender options'}), 500


@family_members_bp.route('/options/relations', methods=['GET'])
@login_required
def get_relation_options(user):
    with DBSession() as session:
        try:
            result = session.execute(text("""
                SELECT DISTINCT Depend_Relation
                FROM XParticipant_Dependents
                WHERE Depend_Relation IS NOT NULL
                ORDER BY Depend_Relation
            """)).fetchall()
            return jsonify([row[0] for row in result])
        except Exception as e:
            current_app.logger.error(e)
            return jsonify({'error': 'Failed to load relation options'}), 500


@family_members_bp.route('/options/coverage_status', methods=['GET'])
def get_coverage_status_options():
    with DBSession() as session:
        try:
            result = session.execute(text("""
                SELECT DISTINCT Depend_Coverage_Status
                FROM XParticipant_Dependents
                WHERE Depend_Coverage_Status IS NOT NULL
                ORDER BY Depend_Coverage_Status
            """)).fetchall()
            return jsonify([row[0] for row in result])
        except Exception as e:
            current_app.logger.error(e)
            return jsonify({'error': 'Failed to load coverage status options'}), 500

        
    
