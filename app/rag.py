from qdrant_client import QdrantClient
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from qdrant_client.http.models import PointStruct
from agent.agent_base import *
from tools.prebuilt_tools import *
from tools.research import *
from tasks.task_base import *
from pipeline.linear_sync_pipeline import *
import openai
openai.api_key = ""
openai_api_key = ""

qdrant_client = QdrantClient(
    url="", 
    api_key="",
)


class RAG:

    def __init__(self, qdrant_client):
        self.qdrant_client = qdrant_client

    def read_data_from_pdf_folder(self, folder_path):
        text = ""
        for filename in os.listdir(folder_path):
            if filename.endswith(".pdf"):
                file_path = os.path.join(folder_path, filename)
                with open(file_path, 'rb') as file:
                    pdf_reader = PdfReader(file)
                    for page in pdf_reader.pages:
                        text += page.extract_text()
        return text
    
    def get_text_chunks(self,text):
        text_splitter = CharacterTextSplitter(
            separator = "\n", chunk_size=1000, chunk_overlap=200, length_function=len
        )
        chunks = text_splitter.split_text(text)
        return chunks
    
    def get_embeddings(self,text_chunks, model_id="text-embedding-ada-002"):
        points = []
        for idx, chunk in enumerate(text_chunks):
            response = openai.embeddings.create(
                input=chunk,
                model=model_id
            )
            embeddings = response.data[0].embedding
            point_id = str(uuid.uuid4())
            points.append(PointStruct(id=point_id, vector=embeddings, payload={"text": chunk}))

        return points
    
    def insert_data(self,get_points):
        operation_info = self.qdrant_client.upsert(
            collection_name="customer_support",
            wait=True,
            points=get_points
        )

    def create_answer_with_context(self,query):
        response = openai.embeddings.create(
            input=query,
            model="text-embedding-ada-002"
        )
        embeddings = response.data[0].embedding
        search_result = self.qdrant_client.search(
            collection_name='customer_support',
            query_vector=embeddings,
            limit=3
        )

        print("QUESTION: ", query, '\n')

        prompt = ""
        for result in search_result:
            prompt+=result.payload['text']
        concatenated_string = " ".join([prompt, query])
        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages = [
                {"role":"user", "content": concatenated_string}
            ]
        )
        return completion.choices[0].message.content
    
rag = RAG(qdrant_client=qdrant_client)

def initialize():
    get_raw_text = rag.read_data_from_pdf_folder('./docs')
    chunks = rag.get_text_chunks(get_raw_text)
    vectors = rag.get_embeddings(chunks)
    rag.insert_data(vectors)

def get_answer(question):
    answer = rag.create_answer_with_context(question)
    return answer

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
