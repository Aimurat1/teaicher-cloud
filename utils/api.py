import time
from typing import List

import openai
import re
import streamlit as st
import json

from model.question import Question
from dotenv import load_dotenv

load_dotenv()

MODEL = "gpt-4o"
ASSISTANT_ID = "asst_70tIJEzRxP8K3wEvdhokwH9u"

# def complete_text(prompt: str) -> str:
#     """
#     Complete text using GPT-4 with JSON response
#     """
    # try:
    #     client = openai.OpenAI(api_key=st.secrets["OPENAI_TOKEN"])
    #     messages = [
    #         {
    #             "role": "user",
    #             "content": [
    #                 {
    #                     "type": "text",
    #                     "text": prompt
    #                 }
    #             ]
    #         }
    #     ]
    #     response = client.chat.completions.create(
    #         model=MODEL,
    #         messages=messages,
    #         response_format={"type": "json_object"},
    #         seed=42,
    #     )
    #     return response.choices[0].message.content
    # except Exception as e:
    #     st.error(f"An error occurred: {str(e)}")
    #     raise
    

def complete_text(prompt: str, files=None) -> str:
    """
    Complete text using OpenAI Assistant API with JSON response
    """
    try:
        client = openai.OpenAI(api_key=st.secrets["OPENAI_TOKEN"])
        
        # Create an assistant with JSON response format
        assistant = client.beta.assistants.retrieve(ASSISTANT_ID)
        
        # Create a thread and message
        thread = client.beta.threads.create()
        
        file_ids = []
        if files:
            for file in files:
                uploaded_file = client.files.create(
                    file=file,
                    purpose='assistants'
                )
                file_ids.append(uploaded_file.id)

        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt,
            attachments=[{"file_id": file_id, "tools": [{"type": "file_search"}]} for file_id in file_ids]
        )

        # Run the assistant
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id
        )
        
        # Wait for completion
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run_status.status == 'completed':
                break
            elif run_status.status == 'failed':
                raise Exception("Assistant run failed")
            time.sleep(1)
        
        # Get the response
        messages = client.beta.threads.messages.list(
            thread_id=thread.id
        )
        
         # Extract the response text and ensure it's valid JSON
        response_text = ""
        for content in messages.data[0].content:
            if content.type == 'text':
                response_text = content.text.value
                break
        
        # Clean and parse the JSON
        # Remove any markdown code block indicators if present
        response_text = response_text.strip('`')
        if response_text.startswith('json'):
            response_text = response_text[4:]

        for file_id in file_ids:
            client.files.delete(file_id)

        # Ensure it's valid JSON by parsing and re-stringifying
        return json.dumps(json.loads(response_text))
        
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        raise


def prepare_prompt(topics: str, number_of_questions: int, number_of_answers: int) -> str:
    """
    Prepare prompt to complete
    :return: Prompt requesting JSON format
    """
    return (
        f"Create a JSON object containing an exam with {number_of_questions} multiple choice questions "
        f"about {topics}. Each question should have {number_of_answers} possible answers. "
        "In the clarification section, explain why the correct answer is correct. And not others. Does not refer to source"
        "If you have access to any files, use them to generate the questions. "
        f"Format the response as a JSON object with this structure:\n"
        "{\n"
        '  "questions": [\n'
        "    {\n"
        '      "question": "Question text",\n'
        '      "answers": ["answer1", "answer2", ...],\n'
        '      "correct_answer_index": 0,\n'
        '      "explanation": "Explanation of the correct answer"\n'
        "    }\n"
        "  ]\n"
        "}"
    )


def sanitize_line(line: str, is_question: bool) -> str:
    """
    Sanitize a line from the response
    :param line: Line to sanitize
    :param is_question: Whether the line is a question or an answer
    :return: Sanitized line
    """
    if is_question:
        new_line = re.sub(r"[0-9]+.", " ", line, count=1)
    else:
        new_line = re.sub(r"[a-eA-E][).]", " ", line, count=1)

    return new_line


def get_correct_answer(answers: List[str]) -> int:
    """
    Return the index of the correct answer
    :param answers: List of answers
    :return: Index of the correct answer if found, -1 otherwise
    """
    for index, answer in enumerate(answers):
        if answer.count("**") > 0:
            return index

    return -1


def response_to_questions(response: str) -> List[Question]:
    """
    Convert the JSON response to a list of questions
    :param response: JSON response to convert
    :return: List of questions
    """
    data = json.loads(response)
    questions = []
    
    for i, q in enumerate(data['questions'], 1):
        questions.append(Question(
            id=i,
            question=q['question'].strip(),
            answers=[a.strip() for a in q['answers']],
            correct_answer=q['correct_answer_index'],
            explanation=q.get('explanation', None)
        ))
    
    return questions


def get_questions(topics: str, number_of_questions: int, number_of_answers: int, files=None) -> List[Question]:
    """
    Get questions from OpenAI API
    :param topics: Topics to include in the exam
    :param number_of_questions: Number of questions
    :param number_of_answers: Number of answers
    :return: List of questions
    """
    try:
        prompt = prepare_prompt(topics, number_of_questions, number_of_answers)
        print("Prompt: ", prompt)
        response = complete_text(prompt, files)
        print("Response: ", response)
        questions = response_to_questions(response)
        print("Questions: ", questions)
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        raise

    return questions


def clarify_question(question: Question) -> str:
    """
    Clarify a question using GPT-3.5 Turbo
    :param question: Question to clarify
    :return: Text clarifying the question
    """
    # join_questions = "\n".join([f"{chr(ord('a') + i)}. {answer}" for i, answer in enumerate(question.answers)])

    # prompt = f"Given this question: {question.question}\n"
    # prompt += f" and these answers: {join_questions}\n\n"
    # prompt += f"Why the correct answer is {chr(ord('a') + question.correct_answer)}?\n\n"

    # return complete_text(prompt)
    
    return question.explanation
