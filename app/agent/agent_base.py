class Agent:
    def __init__(self, role: str, prompt_persona: str="", memory=None):
        self.role = role
        self. prompt_persona = prompt_persona
        self.memory = memory