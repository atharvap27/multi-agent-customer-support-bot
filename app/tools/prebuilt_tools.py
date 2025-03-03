from tools.tool_base import *
from tools.research import *

def research(query):
    return Tool(
        name="Research",
        desc="Researches about the provided topic from internet",
        function=search_website,
        function_input=ResearchInput,
        function_output=ResearchOutput,
        default_params={"query": query}
    )

def doc_writer_tool(file_path, content):
    return Tool(
        name="Document witer",
        desc="Writes the content into a file given file path",
        function=write_to_doc,
        function_input=docInput,
        function_output=docOutput,
        default_params={"file_path": file_path, "content": content}
    )