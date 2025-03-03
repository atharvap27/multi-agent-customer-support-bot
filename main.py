from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from simple_salesforce import Salesforce
import os

app = FastAPI()

# Salesforce connection setup
sf = Salesforce(username="",password="",security_token="")

class CaseModel(BaseModel):
    Id: str
    CaseNumber: str
    Subject: str
    Status: str
    Priority: str
    Description: str
    ContactEmail: str

class EmailMessageModel(BaseModel):
    Id: str
    Subject: str
    TextBody: str
    FromAddress: str

class EmailRequestModel(BaseModel):
    subject: str
    description: str

@app.get("/cases")
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

@app.post("/reply-cases")
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
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)