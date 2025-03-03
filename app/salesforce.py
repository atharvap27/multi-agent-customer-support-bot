from simple_salesforce import Salesforce

sf = Salesforce(username="",password="",security_token="")

def get_all_cases():
    try:
        query = """
        SELECT Id, CaseNumber, Subject, Status, Priority, Description, Contact.Email,
               (SELECT Id, Subject, TextBody, FromAddress FROM EmailMessages ORDER BY CreatedDate ASC)
        FROM Case
        """
        cases = sf.query_all(query)['records']
        
        transformed_cases = []
        for case in cases:
            case_data = {
                'ParentId': case['Id'],
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
                        'ParentId': case['Id'],
                        'Id': email_message['Id'],
                        'CaseNumber': case['CaseNumber'],
                        'Subject': email_message['Subject'],
                        'Status': case['Status'],
                        'Priority': case['Priority'],
                        'Description': email_message['TextBody'],
                        'ContactEmail': case['Contact']['Email'] if case['Contact'] else None
                    }
                    transformed_cases.append(email_data)

        return transformed_cases
    except Exception as e:
        print(e)


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

def reply_to_cases(subject, description, parent_id, contact_email):
    try:
        cases = get_all_cases()
        cases_with_emails = [case for case in cases if case['ContactEmail']]

        if not cases_with_emails:
            return {"message": "No cases with email addresses found"}

        email_reply = {
            'Subject': subject,
            'HtmlBody': description,
            'ParentId': parent_id,  # Link the email to the case
            'ToAddress': contact_email,
            'Status': '3'  # Draft status initially
        }

        # Create the EmailMessage record
        result = sf.EmailMessage.create(email_reply)
        return
        
        # if result['success']:
        #     # Update the status to '3' (sent) to send the email
        #     email_id = result['id']
        #     update_result = sf.EmailMessage.update(email_id, {'Status': '3'})
            
        #     if update_result == 204:  # HTTP status code for successful update (No Content)
        #         return {"message": "Replies created and sent successfully in Salesforce"}
        #     else:
        #         return {"message": "Replies created but failed to send"}
        # else:
        #     return {"message": "Failed to create EmailMessage"}

    except Exception as e:
        print(f"Error: {e}")
        return {"message": f"An error occurred: {e}"}