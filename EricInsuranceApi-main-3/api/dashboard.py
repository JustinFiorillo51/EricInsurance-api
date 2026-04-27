from flask import Blueprint, current_app, request, jsonify
from sqlalchemy import text
from db import Session as DBSession
from utils import login_required

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/', methods=['GET'])
@login_required
def participants(user):
    with DBSession() as session:
        try:
            statistics = {
                'total': None,
                'terminated': None,
                'new': None
            }
            gender = []
        
            result = session.execute(text('SELECT count(1) as [count] FROM dbo.XParticipant;'))
            statistics['total'] = result.scalar()

            result2 = session.execute(text('''
                SELECT 
                    SUM([Termed Participant]) AS TotalTerminatedParticipants
                FROM 
                    [vw_db_NewTermedParticipants_All]
                WHERE 
                    [Week Starting] >= '2023-06-01' AND [Week Starting] <= '2024-12-31';
                                            '''))
            statistics['terminated'] = result2.scalar()

            result3 = session.execute(text('''
                SELECT 
                    SUM([NEW participant]) AS TotalNewParticipants
                FROM 
                    [vw_db_NewTermedParticipants_All]
                WHERE 
                    [Week Starting] >= '2023-06-01' AND [Week Starting] <= '2024-12-31';
                                            '''))
            statistics['new'] = result3.scalar()


            result_gender = session.execute(text('''
                SELECT Participant_Gender AS Gender, 
                    COUNT(Participant_Gender) AS [Count] 
                FROM dbo.XParticipant 
                WHERE Participant_Gender IN('M', 'F') 
                Group BY Participant_Gender;
            '''))
            result_gender = result_gender.all()
            gender = [{ 'gender': g.Gender, 'count': g.Count } for g in result_gender]


            return jsonify({'statistics': statistics, 'gender': gender}), '200 OK'
        except Exception as e:
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'
        

        