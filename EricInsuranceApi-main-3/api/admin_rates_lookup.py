from models import RatesLookup
from flask import Blueprint, current_app, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from db import Session as DBSession
from utils import admin_required, login_required

admin_rates_lookup_bp = Blueprint('admin_rates_lookup', __name__)

# Create
@admin_rates_lookup_bp.route('/', methods=['POST'])
@login_required
@admin_required
def create_rates_lookup(user):
    data = request.get_json()
            
    # Validate required fields
    if not data.get('Age_Bracket'):
        return jsonify(), '400 Parameters are not valid.'

    with DBSession() as session:
        try:
            new_rates_lookup = RatesLookup(
                Age_Bracket=data.get('Age_Bracket', None),
                Rate_VLife=data.get('Rate_VLife', None),
                LastUpdated_Date=datetime.now(),
                Group_Name=data.get('Group_Name', None),
                Group_PolicyNum=data.get('Group_PolicyNum', None)
            )
            session.add(new_rates_lookup)
            session.commit()
            return jsonify(new_rates_lookup.to_dict()), '201 Rates Lookup created.'
        except Exception as e:
            session.rollback()
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'

# Read all
@admin_rates_lookup_bp.route('/', methods=['GET'])
@login_required
@admin_required
def get_rates_lookups(user):
    with DBSession() as session:
        try:
            rates_lookup = session.query(RatesLookup).order_by(RatesLookup.Group_PolicyNum.asc()).all()
            return jsonify([rates_lookup.to_dict() for rates_lookup in rates_lookup]), '200 OK'
        except Exception as e:
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'

# Read single
@admin_rates_lookup_bp.route('/<int:id>', methods=['GET'])
@login_required
@admin_required
def get_rates_lookup(user, id):
    with DBSession() as session:
        try:
            rates_lookup = session.query(RatesLookup).filter_by(Row_ID=id).first()
            if not rates_lookup:
                return jsonify(), '404 Rates Lookup not found.'
            return jsonify(rates_lookup.to_dict()), '200 OK'
        except Exception as e:
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'

# Update
@admin_rates_lookup_bp.route('/<int:id>', methods=['PUT'])
@login_required
@admin_required
def update_rates_lookup(user, id):
    with DBSession() as session:
        try:
            rates_lookup = session.query(RatesLookup).filter_by(Row_ID=id).first()
            if not rates_lookup:
                return jsonify(), '404 Rates Lookup not found.'
            
            data = request.get_json()
        
            # Update only provided fields
            for key, value in data.items():
                if hasattr(rates_lookup, key):
                    setattr(rates_lookup, key, value)
            
            rates_lookup.LastUpdated_Date = datetime.now()
            
            session.commit()
            return jsonify(rates_lookup.to_dict()), '200 OK'
        except Exception as e:
            session.rollback()
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'

# Delete
@admin_rates_lookup_bp.route('/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def delete_rates_lookup(user, id):
    with DBSession() as session:
        try:
            rates_lookup = session.query(RatesLookup).filter_by(Row_ID=id).first()
            if not rates_lookup:
                return jsonify(), '404 Rates Lookup not found.'
            
            session.delete(rates_lookup)
            session.commit()
            return jsonify(), '200 OK'
        except Exception as e:
            session.rollback()
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'

# Delete rates by row ids
@admin_rates_lookup_bp.route('/', methods=['DELETE'])
@login_required
@admin_required
def delete_rates_lookups(user):
    row_ids = request.get_json()
    if not row_ids:
        return jsonify(), '400 Parameters are not valid.'

    with DBSession() as session:
        try:
            rates_lookup = session.query(RatesLookup).filter(RatesLookup.Row_ID.in_(row_ids)).all()
            for rates_lookup in rates_lookup:
                session.delete(rates_lookup)
            session.commit()
            return jsonify(), '200 OK'
        except Exception as e:
            session.rollback()
            current_app.logerr(e)
            return jsonify(), '500 An internal error has occurred.'