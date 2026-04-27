from models import DocumentTemplate
from flask import Blueprint, current_app, request, jsonify, send_file
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from db import Session as DBSession
from utils import admin_required, login_required, MIME_TYPES, validate_sql_query
import uuid
import base64
import io

admin_document_template_bp = Blueprint('admin_document_template', __name__)


# Create a new document template
@admin_document_template_bp.route('/', methods=['POST'])
@login_required
@admin_required
def create_document_template(user):
    # Check if request is multipart/form-data (file upload) or application/json
    if request.content_type and 'multipart/form-data' in request.content_type:
        # Handle file upload
        try:
            # Get form data
            template_name = request.form.get('TemplateName')
            file_name = request.form.get('FileName')
            template_desc = request.form.get('templateDesc')
            sql_query = request.form.get('SQLquery')
            doc_type = request.form.get('DocType')
            source_type = request.form.get('SourceType')
            template_content = request.form.get('TemplateContent')
            record_status = int(request.form.get('RecordStatus', 1))
            
            # Get uploaded file
            uploaded_file = request.files.get('file')
            
            if not template_name:
                return jsonify({'error': 'TemplateName is required'}), 400
                
            if not file_name:
                return jsonify({'error': 'FileName is required'}), 400
                
            if not doc_type:
                return jsonify({'error': 'DocType is required'}), 400
                
            # File upload is required for all document types
            if not uploaded_file:
                return jsonify({'error': 'File upload is required'}), 400
            
            # Validate SQL query if provided
            if sql_query:
                is_valid, error_message = validate_sql_query(sql_query)
                if not is_valid:
                    return jsonify({'error': f'Invalid SQL query: {error_message}'}), 400
            
            with DBSession() as session:
                # Generate a new GUID for the document
                doc_guid = str(uuid.uuid4())
                current_time = datetime.now()
                current_user = user.get('User_ID', 'System')
                
                # Process file if uploaded
                image_blob = None
                document_size = None
                
                if uploaded_file:
                    # Read file content
                    file_content = uploaded_file.read()
                    image_blob = file_content
                    
                    # Calculate file size in MB
                    file_size_bytes = len(file_content)
                    document_size = f"{file_size_bytes / (1024 * 1024):.2f}"
                    
                    # Update filename if not provided
                    if not file_name:
                        file_name = uploaded_file.filename
                
                document_template = DocumentTemplate(
                    DocGuid=doc_guid,
                    TemplateName=template_name,
                    FileName=file_name,
                    templateDesc=template_desc,
                    SQLquery=sql_query,
                    DocType=doc_type,
                    SourceType=source_type,
                    ImageBlob=image_blob,
                    DocumentSizeInMB=document_size,
                    UploadedBy=current_user,
                    UploadedDate=current_time,
                    UpdatedBy=current_user,
                    UpdatedDate=current_time,
                    RecordStatus=record_status,
                    Deleted=0,
                    TemplateContent=template_content
                )
                session.add(document_template)
                session.commit()
                return jsonify(document_template.to_dict()), 201
                
        except Exception as e:
            current_app.logger.error(f"Error creating document template: {str(e)}")
            return jsonify({'error': 'An internal error has occurred'}), 500
    else:
        # Handle JSON data (existing functionality)
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Parameters are not valid'}), 400

        with DBSession() as session:
            try:
                # Validate SQL query if provided
                sql_query = data.get('SQLquery', None)
                if sql_query:
                    is_valid, error_message = validate_sql_query(sql_query)
                    if not is_valid:
                        return jsonify({'error': f'Invalid SQL query: {error_message}'}), 400
                
                # Generate a new GUID for the document
                doc_guid = str(uuid.uuid4())
                current_time = datetime.now()
                current_user = user.get('User_ID', 'System')
                
                document_template = DocumentTemplate(
                    DocGuid=doc_guid,
                    TemplateName=data.get('TemplateName', None),
                    FileName=data.get('FileName', None),
                    templateDesc=data.get('templateDesc', None),
                    SQLquery=sql_query,
                    DocType=data.get('DocType', None),
                    SourceType=data.get('SourceType', None),
                    ImageBlob=data.get('ImageBlob', None),
                    DocumentSizeInMB=data.get('DocumentSizeInMB', None),
                    UpdatedBy=current_user,
                    UpdatedDate=current_time,
                    RecordStatus=data.get('RecordStatus', 1),
                    Deleted=data.get('Deleted', 0),
                    TemplateContent=data.get('TemplateContent', None)
                )
                session.add(document_template)
                session.commit()
                return jsonify(document_template.to_dict()), 201
            except Exception as e:
                session.rollback()
                current_app.logger.error(f"Error creating document template: {str(e)}")
                return jsonify({'error': 'An internal error has occurred'}), 500


