from abc import ABC, abstractmethod


class BaseAgent(ABC):

    @abstractmethod
    def handle(self, **kwargs):
        """
        Execute the task assigned to this agent.
        """
        pass