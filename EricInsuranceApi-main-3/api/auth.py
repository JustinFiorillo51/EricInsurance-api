from re import search
import uuid
from flask import Blueprint, current_app, request, jsonify
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from db import Session as DBSession
from models import User
import datetime

from utils import get_user_by_session_id, login_required


auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/signin', methods=['POST'])
def signin():
    with DBSession() as session:
        try:
            data = request.get_json()
            user_id = data.get('User_ID')
            password = data.get('User_Password')

            if not user_id or not password:
                return jsonify({
                    'error': 'User ID and password are required'
                }), 400

            user = session.query(User).filter(User.User_ID == user_id).first()
            
            if not user or user.User_Password != password:
                return jsonify({
                    'error': 'Invalid credentials'
                }), 401

            # Update user login status
            user.User_LoggedOn = True
            user.User_Timestamp = datetime.datetime.now()
            user.User_Session_ID = str(uuid.uuid4()).replace('-', '')
            session.commit()

            return jsonify(user.to_dict()), 200

        except Exception as e:
            current_app.logger.error(e)
            return jsonify({
                'error': 'An internal error has occurred'
            }), 500


@auth_bp.route('/signout', methods=['GET'])
@login_required
def signout(user):

    with DBSession() as session:
        try:
            user_model = get_user_by_session_id(user['User_Session_ID'])
            # Update user login status
            user_model.User_LoggedOn = False
            user_model.User_Timestamp = datetime.datetime.now()
            user_model.User_Session_ID = None
            session.commit()

            return jsonify({
                'message': 'Successfully signed out'
            }), 200

        except Exception as e:
            current_app.logger.error(e)
            return jsonify({
                'error': 'An internal error has occurred'
            }), 500




