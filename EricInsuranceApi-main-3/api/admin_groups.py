from models import Group
from flask import Blueprint, current_app, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from db import Session as DBSession
from utils import login_required, admin_required

admin_groups_bp = Blueprint('admin_groups', __name__)

# Create
@admin_groups_bp.route('/', methods=['POST'])
@login_required
@admin_required
def create_group(user):
    data = request.get_json()
            
    # Validate required fields
    if not data.get('Group_ID'):
        return jsonify(), '400 Parameters are not valid.'

    with DBSession() as session:
        try:
            new_group = Group(
                Group_ID=data.get('Group_ID', None),
                Group_Name=data.get('Group_Name', None),
                Group_FullName=data.get('Group_FullName', None),
                Group_Contact_FName=data.get('Group_Contact_FName', None),
                Group_Contact_LName=data.get('Group_Contact_LName', None),
                Group_FEIN=data.get('Group_FEIN', None),
                Group_Address=data.get('Group_Address', None),
                Group_Phone=data.get('Group_Phone', None),
                Group_City=data.get('Group_City', None),
                Group_State=data.get('Group_State', None),
                Group_Zip=data.get('Group_Zip', None),
                Group_Country=data.get('Group_Country', None),
                Group_Comments=data.get('Group_Comments', None),
                Group_EMail=data.get('Group_EMail', None)
            )
            session.add(new_group)
            session.commit()
            return jsonify(new_group.to_dict()), '201 Group created.'
        except Exception as e:
            session.rollback()
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'

# Read all
@admin_groups_bp.route('/', methods=['GET'])
@login_required
@admin_required
def get_groups(user):
    with DBSession() as session:
        try:
            groups = session.query(Group).order_by(Group.Group_ID.asc()).all()
            return jsonify([group.to_dict() for group in groups]), '200 OK'
        except Exception as e:
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'

# Read single
@admin_groups_bp.route('/<string:id>', methods=['GET'])
@login_required
@admin_required
def get_group(user, id):
    with DBSession() as session:
        try:
            group = session.query(Group).filter_by(Group_ID=id).first()
            if not group:
                return jsonify(), '404 Group not found.'
            return jsonify(group.to_dict()), '200 OK'
        except Exception as e:
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'

# Update
@admin_groups_bp.route('/<string:id>', methods=['PUT'])
@login_required
@admin_required
def update_group(user, id):
    with DBSession() as session:
        try:
            group = session.query(Group).filter_by(Group_ID=id).first()
            if not group:
                return jsonify(), '404 Group not found.'
            
            data = request.get_json()
        
            # Update only provided fields
            for key, value in data.items():
                if hasattr(group, key):
                    setattr(group, key, value)
            
            session.commit()
            return jsonify(group.to_dict()), '200 OK'
        except Exception as e:
            session.rollback()
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'

# Delete
@admin_groups_bp.route('/<string:id>', methods=['DELETE'])
@login_required
@admin_required
def delete_group(user, id):
    with DBSession() as session:
        try:
            group = session.query(Group).filter_by(Group_ID=id).first()
            if not group:
                return jsonify(), '404 Group not found.'
            
            session.delete(group)
            session.commit()
            return jsonify(), '200 OK'
        except Exception as e:
            session.rollback()
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'

# Delete groups by group ids
@admin_groups_bp.route('/', methods=['DELETE'])
@login_required
@admin_required
def delete_groups(user):
    group_ids = request.get_json()
    if not group_ids:
        return jsonify(), '400 Parameters are not valid.'

    with DBSession() as session:
        try:
            groups = session.query(Group).filter(Group.Group_ID.in_(group_ids)).all()
            for group in groups:
                session.delete(group)
            session.commit()
            return jsonify(), '200 OK'
        except Exception as e:
            session.rollback()
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'