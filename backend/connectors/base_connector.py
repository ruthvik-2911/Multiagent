from abc import ABC, abstractmethod

class BaseConnector(ABC):

    @abstractmethod
    def authenticate(self):
        pass

    @abstractmethod
    def fetch(self):
        pass

    @abstractmethod
    def transform(self, item):
        pass

    @abstractmethod
    def index(self, item):
        pass
