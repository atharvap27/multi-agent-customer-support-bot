from typing import List, Dict, Any, Callable, Union
from agent.agent_base import Agent
from tools.tool_base import Tool

class SupervisorTask:
    def __init__(self, original_instruction: str, tools: List[Tool], agents: List[Agent]):
        self.original_instruction = original_instruction
        self.tools = tools
        self.agents = agents
        self.previous_outputs = []

    def run(self) -> str:
        """
        The main loop that manages the flow of tools/agents execution.
        """
        done = False
        current_output = self.original_instruction

        while not done:
            next_step = self._determine_next_step(current_output)
            if next_step is None:
                done = True
                final_output = current_output
            elif isinstance(next_step, Tool):
                current_output = self._run_tool(next_step, current_output)
                self.previous_outputs.append(current_output)
            elif isinstance(next_step, Agent):
                current_output = self._run_agent(next_step, current_output)
                self.previous_outputs.append(current_output)
            else:
                raise ValueError(f"Invalid next step: {next_step}")

        return final_output

    def _determine_next_step(self, current_output: str) -> Union[Tool, Agent, None]:
        # Implement your logic here
        pass

    def _run_tool(self, tool: Tool, input: str) -> str:
        """
        Run the given tool with the provided input and return the output.
        """
        return tool.run_tool(task_id="supervisor_task", instructions="", input=input, model=None)

    def _run_agent(self, agent: Agent, input: str) -> str:
        """
        Run the given agent with the provided input and return the output.
        """
        return agent.run(input)

# In this implementation, the `SupervisorTask` class takes the original instruction, a list of available tools, and a list of available agents as input. The `run` method is the main loop that manages the flow of tool/agent execution. It starts with the original instruction as the current output and iteratively determines the next step (tool, agent, or None if done) based on the current output using the `_determine_next_step` method.

# If the next step is a tool, the `_run_tool` method is called to execute the tool with the current output as input, and the tool's output is stored as the new current output. If the next step is an agent, the `_run_agent` method is called to execute the agent with the current output as input, and the agent's output is stored as the new current output.

# The `_determine_next_step` method is responsible for determining the next step based on the current output. This method can be implemented using an AI model or a rule-based approach, depending on your requirements.

# Note that you'll need to implement the `Tool` and `Agent` classes according to your specific needs. The `Tool` class should have a `run_tool` method that takes the task ID, instructions, input, and an AI model as input, and returns the output of the tool. The `Agent` class should have a `run` method that takes the input and returns the output of the agent.

# With this implementation, you can create an instance of the `SupervisorTask` class, passing the original instruction, a list of available tools, and a list of available agents. Then, you can call the `run` method to execute the supervisor task, which will manage the flow of tool/agent execution and return the final output.