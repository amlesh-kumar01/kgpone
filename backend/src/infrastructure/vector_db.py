from src.core.interfaces import IVectorRepo

class QdrantRepo(IVectorRepo):
    def search(self, query: str):
        pass