# Get all document templates or a specific document template
@admin_document_template_bp.route('/', methods=['GET'])
@admin_document_template_bp.route('/<int:row_id>', methods=['GET'])
@login_required
@admin_required
def get_document_templates(user, row_id=None):
    with DBSession() as session:
        try:
            if row_id:
                document_template = session.query(DocumentTemplate).filter(
                    DocumentTemplate.RowID == row_id,
                    DocumentTemplate.Deleted == 0
                ).first()
                if not document_template:
                    return jsonify({'error': 'Document template not found'}), 404
                # Include blob for single template query
                return jsonify(document_template.to_dict(include_blob=True)), 200
            
            # Get all non-deleted document templates
            document_templates = session.query(DocumentTemplate).filter(
                DocumentTemplate.Deleted == 0
            ).all()
            # Don't include blob for list query
            return jsonify([template.to_dict(include_blob=False) for template in document_templates]), 200

        except Exception as e:
            current_app.logger.error(f"Error getting document templates: {str(e)}")
            return jsonify({'error': 'An internal error has occurred'}), 500
            

# Update a document template
@admin_document_template_bp.route('/<int:row_id>', methods=['PUT'])
@login_required
@admin_required
def update_document_template(user, row_id):
    with DBSession() as session:
        try:
            document_template = session.query(DocumentTemplate).filter(
                DocumentTemplate.RowID == row_id,
                DocumentTemplate.Deleted == 0
            ).first()
            if not document_template:
                return jsonify({'error': 'Document template not found'}), 404

            # Check if request is multipart/form-data (file upload) or application/json
            if request.content_type and 'multipart/form-data' in request.content_type:
                # Handle file upload for update
                try:
                    # Get form data
                    template_name = request.form.get('TemplateName')
                    file_name = request.form.get('FileName')
                    template_desc = request.form.get('templateDesc')
                    sql_query = request.form.get('SQLquery')
                    doc_type = request.form.get('DocType')
                    source_type = request.form.get('SourceType')
                    template_content = request.form.get('TemplateContent')
                    record_status = int(request.form.get('RecordStatus', 1)) if request.form.get('RecordStatus') else None
                    
                    # Get uploaded file
                    uploaded_file = request.files.get('file')
                    
                    # Validate SQL query if provided
                    if sql_query is not None:
                        is_valid, error_message = validate_sql_query(sql_query)
                        if not is_valid:
                            return jsonify({'error': f'Invalid SQL query: {error_message}'}), 400
                    
                    # Update fields if provided
                    if template_name is not None:
                        document_template.TemplateName = template_name
                    if file_name is not None:
                        document_template.FileName = file_name
                    if template_desc is not None:
                        document_template.templateDesc = template_desc
                    if sql_query is not None:
                        document_template.SQLquery = sql_query
                    if doc_type is not None:
                        document_template.DocType = doc_type
                    if source_type is not None:
                        document_template.SourceType = source_type
                    if template_content is not None:
                        document_template.TemplateContent = template_content
                    if record_status is not None:
                        document_template.RecordStatus = record_status
                    
                    # Process file if uploaded
                    if uploaded_file:
                        # Read file content
                        file_content = uploaded_file.read()
                        document_template.ImageBlob = file_content
                        
                        # Calculate file size in MB
                        file_size_bytes = len(file_content)
                        document_template.DocumentSizeInMB = f"{file_size_bytes / (1024 * 1024):.2f}"
                        
                        # Update filename with uploaded file name if no explicit filename provided
                        # or if the provided filename is the same as the current one (indicating no change)
                        if not file_name or file_name == document_template.FileName:
                            document_template.FileName = uploaded_file.filename
                    
                    # Update the UpdatedDate and UpdatedBy fields
                    document_template.UpdatedDate = datetime.now()
                    document_template.UpdatedBy = user.get('User_ID', 'System')
                    
                    session.commit()
                    return jsonify(document_template.to_dict()), 200
                    
                except Exception as e:
                    session.rollback()
                    current_app.logger.error(f"Error updating document template: {str(e)}")
                    return jsonify({'error': 'An internal error has occurred'}), 500
            else:
                # Handle JSON data (existing functionality)
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No data provided'}), 400

                # Validate SQL query if provided
                if 'SQLquery' in data:
                    sql_query = data['SQLquery']
                    if sql_query is not None:
                        is_valid, error_message = validate_sql_query(sql_query)
                        if not is_valid:
                            return jsonify({'error': f'Invalid SQL query: {error_message}'}), 400
                
                # Update only provided fields
                for key, value in data.items():
                    if hasattr(document_template, key):
                        if key in ['UploadedDate', 'UpdatedDate', 'DeletedDate'] and value:
                            setattr(document_template, key, datetime.fromisoformat(value))
                        else:
                            setattr(document_template, key, value)

                # Update the UpdatedDate and UpdatedBy fields
                document_template.UpdatedDate = datetime.now()
                document_template.UpdatedBy = user.get('User_ID', 'System')

                session.commit()
                return jsonify(document_template.to_dict()), 200

        except SQLAlchemyError as e:
            session.rollback()
            current_app.logger.error(f"Error updating document template: {str(e)}")
            return jsonify({'error': 'An internal error has occurred'}), 500


