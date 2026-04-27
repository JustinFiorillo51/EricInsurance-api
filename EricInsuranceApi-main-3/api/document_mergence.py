import logging
from flask import Blueprint, current_app, request, jsonify, send_file
from constants import SORT_DIRECTIONS, ParticipantQueryFields
from db import Session as DBSession
from sqlalchemy import bindparam, text
from models import DocumentTemplate
from utils import MIME_TYPES, build_where_clause, login_required, convert_sql_result_to_dict, validate_sql_query
import fitz  # PyMuPDF
import io
import zipfile
import re


document_mergence_bp = Blueprint('document_mergence', __name__)


@document_mergence_bp.route('/templates', methods=['GET'])
@login_required
def get_all_templates(user):
    """
    Get all document templates
    
    Optional query params:
    - DocType: filter by document type (e.g., 'PDF')
    - SourceType: filter by source type (e.g., 'SQL Query', 'Participant Filter')
    
    Returns:
        JSON response with list of templates containing id, name, and description
    """
    try:
        with DBSession() as session:
            # Read optional filters
            doc_type = request.args.get('DocType', default=None, type=str)
            source_type = request.args.get('SourceType', default=None, type=str)

            query = session.query(DocumentTemplate)

            if doc_type:
                query = query.filter(DocumentTemplate.DocType == doc_type)
            if source_type:
                query = query.filter(DocumentTemplate.SourceType == source_type)

            templates = query.all()
            
            template_list = []
            for template in templates:
                template_list.append({
                    'id': template.RowID,
                    'name': template.TemplateName,
                    'description': template.templateDesc,
                    'filename': template.FileName,
                    'doc_type': template.DocType
                })
            
            return jsonify(template_list)
            
    except Exception as e:
        current_app.logger.error(f"Error getting templates: {str(e)}")
        return jsonify({'error': 'An internal error has occurred'}), 500


@document_mergence_bp.route('/template/<int:row_id>/fields', methods=['GET'])
@login_required
def get_template_fields(user, row_id):
    """
    Get PDF form field names from a document template
    
    Args:
        row_id: DocumentTemplate RowID
        
    Returns:
        JSON response with list of field names
    """
    try:
        with DBSession() as session:
            document_template = session.query(DocumentTemplate).filter_by(RowID=row_id).first()
            
            if not document_template:
                return jsonify({'error': 'Document template not found'}), 404
            
            # Check if document type is PDF
            if not document_template.DocType or document_template.DocType.upper() != 'PDF':
                # If the document is not a PDF, return 200 with empty field_names list
                return jsonify({
                    'template_id': row_id,
                    'template_name': document_template.TemplateName,
                    'field_names': []
                }), 200
            
            # Check if ImageBlob exists
            if not document_template.ImageBlob:
                return jsonify({
                    'template_id': row_id,
                    'template_name': document_template.TemplateName,
                    'field_names': []
                }), 200
            
            # Read PDF and extract field names
            field_names = extract_pdf_field_names(document_template.ImageBlob)
            
            return jsonify({
                'template_id': row_id,
                'template_name': document_template.TemplateName,
                'field_names': field_names
            })
            
    except Exception as e:
        current_app.logger.error(f"Error getting template fields: {str(e)}")
        return jsonify({'error': 'An internal error has occurred'}), 500


def extract_pdf_field_names(pdf_bytes):
    """
    Extract form field names from PDF bytes
    
    Args:
        pdf_bytes: PDF file bytes
        
    Returns:
        List of field names
    """
    try:
        # Convert PDF bytes to BytesIO for PyMuPDF
        pdf_stream = io.BytesIO(pdf_bytes)
        
        # Open the PDF document
        doc = fitz.open(stream=pdf_stream, filetype="pdf")
        
        field_names = []
        
        # Extract field names from all pages
        for page_num in range(len(doc)):
            page = doc[page_num]
            widgets = page.widgets()
            
            for widget in widgets:
                if widget.field_name and widget.field_name not in field_names:
                    field_names.append(widget.field_name)
        
        doc.close()
        
        return field_names
        
    except Exception as e:
        current_app.logger.error(f"Error extracting PDF field names: {str(e)}")
        return []


