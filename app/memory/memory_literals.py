from enum import Enum


class MemoryProvider(Enum):
    DEFAULT = "default"
    LLAMA_INDEX = "llama_index"
    OPEN_AI = "open_ai"