import streamlit as st
from time import sleep
from salesforce import *
from all_agents import *
from rag import *
import streamlit as st
from time import sleep

st.set_page_config(page_title="Automated Salesforce Process", layout="wide")
def run_main():
    st.markdown("""
        <style>
        .main {
            background-color: #e0f7fa;
            color: #333;
        }
        h1 {
            color: #00796b;
        }
        .stText {
            font-size: 18px;
            font-weight: 500;
        }
        .stButton>button {
            background-color: #00796b;
            color: white;
            font-size: 16px;
            border-radius: 10px;
            height: 50px;
            width: 100%;
        }
        .stProgressBar>div>div {
            background-color: #00796b;
        }
        </style>
    """, unsafe_allow_html=True)

    st.header('Automated Salesforce Process')
    all_case_data = get_all_cases()
    print("ALL CASE DATA: ", all_case_data)

    st.markdown("## 🚀 Starting the Pipeline")
    with st.spinner('Loading...'):
        sleep(1)
    
    unique_parent_ids = get_unique_parent_ids(all_case_data)
    print(unique_parent_ids)
    
    for parent_id in unique_parent_ids:
        st.markdown(f"### 📂 Processing Case ID: {parent_id}")
        with st.spinner('Fetching records...'):
            records_by_id = get_records_by_parent_id(all_case_data, parent_id)
            sleep(1)
        subject_record = records_by_id[-1]['Subject']
        description_record = records_by_id[-1]['Description']
        contact_email = records_by_id[-1]['ContactEmail']

        st.markdown("#### ✉️ Checking if the client has replied")
        with st.spinner('Classifying email...'):
            email_classifier_task = Task(
                name="Process Determiner",
                output_type=OutputType.TEXT,
                input_type=InputType.TEXT,
                model=open_ai_model,
                agent=email_summary_writer_agent,
                instructions="""
                You are responsible for REVIEWING an EMAIL and DETERMINING if the EMAIL IS WRITTEN BY CUSTOMER SUPPORT EXECUTIVE OR CLIENT.
                GIVE THE OUTPUT JUST AS "CUSTOMER SUPPORT EXECUTIVE" OR "CLIENT"
                """,
                enhance_prompt=True,
                default_input=subject_record + description_record
            ).execute()
            sleep(1)

        if "CLIENT" in email_classifier_task:
            st.markdown("#### 📝 Creating a summary of case email conversation history")
            with st.spinner('Writing summary...'):
                summary_task = Task(
                    name="Summary writer",
                    output_type=OutputType.TEXT,
                    input_type=InputType.TEXT,
                    model=open_ai_model,
                    agent=email_summary_writer_agent,
                    instructions="""
                    You are a PROFESSIONAL SUMMARY WRITER. 
                    Your task is to CONSTRUCT A DETAILED SUMMARY from a LIST OF EMAIL CONVERSATIONS, each having a SUBJECT and BODY (DESCRIPTION). 
                    This summary should be DETAILED, COVERING ALL NECESSARY DETAILS, and should be in a PARAGRAPH FORMAT as it will be used by another system to GENERATE QUESTIONS to help us REPLY TO THE LATEST EMAIL.
                    ALWAYS INCLUDE EVERY DETAIL from the LAST 4 EMAILS as they are the MOST RECENT and CRITICALLY IMPORTANT for drafting the NEXT EMAIL RESPONSE. Explain the summary as if you are addressing it to a TECHNICAL SUPPORT SPECIALIST, ensuring all RELEVANT DETAILS and CONTEXT are CLEAR and PRECISE.
                    Make sure the summary is COMPREHENSIVE and COVERS ALL ASPECTS discussed in the emails, especially FOCUSING ON THE KEY POINTS and ISSUES RAISED in the LATEST COMMUNICATIONS.
                    """,
                    enhance_prompt=False,
                    default_input=records_by_id
                ).execute()
                sleep(1)

            st.markdown("#### 🔍 Looking through for the solutions")
            with st.spinner('Designing questionnaire...'):
                question_framer_task = Task(
                    name="Questionnaire Designer",
                    output_type=OutputType.TEXT,
                    input_type=InputType.TEXT,
                    model=open_ai_model,
                    agent=question_framer_agent,
                    instructions="""
                    You are a customer support TROUBLESHOOTING EXPERT who works in the customer support team.
                    Your task is to UNDERSTAND the email conversation and its summary in detail. 
                    After getting a deep understanding of the conversation, issues faced by customer, solutions suggested by the customer support agent and then solutions tried by the customer, give the NEXT STEPS that the CUSTOMER needs to try.
                    Also, if you have any TECHNICAL QUESTIONS whose answer is needed to be searched from the COMPANY INTERNAL TECHNICAL DOCUMENTS using RETRIEVAL AUGMENTED GENERATION system, mention them as well.
                    If you have any QUESTIONS that you want to ask to the CLIENT for BETTER CLARITY, mention that as well.
                    - Give output ONLY in following format:
                    Next Steps for customer: 

                    Technical Questions:

                    Questions for Client: 

                    - ONLY GIVE THE OUTPUT IN ABOVE FORMAT AND DONT GIVE ANY OTHER TEXT.
                    """,
                    enhance_prompt=False,
                    default_input=[records_by_id, summary_task]
                ).execute()
                sleep(1)

            st.markdown("#### 🔄 Initiating RAG")
            with st.spinner('Processing documents...'):
                question_for_rag = extract_questions_for_rag(question_framer_task)
                que_ans = {}
                for question in question_for_rag:
                    answer = get_answer(question)
                    que_ans[question] = answer
                sleep(1)
                
            st.markdown("#### ✍️ Composing the email")
            with st.spinner('Writing email...'):
                email_writer_task = Task(
                    name="Email writer",
                    output_type=OutputType.TEXT,
                    input_type=InputType.TEXT,
                    model=open_ai_model,
                    agent=email_creator_agent,
                    instructions="""
                    You are a PROFESSIONAL CUSTOMER SUPPORT EXECUTIVE WHO EXCELS IN EMAIL WRITING. 
                    Your task is to CREATE A PROFESSIONAL EMAIL given summary of previous emails, the last email to which you are writing the reply, and the content that email should have.
                    You will receive PAIRS of QUESTIONS and ANSWERS GENERATED by ANOTHER SYSTEM designed to formulate questions that require SEARCHING through ORGANISATION INTERNAL DOCUMENTS for their ANSWERS. Use them to formulate the email as well. 
                    REMEMBER these PAIRS of QUESTIONS and ANSWERS are NOT given by CUSTOMER BUT by ANOTHER SYSTEM like YOU. So just CHECK if these question answer pairs can help YOU better GUIDE the CUSTOMER for TROUBLESHOOTING and DONT write anything like "based on the technical questions provided". 
                    - ALWAYS KEEP THE EMAIL IN FOLLOWING FORMAT:
                    SUBJECT: The subject of the email

                    BODY: The email body
                    - MAKE SURE that this email looks like it is written by a professional technical support person and not by AI. Make the email humble, polite and interactive.
                    - MENTION THE NAME OF THE CUSTOMER IF YOU GET IT FROM THE INPUT.
                    - NO TEXT EXCEPT THE EMAIL
                    - JUST MENTION WARM REGARDS WITHOUT ANY NAME OR CONTACT AT THE END.
                    """,
                    enhance_prompt=False,
                    default_input=[summary_task, records_by_id[-1], question_framer_task, que_ans]
                ).execute()
                sleep(1)
            
            st.markdown("#### 📬 Replying back to the client")
            with st.spinner('Sending email...'):
                subject, body = split_email_content(email_writer_task)
                print("SUBJECT: ", subject)
                print("BODY: ", body)
                reply_to_cases(subject=subject, description=body, parent_id=parent_id, contact_email=contact_email)
                st.success(f"Replied to the client successfully for Case ID {parent_id}")
                sleep(1)

            with st.spinner('Updating status on Salesforce...'):
                email_status_updater_task = Task(
                    name="Salesforce Case status determiner",
                    output_type=OutputType.TEXT,
                    input_type=InputType.TEXT,
                    model=open_ai_model,
                    agent=email_creator_agent,
                    instructions="""
                    You are a PROFESSIONAL SALESFORCE CASE STATUS DETERMINER, who understand the CASE HISTORY, LATEST EMAIL, and decides the STATUS:
                    FOLLOWING ARE THE STATUS AVAILABLE. ONLY GIVE THE STATUS AS THE OUTPUT AND NO OTHER TEXT. 
                    Working: Status to be kept when the latest email depicts that we are looking for solutions and will get back to the customer.
                    Waiting on Customer: When the latest email has questions for the customer whose response we are awaiting for.
                    Escalated: When the latest client email from the case history seems frustrated and needs to be escalated.
                    Closed: When the latest 2 emails from the case email history depicts that the case is closed.
                    """,
                    enhance_prompt=False,
                    default_input=[summary_task, email_writer_task]
                ).execute()
            print(email_status_updater_task)

            update_case_status(parent_id,new_status=email_status_updater_task)
        else:
            st.info(f"No mail received from client yet for Case ID {parent_id}")

# # Streamlit UI
def main():
    st.title('Multi-Agent Customer Support Bot')

    # Login functionality
    username = st.text_input('Username')
    password = st.text_input('Password', type='password')
    
    if username == 'atharvapatilap27-rw2k@force.com' and password == 'admin12345':
        if st.button('Login'):
            st.success(f'Hi Atharva, you might have new updates, but don\'t worry, let me take care of it for you!')
            run_main()
    elif username or password:
        st.error('Incorrect username or password. Please try again.')
    run_main()
if __name__ == '__main__':
    main()