def sanitize_filename(value: str) -> str:
    """Return a filesystem-safe file name derived from the provided value."""
    if not value:
        return 'document'
    safe_value = re.sub(r'[\\/:*?"<>|]+', '_', str(value))
    safe_value = safe_value.strip()
    return safe_value or 'document'


def fill_pdf_form_fields(pdf_bytes: bytes, data_dict: dict) -> io.BytesIO:
    """
    Fill PDF form fields using PyMuPDF and return a BytesIO stream of the filled PDF.

    Args:
        pdf_bytes: The source PDF bytes
        data_dict: A dict mapping field names to values

    Returns:
        BytesIO of the filled PDF
    """
    pdf_stream = io.BytesIO(pdf_bytes)
    doc = fitz.open(stream=pdf_stream, filetype="pdf")
    try:
        for page_index in range(len(doc)):
            page = doc[page_index]
            widgets = page.widgets() or []
        
            for widget in widgets:
                for field_name, field_value in (data_dict or {}).items():
                    if field_value is None:
                        continue
                    try:
                        if widget.field_name and widget.field_name.lower() == str(field_name).lower():    
                            widget.field_value = str(field_value)
                            widget.update()
                            break
                    except Exception as e:
                        current_app.logger.error(f"Error filling field {field_name} on page {page_index + 1}: {str(e)}")
                        break

        output_stream = io.BytesIO()
        doc.save(output_stream)
        output_stream.seek(0)
        return output_stream
    except Exception:
        # Ensure the document is closed before re-raising
        try:
            doc.close()
        except Exception:
            pass
        raise
    finally:
        try:
            doc.close()
        except Exception:
            pass


@document_mergence_bp.route('/gen_mergence_from_sql/<int:row_id>', methods=['GET'])
@login_required
def merge_from_template_sql(user, row_id):
    
    # get the document template from the database
    with DBSession() as session:
        document_template = session.query(DocumentTemplate).filter_by(RowID=row_id).first()
        
        if not document_template:
            return jsonify({'error': 'Document template not found'}), 404

        # get the sql query from the document template
        sql_query = document_template.SQLquery
        
        if not sql_query:
            return jsonify({'error': 'SQL query not found in template'}), 400

        # Validate SQL query before execution
        is_valid, error_message = validate_sql_query(sql_query)
        if not is_valid:
            current_app.logger.error(f"Invalid SQL query in template {row_id}: {error_message}")
            return jsonify({'error': f'Invalid SQL query in template: {error_message}'}), 400

        # execute the sql query
        results = None
        try:
            results = session.execute(text(sql_query)).all()
        except Exception as e:
            current_app.logger.error(f"Error executing sql query: {str(e)}")
            return jsonify({'error': 'An internal error has occurred'}), 500
    
    merged_file_stream = None

    # merge the results into the pdf file
    if document_template.DocType and document_template.DocType.upper() == 'PDF':
        merged_file_stream = merge_pdf(results, document_template.ImageBlob)
    else:
        return jsonify({'error': 'Document type not supported'}), 400
    
    if not merged_file_stream:
        return jsonify({'error': 'Failed to merge documents'}), 500
    
    file_extension = document_template.FileName.split('.')[-1].lower() if document_template.FileName else None
    mime_type = MIME_TYPES.get(file_extension, 'application/octet-stream')

    # return the results
    return send_file(merged_file_stream, mimetype=mime_type, as_attachment=True, download_name=f'merged_{document_template.FileName}')


def merge_pdf(data, pdffile):
    """
    Merge a single record of data into PDF form fields using PyMuPDF.

    Args:
        data: SQL query result row (mapping-like) or list of rows for a single record
        pdffile: PDF file bytes

    Returns:
        BytesIO object containing the filled PDF, or None on error
    """
    try:
        data_dict = convert_sql_result_to_dict(data)
        return fill_pdf_form_fields(pdffile, data_dict)
    except Exception as e:
        current_app.logger.error(f"Error merging PDF: {str(e)}")
        return None
    
