import json
from typing import List
import streamlit as st
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from model.question import Question

SCOPES = [
    'https://www.googleapis.com/auth/forms.body',
    'https://www.googleapis.com/auth/drive.file'
]

def get_credentials():
    """Get valid credentials for Google Forms API using service account."""
    try:
        service_account_info = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
        
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=SCOPES
        )
        
        return credentials
        
    except Exception as e:
        st.error(f"Failed to load Google credentials: {str(e)}")
        raise


def create_google_form(title: str, questions: List[Question], owner_email: str) -> str:
    creds = get_credentials()
    service = build('forms', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    form = {
        'info': {
            'title': title,
            'documentTitle': title,
        }
    }
    
    result = service.forms().create(body=form).execute()
    form_id = result['formId']

    update_settings_request = {
        'requests': [{
            'updateSettings': {
                'settings': {
                    'quizSettings': {
                        'isQuiz': True
                    }
                },
                'updateMask': 'quizSettings.isQuiz'
            }
        }]
    }
    service.forms().batchUpdate(formId=form_id, body=update_settings_request).execute()

    question_requests = []
    for q in questions:
        question_request = {
            'createItem': {
                'item': {
                    'title': q.question,
                    'questionItem': {
                        'question': {
                            'required': True,
                            'grading': {
                                'pointValue': 1,
                                'correctAnswers': {
                                    'answers': [{'value': q.answers[q.correct_answer]}]
                                }
                            },
                            'choiceQuestion': {
                                'type': 'RADIO',
                                'options': [{'value': answer} for answer in q.answers],
                                'shuffle': False
                            }
                        }
                    }
                },
                'location': {'index': len(question_requests)}
            }
        }
        question_requests.append(question_request)

    update_request = {'requests': question_requests}
    service.forms().batchUpdate(formId=form_id, body=update_request).execute()

    try:
        drive_service.permissions().create(
            fileId=form_id,
            body={
                'type': 'user',
                'role': 'writer',
                'emailAddress': owner_email
            }
        ).execute()
    except Exception as e:
        st.warning(f"Form created but sharing failed: {str(e)}")
    
    return f"https://docs.google.com/forms/d/{form_id}/edit"