from __future__ import annotations
import time
from typing import Any, List, Union
import uuid

from agent.agent_base import *
from models.openai_agent import *

from tools.tool_base import *
from utils.utils import *
from tasks.task_literals import *
import models.model_base as model_base
import settings


class Task:

    def __init__(self,
                 model: AIModel,
                 instructions: str = "",
                 default_input: str = "",
                 name: str = None,
                output_type: Union[OutputType, str] = OutputType.TEXT,
                input_type: Union[InputType, str] = InputType.TEXT,
                agent: Agent = Agent(role = "", prompt_persona=""),
                tool: Tool = None,
                file_paths: List[str] = None,
                previous_output: Any = None,
                resource_box: ResourceBox = ResourceBox(),
                input_tasks: List[Task] = None,
                enhance_prompt: bool = False,
                ):
        self.model = model
        self.instructions = instructions
        self.default_input = default_input
        self.name = name
        self.output_type = output_type
        self.input_type = input_type
        self.agent = agent
        self.tool = tool
        self.file_paths = file_paths
        self.previous_output = previous_output
        self.resource_box = resource_box
        self.input_tasks = input_tasks
        self.enhance_prompt = enhance_prompt
        self.task_id = uuid.uuid4()
        if self.tool != None:
            self.output_type = OutputType.TOOL
        if self.name == None:
            self.name = self.task_id
        if self.input_tasks == None:
            self.input_tasks = []
        if self.agent.memory != None:
            self.model = self.agent.memory.generate_memory_model(model)
        else:
            self.model = model

        self._create_task_execution_method()

    def set_resource_box(self, resource_box: ResourceBox):
        self.resource_box = resource_box

    def _create_task_execution_method(self):
        system_persona = f"In your role as {self.agent.role}, you embody a person defined as {self.agent.prompt_persona}."
        prompt = f"Now execute these instructions: {self.instructions}."

        if self.output_type == OutputType.TEXT:
            self._execute_task = lambda: self._generate_text(
                system_persona=system_persona,
                prompt=prompt
            )
        
        if self.output_type == OutputType.IMAGE:
            self._execute_task = lambda: self._generate_image(
                system_persona=system_persona,
                prompt=prompt
            )
        
        if self.output_type == OutputType.TOOL:
            self._execute_task = lambda: self._execute_tool(
                system_persona=system_persona,
                prompt=prompt
            )


    def _generate_text(self, system_persona: str, prompt: str):
        if self.enhance_prompt:
            prompt = enhance_prompt(prompt=prompt, model= self.model)
        return self.model.generate_text(
            task_id=self.task_id,
            system_persona=system_persona,
            prompt=f"Prompt: {prompt}  Input: {self.previous_output} {self.default_input}"
        )
    
    def _generate_image(self, prompt: str):
        return self.model.generate_image(
            task_id = self.task_id,
            prompt=f"Create an image based on this prompt: {prompt} and Input: {self.previous_output} {self.default_input}. Dont include text in image",
            resource_box=self.resource_box
        )
    
    def _execute_tool(self,system_persona, prompt):
        return self.tool.run_tool(
            task_id=self.task_id,
            instructions=f"${system_persona} ${prompt}",
            input=f"{self.previous_output} {self.default_input}",
            model=self.model
        )
    
    def execute(self):
        self.log_output = True
        if self.log_output == True:
            # TODO create a better logger
            execution_start_time = time.time()
            print(
                f"START TASK {self.name} :: start time : {str(execution_start_time)}"
            )
            self.output = self._execute_task()
            execution_end_time = time.time()
            execution_time = execution_end_time - execution_start_time
            print(
                f"END TASK {self.name} :: end time :  {str(execution_end_time)} :: execution time : {execution_time}"
            )
        else:
            self.output = self._execute_task()
        return self.output