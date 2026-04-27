import io
import csv
from datetime import datetime
from flask import Blueprint, current_app, request, jsonify, Response
from sqlalchemy import text
from db import Session as DBSession
from utils import login_required
import openpyxl


groups_bp = Blueprint('groups', __name__)


@groups_bp.route('/', methods=['GET'])
@login_required
def index(user):
    with DBSession() as session:
        try:
            result = session.execute(text('SELECT * FROM dbo.vw_grp_Summary_Rpt ORDER BY [Group],[Division] ASC;'))
            columns = list(result.keys())
            rows = result.all()
            data = [row._asdict() for row in rows]

            return jsonify({
                'columns': columns,
                'data': data
            }), '200 OK'
        except Exception as e:
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'
        

@groups_bp.route('/export_csv', methods=['GET'])
@login_required
def export_csv(user):

    sort_by = 'Group'
    sort_order = 'ASC'

    with DBSession() as session:
        try:
            result = session.execute(text(f'''
            SELECT * FROM [dbo].[vw_grp_Summary_Rpt] ORDER BY [{sort_by}] {sort_order}, [Division] ASC
            '''))

            columns = list(result.keys())
            rows = result.all()

            # Write CSV to memory
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(columns)
            for row in rows:
                writer.writerow(list(row))

            output.seek(0)
            csv_data = output.getvalue()
            output.close()

            # Prepare response
            response = Response(
                csv_data,
                mimetype='text/csv',
                headers={
                    "Content-Disposition": f"attachment; filename=groups_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
                }
            )
            return response
        except Exception as e:
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'

@groups_bp.route('/export_excel', methods=['GET'])
@login_required
def export_excel(user):
    sort_by = 'Group'
    sort_order = 'ASC'

    with DBSession() as session:
        try:
            result = session.execute(text(f'''
                SELECT * FROM [dbo].[vw_grp_Summary_Rpt] 
                ORDER BY [{sort_by}] {sort_order}, [Division] ASC
            '''))

            columns = list(result.keys())
            rows = result.fetchall()

            # Create Excel workbook
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Groups Summary"

            # Write header
            ws.append(columns)

            # Write rows
            for row in rows:
                ws.append(list(row))

            # Save to a BytesIO stream
            output = io.BytesIO()
            wb.save(output)
            output.seek(0)

            # Prepare response
            response = Response(
                output.getvalue(),
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers={
                    "Content-Disposition": f"attachment; filename=groups_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                }
            )
            return response
        except Exception as e:
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'
