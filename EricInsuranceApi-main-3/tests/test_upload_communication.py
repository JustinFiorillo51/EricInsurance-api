#!/usr/bin/env python3
"""
Simple test script to call the multipart upload endpoint and attach a PDF.

It will:
- Insert a temporary user with a known session id
- POST to /api/participants/communications/upload with multipart/form-data
- Print the response and created RowID
- Clean up inserted communication record and test user
"""

import os
import sys
import io
import json
import datetime

from sqlalchemy import text

# Ensure project root is on path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app
from db import Session as DBSession
from models import User


def ensure_test_user(session, user_id: str, session_id: str):
    user = session.query(User).filter(User.User_ID == user_id).first()
    if user is None:
        user = User(
            User_ID=user_id,
            User_Password=None,
            User_Level=1.0,
            User_LoggedOn=False,
            User_Timestamp=datetime.datetime.now(datetime.timezone.utc),
            User_Sync=False,
            User_FirstName='Test',
            User_LastName='User',
            User_Dept='QA',
            User_Workfile_Location=None,
            User_Session_ID=session_id,
        )
        session.add(user)
        session.commit()
        return True
    else:
        # Update session id for existing test user
        user.User_Session_ID = session_id
        session.commit()
        return False


def cleanup_test_user(session, user_id: str):
    try:
        session.execute(text("DELETE FROM Table_Security WHERE User_ID = :uid"), {"uid": user_id})
        session.commit()
    except Exception:
        session.rollback()


def cleanup_created_comm(session, row_id: int):
    try:
        session.execute(text("DELETE FROM dbo.XParticipant_Communications WHERE RowID = :rid"), {"rid": row_id})
        session.commit()
    except Exception:
        session.rollback()


def main():
    TEST_USER_ID = 'TUPLOAD1'  # <= 10 chars
    TEST_SESSION_ID = 'SESSIONUPLOAD1'

    pdf_path = os.path.join(PROJECT_ROOT, 'docs', 'Mailing-Letter01_Template.pdf')
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return 1

    # Prepare DB user for login_required
    created_user = False
    with DBSession() as session:
        created_user = ensure_test_user(session, TEST_USER_ID, TEST_SESSION_ID)

    app = create_app()
    app.config['TESTING'] = True

    created_row_id = None
    try:
        with app.test_client() as client:
            data = {
                'Participant_Pkey': 'P4171908682568443523',
                'ComType': 'SPD',
                'Subject': 'Test SPD Upload',
                'ComContent': 'Automated test upload of SPD PDF.',
                'Receiver': 'qa@example.com',
                'EventDate': datetime.date.today().isoformat(),
                'RecordStatus': '1',
            }

            with open(pdf_path, 'rb') as f:
                data['file'] = (io.BytesIO(f.read()), 'Mailing-Letter01_Template.pdf')

                resp = client.post(
                    '/api/participants/communications/upload',
                    data=data,
                    headers={'User-Session-ID': TEST_SESSION_ID},
                    content_type='multipart/form-data'
                )

            try:
                payload = resp.get_json()
            except Exception:
                payload = None

            print(f"HTTP {resp.status_code}")
            print(f"Response JSON: {json.dumps(payload, ensure_ascii=False)}")

            if resp.status_code in (200, 201) and payload and 'RowID' in payload:
                created_row_id = payload['RowID']
                print(f"✅ Created communication RowID: {created_row_id}")
            else:
                print("❌ Failed to create communication record")
                return 1

        return 0
    finally:
        with DBSession() as session:
            # if created_row_id is not None:
            #     cleanup_created_comm(session, created_row_id)
            cleanup_test_user(session, TEST_USER_ID)


if __name__ == '__main__':
    sys.exit(main())