# Soft delete a document template (set Deleted = 1)
@admin_document_template_bp.route('/<int:row_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_document_template(user, row_id):
    with DBSession() as session:
        try:
            document_template = session.query(DocumentTemplate).filter(
                DocumentTemplate.RowID == row_id,
                DocumentTemplate.Deleted == 0
            ).first()
            if not document_template:
                return jsonify({'error': 'Document template not found'}), 404

            # Soft delete - set Deleted = 1 and DeletedDate
            document_template.Deleted = 1
            document_template.DeletedDate = datetime.now()
            # Update the UpdatedDate and UpdatedBy fields
            document_template.UpdatedDate = datetime.now()
            document_template.UpdatedBy = user.get('User_ID', 'System')
            
            session.commit()
            return jsonify({'message': 'Document template deleted successfully'}), 200

        except SQLAlchemyError as e:
            session.rollback()
            current_app.logger.error(f"Error deleting document template: {str(e)}")
            return jsonify({'error': 'An internal error has occurred'}), 500


# Download document template file
@admin_document_template_bp.route('/<int:row_id>/download', methods=['GET'])
@login_required
@admin_required
def download_document_template(user, row_id):
    with DBSession() as session:
        try:
            document_template = session.query(DocumentTemplate).filter(
                DocumentTemplate.RowID == row_id,
                DocumentTemplate.Deleted == 0
            ).first()
            
            if not document_template:
                return jsonify({'error': 'Document template not found'}), 404
            
            if not document_template.ImageBlob:
                return jsonify({'error': 'No file content found for this template'}), 404
            
            # Create a file-like object from the blob data
            file_stream = io.BytesIO(document_template.ImageBlob)
            file_stream.seek(0)
            
            # Determine the MIME type based on file extension
            file_extension = document_template.FileName.split('.')[-1].lower() if document_template.FileName else None
            mime_type = MIME_TYPES.get(file_extension, 'application/octet-stream')
            
            return send_file(
                file_stream,
                mimetype=mime_type,
                as_attachment=True,
                download_name=document_template.FileName
            )
            
        except Exception as e:
            current_app.logger.error(f"Error downloading document template: {str(e)}")
            return jsonify({'error': 'An internal error has occurred'}), 500


# Preview document template file (for PDF preview in browser)
@admin_document_template_bp.route('/<int:row_id>/preview', methods=['GET'])
@login_required
@admin_required
def preview_document_template(user, row_id):
    with DBSession() as session:
        try:
            document_template = session.query(DocumentTemplate).filter(
                DocumentTemplate.RowID == row_id,
                DocumentTemplate.Deleted == 0
            ).first()
            
            if not document_template:
                return jsonify({'error': 'Document template not found'}), 404
            
            if not document_template.ImageBlob:
                return jsonify({'error': 'No file content found for this template'}), 404
            
            # Create a file-like object from the blob data
            file_stream = io.BytesIO(document_template.ImageBlob)
            file_stream.seek(0)
            
            # Determine the MIME type based on file extension
            file_extension = document_template.FileName.split('.')[-1].lower() if document_template.FileName else None
            mime_type = MIME_TYPES.get(file_extension, 'application/octet-stream')
            
            # For preview, we want to display in browser, not download
            return send_file(
                file_stream,
                mimetype=mime_type,
                as_attachment=False,  # This allows browser to display the file
                download_name=document_template.FileName
            )
            
        except Exception as e:
            current_app.logger.error(f"Error previewing document template: {str(e)}")
            return jsonify({'error': 'An internal error has occurred'}), 500

