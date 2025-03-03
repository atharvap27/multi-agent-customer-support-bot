from duckduckgo_search import DDGS
from pydantic import BaseModel
from typing import Optional
import time
from simple_salesforce import Salesforce
import os
from dotenv import load_dotenv
load_dotenv()

sf = Salesforce(username="",password="",security_token="")
                
d = DDGS(timeout=120)

class EmailRequestModel(BaseModel):
    subject: str
    description: str


class ResearchInput(BaseModel):
        query: str

class ResearchOutput(BaseModel):
        success: str
        message: Optional[str]
        research_output: str

class docInput(BaseModel):
        file_path: str
        content: str

class docOutput(BaseModel):
        success: str
        message: Optional[str]

def search_website(query):
        print("QUERY: ", query)
        results = d.text(query, region='wt-wt', safesearch='off', timelimit='y', max_results=20)
        return results

def write_to_doc(file_path, content):
        with open(file_path, "w") as f:
                f.write(content)
