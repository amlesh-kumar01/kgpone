from src.utils.interfaces import IS3Storage

class S3Storage(IS3Storage):
    def upload(self, file_name: str, file_content: bytes):
        pass