@document_mergence_bp.route('/gen_pdf_by_pkeys', methods=['POST'])
@login_required
def gen_pdf_by_pkeys(user):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided.'}), 400

    pkeys = data.get('pkeys', [])
    if not pkeys:
        return jsonify({'error': 'No pkeys provided.'}), 400

    pkeys = [str(pkey) for pkey in pkeys]
    pkeys_placeholders = [f':pkey{i}' for i in range(len(pkeys))]
    params = {f"pkey{i}": id_value for i, id_value in enumerate(pkeys)}

    template_id = data.get('template_id', '')
    in_one_file = data.get('in_one_file', False)

    with DBSession() as session:
        try:
            # Do sql query to get data
            result = session.execute(text(f'''
                SELECT 
                    {ParticipantQueryFields},
                    T1.Terminated,
                    T1.RowID,
                    T1.Participant_Weekly_VL_Deduction
                FROM dbo.vw_participants T1
                LEFT JOIN Table_Rates ON (
                    T1.Participant_Group_PolicyNum = Table_Rates.Rate_PolicyID
                    AND T1.Participant_Baseline_Date = Table_Rates.Rate_Date
                )
                WHERE T1.Participant_Pkey IN ({','.join(pkeys_placeholders)});
            '''), params)
            rows = result.all()
            columns = list(result.keys())
            data = [dict(zip(columns, row)) for row in rows]

            # Load dependents
            dependent_sql = text('''
                SELECT [Depend_Pkey]
                    ,[Depend_AutoNum]
                    ,[Depend_ID]
                    ,[Depend_D_IDNum]
                    ,[Depend_Name]
                    ,[Depend_LastName]
                    ,[Depend_FirstName]
                    ,[Depend_MiddleName]
                    ,[Depend_SSN]
                    ,[Depend_Gender]
                    ,[Depend_TermDate]
                    ,[Depend_Relation]
                    ,[Depend_BirthDate]
                    ,[Depend_Coverage_Status]
                    ,[Depend_MED_Effective]
                    ,[Depend_MED_EndDate]
                    ,[Depend_DEN_Effective]
                    ,[Depend_DEN_EndDate]
                    ,[Depend_VIS_Effective]
                    ,[Depend_VIS_EndDate]
                    ,[Depend_ID1]
                    ,[Depend_ID2]
                    ,[Depend_Other_Insurance]
                    ,[Depend_PPO]
                    ,[Depend_InEligible_YN]
                    ,[Depend_WorkNotes]
                    ,[Depend_Marker]
                    ,[Depend_Change_Seq]
                    ,[Depend_PPO_Change_Seq]
                    ,[RowID]
                FROM dbo.XParticipant_Dependents
                WHERE Depend_Pkey IN :pkeys
                ORDER BY Depend_Pkey, Depend_AutoNum ASC
            ''').bindparams(bindparam('pkeys', expanding=True))

            dependent_results = session.execute(dependent_sql, {'pkeys': tuple(pkeys)}).mappings().fetchall()
            dependent_data = [dict(row) for row in dependent_results]
            dependent_data_dict = {}
            for dependent in dependent_data:
                dependent_data_dict.setdefault(dependent['Depend_Pkey'], []).append(dependent)

            kwargs = {
                'template_id': template_id,
                'in_one_file': in_one_file,
                'participants': data,
                'family_members': dependent_data_dict
            }

            return merge_pdf_from_participants(**kwargs)

        except Exception as e:
            current_app.logerr(e)
            return jsonify({'error': 'An internal error has occurred.'}), 500


