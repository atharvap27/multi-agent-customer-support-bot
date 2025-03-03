### GET ALL THE SUBJECTS AND DESCRIPTION FOR ALL THE CASE FOR THE GIVEN USER


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from simple_salesforce import Salesforce
import os

app = FastAPI()

sf = Salesforce(username="<your-salesforce-username>",password="<password>",security_token="<security_token>")

async def get_all_cases():
    try:
        query = """
        SELECT Id, CaseNumber, Subject, Status, Priority, Description, Contact.Email,
               (SELECT Id, Subject, TextBody, FromAddress FROM EmailMessages ORDER BY CreatedDate ASC)
        FROM Case
        """
        cases = sf.query_all(query)['records']
        
        transformed_cases = []
        for case in cases:
            print(case)
            case_data = {
                'Id': case['Id'],
                'CaseNumber': case['CaseNumber'],
                'Subject': case['Subject'],
                'Status': case['Status'],
                'Priority': case['Priority'],
                'Description': case['Description'],
                'ContactEmail': case['Contact']['Email'] if case['Contact'] else None,
            }
            transformed_cases.append(case_data)
            if case['EmailMessages']:
                for email_message in case['EmailMessages']['records']:
                    email_data = {
                        'Id': email_message['Id'],
                        'CaseNumber': case['CaseNumber'],
                        'Subject': email_message['Subject'],
                        'Status': case['Status'],
                        'Priority': case['Priority'],
                        'TextBody': email_message['TextBody'],
                        'ContactEmail': case['Contact']['Email'] if case['Contact'] else None
                    }
                    transformed_cases.append(email_data)

        return transformed_cases
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from typing import List
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains import (
    ConversationalRetrievalChain,
)
from langchain.memory import ChatMessageHistory, ConversationBufferMemory
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import os
import chainlit as cl

api_key = "<YOUR API KEY>"

def load_and_process_pdfs(pdf_folder_path):
    documents = []
    for file in os.listdir(pdf_folder_path):
        if file.endswith('.pdf'):
            pdf_path = os.path.join(pdf_folder_path, file)
            loader = PyPDFLoader(pdf_path)
            documents.extend(loader.load())
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(documents)
    return splits


# Cache the function to initialize the vector store with documents
def initialize_vectorstore(splits):
    return FAISS.from_documents(documents=splits, embedding=OpenAIEmbeddings(api_key=api_key))
pdf_folder_path = "./fin_ed_docs"
splits = load_and_process_pdfs(pdf_folder_path)
vectorstore = initialize_vectorstore(splits)
model = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0, api_key=api_key)
embeddings_model = OpenAIEmbeddings(api_key=api_key)
@cl.on_chat_start
async def on_chat_start():
    retriever = vectorstore.as_retriever()
    message_history = ChatMessageHistory()
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        output_key="answer",
        chat_memory=message_history,
        return_messages=True,
    )
    chain = ConversationalRetrievalChain.from_llm(
        model,
        chain_type="stuff",
        retriever=retriever,
        memory=memory,
        return_source_documents=True,
    )
    cl.user_session.set("chain", chain)
@cl.on_message
async def main(message: cl.Message):
    chain = cl.user_session.get("chain")
    cb = cl.AsyncLangchainCallbackHandler()
    res = await chain.acall(message.content, callbacks=[cb])
    answer = res["answer"]
    source_documents = res["source_documents"]
    text_elements = []
    if source_documents:
        for source_idx, source_doc in enumerate(source_documents):
            source_name = f"source_{source_idx}"
            
            text_elements.append(
                cl.Text(content=source_doc.page_content, name=source_name)
            )
        source_names = [text_el.name for text_el in text_elements]
        if source_names:
            answer += f"\nSources: {', '.join(source_names)}"
        else:
            answer += "\nNo sources found"
    await cl.Message(content=answer, elements=text_elements).send()

##################

### Push the new created email to salesforce as well as send a mail to the user.



from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from simple_salesforce import Salesforce
import os
from module_1 import get_all_cases

app = FastAPI()


class EmailRequestModel(BaseModel):
    subject: str
    description: str

async def reply_to_cases(email_request: EmailRequestModel):
    try:
        cases = await get_all_cases()
        cases_with_emails = [case for case in cases if case['ContactEmail']]

        if not cases_with_emails:
            return {"message": "No cases with email addresses found"}

        email_reply = {
            'Subject': email_request.subject,
            'HtmlBody': email_request.description,
            'ParentId': cases_with_emails[0]['Id'],  # Link the email to the case
            'ToAddress': cases_with_emails[0]['ContactEmail'],
            'Status': '1'  # Draft status
        }
        sf.EmailMessage.create(email_reply)

        return {"message": "Replies created successfully in Salesforce"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

