from models import Rate
from flask import Blueprint, current_app, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from db import Session as DBSession
from utils import admin_required, login_required

admin_rates_bp = Blueprint('admin_rates', __name__)

# Create
@admin_rates_bp.route('/', methods=['POST'])
@login_required
@admin_required
def create_rate(user):

    data = request.get_json()
            
    # Validate required fields
    if not data.get('Rate_Date') or not data.get('Rate_PolicyID'):
        return jsonify(), '400 Parameters are not valid.'

    with DBSession() as session:
        try:
            
            new_rate = Rate(
                Rate_Date=datetime.fromisoformat(data.get('Rate_Date')) if data.get('Rate_Date', None) else None,
                Rate_PolicyID=data.get('Rate_PolicyID', None),
                Rate_Lookup=data.get('Rate_Lookup', None),
                Rate_Comments=data.get('Rate_Comments', None),
                Rate_Basic_Prem=data.get('Rate_Basic_Prem', None),
                Rate_Basic_Prem_ADD=data.get('Rate_Basic_Prem_ADD', None),
                Rate_Basic_Prem_Dep=data.get('Rate_Basic_Prem_Dep', None),
                Rate_VLife_Wkly_Deduct=data.get('Rate_VLife_Wkly_Deduct', None),
                Rate_VLife_Prem_Child=data.get('Rate_VLife_Prem_Child', None),
                Rate_Basic_Volume_Emp=data.get('Rate_Basic_Volume_Emp', None),
                Rate_Basic_Volume_Spouse=data.get('Rate_Basic_Volume_Spouse', None),
                Rate_Basic_Volume_Child=data.get('Rate_Basic_Volume_Child', None)
            )
            session.add(new_rate)
            session.commit()
            return jsonify(new_rate.to_dict()), '201 Rate created.'
        except Exception as e:
            session.rollback()
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'

# Read all
@admin_rates_bp.route('/', methods=['GET'])
@login_required
@admin_required
def get_rates(user):
    with DBSession() as session:
        try:
            rates = session.query(Rate).order_by(Rate.Rate_Date.desc()).all()
            return jsonify([rate.to_dict() for rate in rates]), '200 OK'
        except Exception as e:
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'

# Read single
@admin_rates_bp.route('/<int:id>', methods=['GET'])
@login_required
@admin_required
def get_rate(user, id):
    with DBSession() as session:
        try:
            rate = session.query(Rate).filter_by(Row_ID=id).first()
            if not rate:
                return jsonify(), '404 Rate not found.'
            return jsonify(rate.to_dict()), '200 OK'
        except Exception as e:
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'

# Update
@admin_rates_bp.route('/<int:id>', methods=['PUT'])
@login_required
@admin_required
def update_rate(user, id):
    with DBSession() as session:
        try:
            rate = session.query(Rate).filter_by(Row_ID=id).first()
            if not rate:
                return jsonify(), '404 Rate not found.'
            
            data = request.get_json()
        
            # Update only provided fields
            for key, value in data.items():
                if hasattr(rate, key):
                    if key == 'Rate_Date' and value:
                        setattr(rate, key, datetime.fromisoformat(value))
                    else:
                        setattr(rate, key, value)
            
            session.commit()
            return jsonify(rate.to_dict()), '200 OK'
        except Exception as e:
            session.rollback()
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'

# Delete
@admin_rates_bp.route('/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def delete_rate(user, id):
    with DBSession() as session:
        try:
            rate = session.query(Rate).filter_by(Row_ID=id).first()
            if not rate:
                return jsonify(), '404 Rate not found.'
            
            session.delete(rate)
            session.commit()
            return jsonify(), '200 OK'
        except Exception as e:
            session.rollback()
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'

# Delete rates by row ids
@admin_rates_bp.route('/', methods=['DELETE'])
@login_required
@admin_required
def delete_rates(user):

    row_ids = request.get_json()
    if not row_ids:
        return jsonify(), '400 Parameters are not valid.'

    with DBSession() as session:
        try:
            rates = session.query(Rate).filter(Rate.Row_ID.in_(row_ids)).all()
            for rate in rates:
                session.delete(rate)
            session.commit()
            return jsonify(), '200 OK'
        except Exception as e:
            session.rollback()
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'