@document_mergence_bp.route('/gen_pdf_by_advanced_filter', methods=['POST'])
@login_required
def gen_pdf_by_advanced_filter(user):
    

    data = request.get_json()
    if not data:
        return jsonify(), '400 No data provided.'
    
    filter_criteria = data.get('filter_criteria')
    sort_by = data.get('sort_by', 'Name')
    sort_order = data.get('sort_order', 'ascend')

    template_id = data.get('template_id', '')
    in_one_file = data.get('in_one_file', False)

    if sort_by not in ('Name', 'Participant_Status', 'Participant_Group_Name'):
        return jsonify(), '400 Parameters are not valid.'
    if sort_order not in ('ascend', 'descend'):
        return jsonify(), '400 Parameters are not valid.'

    sql_params = {}

    where_clause = build_where_clause(filter_criteria, sql_params)

    with DBSession() as session:
        try:
            # Do sql query to get data
            result = session.execute(text(f'''
                SELECT * FROM (
                    SELECT 
                    {ParticipantQueryFields},
                    T1.Terminated,
                    T1.RowID
                    FROM dbo.vw_participants T1
                        LEFT JOIN Table_Rates ON (T1.Participant_Group_PolicyNum = Table_Rates.Rate_PolicyID) AND (T1.Participant_Baseline_Date = Table_Rates.Rate_Date)
                ) AS T1
                WHERE {where_clause}
                ORDER BY T1.[{sort_by}] {SORT_DIRECTIONS[sort_order]}
            '''), sql_params)
            rows = result.all()
            columns = list(result.keys())
            data = [dict(zip(columns, row)) for row in rows]

            pkeys = [row['Participant_Pkey'] for row in data if 'Participant_Pkey' in row]
            if not pkeys:
                return jsonify({'participants': [], 'family_members': {}}), '200 OK'

            dependent_sql = text(f'''
                SELECT [Depend_Pkey]
                    ,[Depend_AutoNum]
                    ,[Depend_ID]
                    ,[Depend_D_IDNum]
                    ,[Depend_Name]
                    ,[Depend_LastName]
                    ,[Depend_FirstName]
                    ,[Depend_MiddleName]
                    ,[Depend_SSN]
                    ,[Depend_Gender]
                    ,[Depend_TermDate]
                    ,[Depend_Relation]
                    ,[Depend_BirthDate]
                    ,[Depend_Coverage_Status]
                    ,[Depend_MED_Effective]
                    ,[Depend_MED_EndDate]
                    ,[Depend_DEN_Effective]
                    ,[Depend_DEN_EndDate]
                    ,[Depend_VIS_Effective]
                    ,[Depend_VIS_EndDate]
                    ,[Depend_ID1]
                    ,[Depend_ID2]
                    ,[Depend_Other_Insurance]
                    ,[Depend_PPO]
                    ,[Depend_InEligible_YN]
                    ,[Depend_WorkNotes]
                    ,[Depend_Marker]
                    ,[Depend_Change_Seq]
                    ,[Depend_PPO_Change_Seq]
                    ,[RowID]
                FROM dbo.XParticipant_Dependents
                WHERE Depend_Pkey 
                IN (
                    SELECT Participant_Pkey FROM (
                        SELECT 
                        {ParticipantQueryFields},
                        T1.Terminated,
                        T1.RowID
                        FROM dbo.vw_participants T1
                        LEFT JOIN Table_Rates ON (T1.Participant_Group_PolicyNum = Table_Rates.Rate_PolicyID) AND (T1.Participant_Baseline_Date = Table_Rates.Rate_Date)
                    ) AS T1
                    WHERE {where_clause}
                )
                                 
                ORDER BY Depend_Pkey,Depend_AutoNum ASC
            ''')

            dependent_results = session.execute(dependent_sql, sql_params).mappings().fetchall()
            dependent_data = [dict(row) for row in dependent_results]
            dependent_data_dict = {}
            for dependent in dependent_data:
                if dependent['Depend_Pkey'] not in dependent_data_dict:
                    dependent_data_dict[dependent['Depend_Pkey']] = []
                dependent_data_dict[dependent['Depend_Pkey']].append(dependent)

            kwargs = {
                'template_id': template_id,
                'in_one_file': in_one_file,
                'participants': data,
                'family_members': dependent_data_dict
            }

            return merge_pdf_from_participants(**kwargs)

        except Exception as e:
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'


