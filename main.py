import typing_extensions as typing

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/forms.body']

class Question(typing.TypedDict):
    title: str
    options: list[str]
    answer_key: int

class Quiz(typing.TypedDict):
    quiz_title: str
    questions: list[Question]


def authenticate():
    """Handles OAuth 2.0 authentication and returns an authenticated Google Forms API service."""
    
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    
    creds = flow.run_local_server(port=0)
    service = build('forms', 'v1', credentials=creds)
    
    return service

def create_form(service, title):
    """Creates a Google Form with just a title"""
    form = {
        "info": {
            "title": title
        }
    }
    
    form_response = service.forms().create(body=form).execute()
    form_id = form_response['formId']
    form_url = f"https://docs.google.com/forms/d/{form_id}/edit"
    
    print(f"Form created! You can view it here: {form_url}")
    
    return form_id

def create_question(title, options, question_type, idx, correct_answer):
    return {
        "createItem": {
            "item": {
                "title": title,
                "questionItem": {
                    "question": {
                        "required": True,
                        "choice_question": {
                            "type": question_type,
                            "options": options,
                        }
                    },
                }
            },
            "location": {
                "index": idx,
            }
        },
    }

def add_questions(service, form_id, quiz):
    """ take a Quiz object and populate the form questions """

    requests = [
        {
            "createItem": {
                "item": {
                    "title": "Enter yout name",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "textQuestion": {
                                "paragraph": False
                            }
                        }
                    }
                },
                "location": {
                    "index": 0
                }
            }
        },
    ]

    for index, question in enumerate(quiz["questions"]):
        requests.append(
            create_question(question_type="RADIO", title=question["title"], idx=index + 1, options=
                [{"value": option} for option in question["options"]], correct_answer=question["answer_key"]
            )
        )

    update_request = { "requests": requests }
    service.forms().batchUpdate(formId=form_id, body=update_request).execute()


def make_quiz_from_form(service, form_id):
    form = {
          "updateSettings": {
            "settings": {
              "quizSettings": {
                "isQuiz": True
              }
            },
           "updateMask": "quizSettings.isQuiz"
          }
        }

    requests = [form]
     
    service.forms().batchUpdate(formId=form_id, body={"requests": requests}).execute()


def set_answer_keys(service, form_id, quiz):
    """Set answer keys for the quiz questions."""
    requests = []

    for index, question in enumerate(quiz["questions"]):
        correct_answer = question["options"][question["answer_key"] - 1] 

        requests.append({
            "updateItem": {
                "item": {
                    "questionItem": {
                        "question": {
                            "grading": {
                                "correctAnswers": {
                                    "answers": [{"value": correct_answer}]
                                },
                            },
                        },
                    }
                },
                "location": {
                    "index": index + 1
                },
                "updateMask": "questionItem.question.grading.correctAnswers"
            }
        })

    service.forms().batchUpdate(formId=form_id, body={"requests": requests}).execute()

service = authenticate()

file = open('quiz.txt')
text = file.read().strip()

quiz = eval(text)

form_id = create_form(service, quiz["quiz_title"])
add_questions(service, form_id, quiz)
make_quiz_from_form(service, form_id)
set_answer_keys(service, form_id, quiz)

