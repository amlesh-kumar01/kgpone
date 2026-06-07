from abc import ABC, abstractmethod

class IVectorRepo(ABC):
    @abstractmethod
    def search(self, query: str):
        pass

class IS3Storage(ABC):
    @abstractmethod
    def upload(self, file_name: str, file_content: bytes):
        pass