def merge_pdf_from_participants(template_id, in_one_file, participants, family_members):
    try:
        if not template_id:
            return jsonify({'error': 'template_id is required'}), 400
        if not isinstance(participants, list) or len(participants) == 0:
            return jsonify({'error': 'No participants provided'}), 400

        # Load template
        with DBSession() as session:
            document_template = session.query(DocumentTemplate).filter_by(RowID=template_id).first()

            if not document_template:
                return jsonify({'error': 'Document template not found'}), 404

            # Validate template eligibility
            if not (document_template.DocType and document_template.DocType.upper() == 'PDF'):
                return jsonify({'error': 'Document type not supported (must be PDF)'}), 400
            if not (document_template.SourceType and str(document_template.SourceType).strip().lower() == 'participant filter'):
                return jsonify({'error': 'Source type not supported (must be Participant Filter)'}), 400
            if not document_template.ImageBlob:
                return jsonify({'error': 'Template PDF content is empty'}), 400

            template_pdf_bytes = bytes(document_template.ImageBlob)

        # Generate filled PDFs
        filled_streams = []
        for index, participant in enumerate(participants, start=1):
            try:
                participant_dict = participant if isinstance(participant, dict) else convert_sql_result_to_dict(participant)
                filled_stream = fill_pdf_form_fields(template_pdf_bytes, participant_dict)
                # Determine per-file name in ZIP mode
                name_hint = participant_dict.get('FullName') or participant_dict.get('Participant_ID') or participant_dict.get('Participant_Pkey') or str(index)
                name_hint = f'{participant_dict.get("Participant_Group_Name")}_{name_hint}'
                per_file_name = f"{sanitize_filename(document_template.TemplateName or 'template')}_{sanitize_filename(str(name_hint))}.pdf"
                filled_streams.append((per_file_name, filled_stream))
            except Exception as e:
                current_app.logger.error(f"Error filling PDF for participant index {index}: {str(e)}")
                continue

        if not filled_streams:
            return jsonify({'error': 'Failed to generate any PDF files'}), 500

        # If one file: merge PDFs
        if in_one_file:
            try:
                merged_doc = fitz.open()
                for _, pdf_stream in filled_streams:
                    try:
                        src_doc = fitz.open(stream=pdf_stream.getvalue(), filetype='pdf')
                        merged_doc.insert_pdf(src_doc)
                        src_doc.close()
                    except Exception as e:
                        current_app.logger.error(f"Error merging a PDF into the final document: {str(e)}")
                        continue

                if merged_doc.page_count == 0:
                    merged_doc.close()
                    return jsonify({'error': 'Merged document is empty'}), 500

                merged_stream = io.BytesIO()
                merged_doc.save(merged_stream)
                merged_doc.close()
                merged_stream.seek(0)

                base_name = sanitize_filename(document_template.TemplateName or 'merged')
                download_name = f"merged_{base_name}.pdf"
                mime_type = MIME_TYPES.get('pdf', 'application/pdf')
                return send_file(merged_stream, mimetype=mime_type, as_attachment=True, download_name=download_name)
            except Exception as e:
                current_app.logger.error(f"Error creating merged PDF: {str(e)}")
                return jsonify({'error': 'Failed to merge PDF files'}), 500

        # Else: ZIP multiple PDFs
        try:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, mode='w', compression=zipfile.ZIP_DEFLATED) as zipf:
                for file_name, pdf_stream in filled_streams:
                    try:
                        zipf.writestr(file_name, pdf_stream.getvalue())
                    except Exception as e:
                        current_app.logger.error(f"Error adding file to ZIP ({file_name}): {str(e)}")
                        continue

            zip_buffer.seek(0)
            base_name = sanitize_filename(document_template.TemplateName or 'documents')
            download_name = f"{base_name}.zip"
            return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name=download_name)
        except Exception as e:
            current_app.logger.error(f"Error creating ZIP archive: {str(e)}")
            return jsonify({'error': 'Failed to create ZIP archive'}), 500

    except Exception as e:
        current_app.logger.error(f"Error in merge_pdf_from_participants: {str(e)}")
        return jsonify({'error': 'An internal error has occurred'}), 500


