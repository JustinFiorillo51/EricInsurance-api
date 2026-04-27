from flask import Blueprint, current_app, request, jsonify
from db import Session as DBSession
from sqlalchemy import text
from models import Group
from utils import login_required

commons_bp = Blueprint('commons', __name__)


# Get all policy
@commons_bp.route('/policy/', methods=['GET'])
@login_required
def get_policy(user):
    with DBSession() as session:
        try:
            result = session.execute(text('''
                SELECT DISTINCT tDivisions.Division_Group_Name AS [Group], tDivisions.Division_Group_PolicyNum AS [Policy_ID]
                FROM tDivisions
                ORDER BY tDivisions.Division_Group_Name, tDivisions.Division_Group_PolicyNum;
            '''))

            policy = [{ 'Group': p.Group, 'Policy_ID': p.Policy_ID } for p in result.all()]
            
            return jsonify(policy), '200 OK'

        except Exception as e:
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'
            

@commons_bp.route('/states/', methods=['GET'])
@login_required
def get_states(user):
    with DBSession() as session:
        try:
            result = session.execute(text('SELECT * FROM dbo.tblStates ORDER BY StateAbbrev ASC;'))

            states = [{ 'RowID': s.RowID, 'StateName': s.StateName, 'StateAbbrev': s.StateAbbrev, 'Capital': s.Capital, 'Region': s.Region } for s in result.all()]
            
            return jsonify(states), '200 OK'

        except Exception as e:
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'


@commons_bp.route('/groups/', methods=['GET'])
@login_required
def get_groups(user):
    with DBSession() as session:
        try:
            groups = session.query(Group).order_by(Group.Group_ID.asc()).all()
            return jsonify([group.to_dict() for group in groups]), '200 OK'
        except Exception as e:
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'


@commons_bp.route('/occupations/', methods=['GET'])
@login_required
def get_occupations(user):
    with DBSession() as session:
        try:
            result = session.execute(text('''
            SELECT Participant_Occupation, SUM(1) AS Count
            FROM XParticipant
            GROUP BY Participant_Occupation
            HAVING Participant_Occupation > ''
            ORDER BY Participant_Occupation;
            '''))

            occupations = [s._asdict() for s in result.all()]
            
            return jsonify(occupations), '200 OK'

        except Exception as e:
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'


@commons_bp.route('/departments/', methods=['GET'])
@login_required
def get_departments(user):
    with DBSession() as session:
        try:
            result = session.execute(text('''
            SELECT TRIM(Participant_Department) AS Dept
            FROM XParticipant
            GROUP BY TRIM(Participant_Department)
            HAVING TRIM(Participant_Department) > '';
            '''))

            departments = [s._asdict() for s in result.all()]
            
            return jsonify(departments), '200 OK'

        except Exception as e:
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'


@commons_bp.route('/divisions/', methods=['GET'])
@login_required
def get_divisions(user):
    with DBSession() as session:
        try:
            result = session.execute(text('''
            SELECT tDivisions.Division_Name, tDivisions.Division_Group_ID, tDivisions.Division_Group_Name, tDivisions.Division_Comments AS Description, tDivisions.Division_Group_FullName, tDivisions.Division_Group_PolicyNum, tDivisions.Division_FEIN
            FROM tDivisions
            ORDER BY tDivisions.Division_Name;
            '''))

            divisions = [s._asdict() for s in result.all()]
            
            return jsonify(divisions), '200 OK'

        except Exception as e:
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'


@commons_bp.route('/membership_descs/', methods=['GET'])
@login_required
def get_membership_descs(user):
    with DBSession() as session:
        try:
            result = session.execute(text('SELECT * FROM [Table-Memberships];'))

            descs = [s._asdict() for s in result.all()]
            
            return jsonify(descs), '200 OK'

        except Exception as e:
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'


