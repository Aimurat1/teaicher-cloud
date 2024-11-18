import os
import subprocess
from typing import List

from model.question import Question

TEMP_MD_FILE = "__temp.md"
TEMP_PDF_FILE = "__temp.pdf"


def questions_to_markdown(questions: List[Question]) -> str:
    """
    Convert a list of questions to Markdown
    :param questions: List of questions
    :return: Markdown string
    """
    markdown = ""

    for index, question in enumerate(questions):
        markdown += f"**{index + 1}. {question.question}**\n\n"

        for answer in question.answers:
            markdown += f"- [ ] {answer}\n"

        markdown += "\n"

    return markdown


def questions_to_markdown_with_answers(questions: List[Question]) -> str:
    """
    Convert a list of questions to Markdown with answers
    :param questions: List of questions
    :return: Markdown string
    """
    markdown = ""

    for index, question in enumerate(questions):
        markdown += f"**{index + 1}. {question.question}**\n\n"

        for i, answer in enumerate(question.answers):
            if i == question.correct_answer:
                markdown += f"- [X] {answer}\n"
            else:
                markdown += f"- [ ] {answer}\n"

        markdown += f"\n**Explanation:** {question.explanation}\n\n"

    return markdown


def markdown_to_pdf(markdown: str, output_file: str):
    """
    Convert Markdown to PDF
    :param markdown: Markdown string
    :param output_file: Output file
    """
    with open(TEMP_MD_FILE, "w") as f:
        f.write(markdown)

    subprocess.run([
        "mdpdf", TEMP_MD_FILE,
        "--output", output_file,
        "--footer", ",,{page}",
        "--paper", "A4"
    ])

    os.remove(TEMP_MD_FILE)


def questions_to_pdf(questions: List[Question], output_file: str):
    """
    Convert a list of questions to PDF
    :param questions: List of questions
    :param output_file: Output file
    """
    markdown = questions_to_markdown(questions)
    markdown_to_pdf(markdown, output_file)


def questions_with_answers_to_pdf(questions: List[Question], output_file: str):
    """
    Convert a list of questions to PDF
    :param questions: List of questions
    :param output_file: Output file
    """
    markdown = questions_to_markdown_with_answers(questions)
    markdown_to_pdf(markdown, output_file)
