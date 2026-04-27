from models import User
from flask import Blueprint, current_app, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from db import Session as DBSession
from utils import admin_required, login_required

admin_user_bp = Blueprint('admin_user', __name__)


# Create a new user
@admin_user_bp.route('/', methods=['POST'])
@login_required
@admin_required
def create_user(user):

    data = request.get_json()
    if not data or not data.get('User_ID'):
        return jsonify(), '400 Parameters are not valid.'

    with DBSession() as session:
        try:

            if session.query(User).filter(User.User_ID == data['User_ID']).first():
                return jsonify(), '409 User already exists.'

            user = User(
                User_ID=data.get('User_ID', None),
                User_Password=data.get('User_Password', None),
                User_Level=data.get('User_Level', None),
                User_LoggedOn=data.get('User_LoggedOn', False),
                User_Timestamp=datetime.now() if data.get('User_Timestamp') else None,
                User_Sync=data.get('User_Sync', False),
                User_FirstName=data.get('User_FirstName', None),
                User_LastName=data.get('User_LastName', None),
                User_Dept=data.get('User_Dept', None),
                User_Workfile_Location=data.get('User_Workfile_Location', None)
            )
            session.add(user)
            session.commit()
            return jsonify(user.to_dict()), '201 User created.'
        except Exception as e:
            session.rollback()
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'


# Get all users or a specific user
@admin_user_bp.route('/', methods=['GET'])
@admin_user_bp.route('/<user_id>', methods=['GET'])
@login_required
@admin_required
def get_users(user, user_id=None):
    with DBSession() as session:
        try:
            if user_id:
                user = session.query(User).filter(User.User_ID == user_id).first()
                if not user:
                    return jsonify(), '404 User not found.'
                return jsonify(user.to_dict()), '200 OK'
            
            users = session.query(User).all()
            return jsonify([user.to_dict() for user in users]), '200 OK'

        except Exception as e:
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'
            

# Update a user
@admin_user_bp.route('/<user_id>', methods=['PUT'])
@login_required
@admin_required
def update_user(user, user_id):
    with DBSession() as session:
        try:
            user = session.query(User).filter(User.User_ID == user_id).first()
            if not user:
                return jsonify(), '404 User not found.'

            data = request.get_json()
            if not data:
                return jsonify(), '400 No data provided.'

            # Update only provided fields
            for key, value in data.items():
                if hasattr(user, key):
                    if key == 'User_Timestamp' and value:
                        setattr(user, key, datetime.fromisoformat(value))
                    else:
                        setattr(user, key, value)

            session.commit()
            return jsonify(user.to_dict()), '200 OK'

        except SQLAlchemyError as e:
            session.rollback()
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'


# Delete a user
@admin_user_bp.route('/<user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user, user_id):
    with DBSession() as session:
        try:
            user = session.query(User).filter(User.User_ID == user_id).first()
            if not user:
                return jsonify(), '404 User not found.'

            session.delete(user)
            session.commit()
            return jsonify(), '200 OK'

        except SQLAlchemyError as e:
            session.rollback()
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'


# Update user's password
@admin_user_bp.route('/<user_id>/password', methods=['PUT'])
@login_required
@admin_required
def update_password(user, user_id):
    with DBSession() as session:
        try:
            user = session.query(User).filter(User.User_ID == user_id).first()
            if not user:
                return jsonify(), '404 User not found.'

            data = request.get_json()
            if not data or not data.get('User_Password'):
                return jsonify(), '400 No password provided.'

            user.User_Password = data['User_Password']
            session.commit()
            return jsonify(user.to_dict()), '200 OK'

        except SQLAlchemyError as e:
            session.rollback()
            return jsonify(), '500 An internal error has occurred.'