@commons_bp.route('/premium_rate/', methods=['GET'])
@login_required
def get_premium_rate(user):

    group_policy_number = request.args.get('group_policy_number')
    age_bracket = request.args.get('age_bracket')
    baseline_date = request.args.get('baseline_date')

    if not group_policy_number or group_policy_number == '':
        return jsonify(), '400 Bad Request'

    if not age_bracket or age_bracket == '':
        return jsonify(), '400 Bad Request'

    if not baseline_date or baseline_date == '':
        return jsonify(), '400 Bad Request'

    with DBSession() as session:
        try:
            # {{appsmith.store.currentParticipant.Participant_Age_Bracket}}
            # {{appsmith.store.currentParticipant.Participant_Group_PolicyNum}}
            query_rate_lookup = 'SELECT TOP 1 * FROM dbo.[Table_VLifeAgeRates] WHERE [Age_Bracket]=:Age_Bracket AND [Group_PolicyNum]=:Group_PolicyNum;'

            rate_lookup = session.execute(text(query_rate_lookup), {
                'Age_Bracket': age_bracket,
                'Group_PolicyNum': group_policy_number
            }).first()

            # {{moment.utc(JSLifeInsurance.editingParticipant.Participant_Baseline_Date).format('L')}}
            # {{JSLifeInsurance.editingParticipant.Participant_Group_PolicyNum}}
            query_rate = 'SELECT TOP 1 * FROM dbo.[Table_Rates] WHERE [Rate_Date]=:Rate_Date AND [Rate_PolicyID]=:Rate_PolicyID;'

            rate = session.execute(text(query_rate), {
                'Rate_Date': baseline_date,
                'Rate_PolicyID': group_policy_number
            }).first()

            result = {
                'groupPolicyNum': group_policy_number,
                'vLifeRate': rate_lookup.Rate_VLife if rate_lookup else 0,
                'basic': rate.Rate_Basic_Prem if rate else 0,
                'basicADD': rate.Rate_Basic_Prem_ADD if rate else 0,
                'basicDepend': rate.Rate_Basic_Prem_Dep if rate else 0,
                'child': rate.Rate_VLife_Prem_Child if rate else 0,
                'wklyDedution': rate.Rate_VLife_Wkly_Deduct if rate else 0,
                'rate': rate._asdict() if rate else None,
                'rate_lookup': rate_lookup._asdict() if rate_lookup else None
            }
            
            return jsonify(result), '200 OK'

        except Exception as e:
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'
        
@commons_bp.route('/rate/', methods=['GET'])
@login_required
def get_rate(user):

    group_policy_number = request.args.get('group_policy_number')

    if not group_policy_number or group_policy_number == '':
        return jsonify(), '400 Bad Request'

    with DBSession() as session:
        try:
            query_rate = 'SELECT TOP 1 * FROM dbo.[Table_Rates] WHERE [Rate_PolicyID]=:Rate_PolicyID;'

            rate = session.execute(text(query_rate), {
                'Rate_PolicyID': group_policy_number
            }).first()
            
            return jsonify(rate._asdict()), '200 OK'

        except Exception as e:
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'


@commons_bp.route('/rate_lookup_by_age_bracket/', methods=['GET'])
@login_required
def get_rate_lookup_by_age_bracket(user):

    group_name = request.args.get('group_name', None)
    age_bracket = request.args.get('age_bracket', None)

    with DBSession() as session:
        try:
            query_rate = 'SELECT TOP 1 * FROM dbo.[Table_VLifeAgeRates] WHERE [Age_Bracket]=:Age_Bracket AND [Group_Name]=:Group_Name;'

            rate = session.execute(text(query_rate), {
                'Age_Bracket': age_bracket,
                'Group_Name': group_name
            }).first()
            
            return jsonify(rate._asdict()), '200 OK'

        except Exception as e:
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'
        

@commons_bp.route('/rate_lookup_default/', methods=['GET'])
@login_required
def get_rate_lookup_default(user):
    with DBSession() as session:
        try:
            query_rate = 'SELECT TOP 1 * FROM dbo.[Table_VLifeAgeRates] WHERE [Age_Bracket]=null AND [Group_Name]=null;'

            rate = session.execute(text(query_rate)).first()
            
            return jsonify(rate._asdict() if rate else None), '200 OK'

        except Exception as e:
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'