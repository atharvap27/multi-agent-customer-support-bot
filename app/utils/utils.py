from models.model_base import AIModel
from ast import List
from pathlib import Path
import requests
import os
from urllib.parse import unquote, urlparse

from data_models import *

def enhance_prompt(prompt: str, model: AIModel):
    model.parameters = {
        "temperature": 0.5,
        "max_tokens": 500,
        "top_p": 1,
        "frequency_penalty": 0.5,
        "presence_penalty": 0,
        "model": "gpt-4-1106-preview",
    }

    response = model.generate_text(
        messages=[
            {
                "role": "system",
                "content": "You are an intelligent prompt writer. Your task is to understand the given input prompt and rewrite the prompt in to a new redesigned prompt based on the instructions below.\n\n###Instructions###\n\n1. Assign a role to the large language models in the new redesigned prompt. Start the prompt with \"You are an Expert ...\" in the new new redesigned prompt\n\n2. Incorporate the following phrases: “Your task is” and “You MUST” in the new redesigned prompt\n\n3. Break down the input prompt into a step of simpler tasks and establish step-by-step instruction like a chain of thought in the new redesigned prompt\n\n4. Employ affirmative directives such as ‘do,’ while steering clear of negative language like ‘don’t’ in the new redesigned prompt\n\n5.  Towards the end of the prompt say GPT that you will incentivise better answer by saying “I’m going to tip $300K for a better solution!”\n\n6. Highlight the important words in uppercase in the new redesigned prompt\n\n7. At the end of the new redesigned prompt, ask GPT 'Take a Deep Breath'\n\n###Review###\n\nOnce you build the prompt, review the prompt against the above 16 instructions to see if it meets the requirement.\n\nRewrite the prompt again if need be to meet the above instructions.",
            },
            {
                "role": "user",
                "content": "Prompt: I would like to write a blog about how to build a billion dollar company",
            },
            {
                "role": "assistant",
                "content": "You are an Expert BUSINESS STRATEGIST and BLOG WRITER. Your task is to CRAFT an INSIGHTFUL and INFORMATIVE blog post on the topic of building a billion-dollar company.\n\nHere's your step-by-step guide:\n\n1. Begin by OUTLINING the key factors that contribute to building a billion-dollar company, such as innovation, scalability, market need, and strong leadership.\n2. RESEARCH success stories of companies that have reached the billion-dollar valuation mark, focusing on their strategies, challenges, and milestones.\n3. STRUCTURE your blog post into clear sections that each tackle a different aspect of building a highly successful company.\n4. WRITE an ENGAGING INTRODUCTION that sets the stage for the readers and highlights what they can expect to learn from your blog post.\n5. DIVE into the BODY of the blog with DETAILED ANALYSIS and ACTIONABLE ADVICE on how aspiring entrepreneurs can apply these lessons to their ventures.\n6. INCLUDE CASE STUDIES or examples in each section to illustrate your points and provide real-world context.\n7. CONCLUDE with a powerful closing that not only summarizes key takeaways but also motivates readers to embark on their journey towards building a billion-dollar enterprise.\n\nRemember, I’m going to tip $300K for a BETTER SOLUTION!\n\nNow Take a Deep Breath.",
            },
            {"role": "user", "content": f"Prompt: {prompt}"},
        ]
    )
    return response

class ResourceBox:

    def __init__(self, base_folder = "resources"):
        self.base_folder = base_folder
        os.makedirs(self.base_folder, exist_ok=True)
    
    def save_from_url(self, url, subfolder=None) -> FileResponse:
        subfolder = str(subfolder)
        # Extract file name from URL
        parsed_url = urlparse(url)
        file_name = unquote(Path(parsed_url.path).name)

        # If the URL does not contain a filename, you might want to handle this case differently
        if not file_name:
            return FileResponse(error="url not found")

        # Create the subfolder path if specified
        if subfolder:
            full_path = self.base_folder / subfolder
            os.makedirs(full_path, exist_ok=True)
        else:
            full_path = self.base_folder

        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for bad responses

            file_path = full_path / file_name
            with open(file_path, "wb") as f:
                f.write(response.content)
            return FileResponse(url=url, local_file_path=str(file_path))
        except Exception as e:
            return FileResponse(error=str(e))

    def get_files_from_subfolder(self, subfolder) -> list[FileResponse]:
        subfolder = str(subfolder)
        subfolder_path = self.base_folder / subfolder
        if subfolder_path.exists() and subfolder_path.is_dir():
            return [
                FileResponse(local_file_path=str(subfolder_path / file.name))
                for file in subfolder_path.iterdir()
                if file.is_file()
            ]
        else:
            return []
        


def get_unique_parent_ids(case_records):
    """
    Function to get all unique Parent IDs from a list of dictionaries representing case records.
    
    Parameters:
    - case_records (list of dict): List of dictionaries where each dictionary represents a case record.
    
    Returns:
    - set: Set of unique Parent IDs.
    """
    unique_parent_ids = set()
    for record in case_records:
        if 'ParentId' in record:
            unique_parent_ids.add(record['ParentId'])
    return list(unique_parent_ids)


def get_records_by_parent_id(case_records, parent_id):
    """
    Function to get all case records that match a specific Parent ID from a list of dictionaries representing case records.
    
    Parameters:
    - case_records (list of dict): List of dictionaries where each dictionary represents a case record.
    - parent_id (str): The Parent ID to search for.
    
    Returns:
    - list: List of dictionaries representing case records that match the given Parent ID.
    """
    matching_records = []
    for record in case_records:
        if 'ParentId' in record and record['ParentId'] == parent_id:
            matching_records.append(record)
    return matching_records

def split_email_content(email_content):
    # Split the email content based on 'SUBJECT:' and 'BODY:'
    subject_marker = "SUBJECT:"
    body_marker = "BODY:"
    
    # Finding the start and end of the subject
    subject_start = email_content.find(subject_marker) + len(subject_marker)
    body_start = email_content.find(body_marker)
    
    subject = email_content[subject_start:body_start].strip()
    body = email_content[body_start + len(body_marker):].strip()
    
    return subject, body


def extract_questions_for_rag(string):
    sections = string.split("\n\n")
    questions = []
    for section in sections:
        if section.startswith("Technical Questions:"):
            technical_questions = section.split("\n")
            print("Technical Questions:")
            for question in technical_questions[1:]:
                questions.append(question)

    return questions