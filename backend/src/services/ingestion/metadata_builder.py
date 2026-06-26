from src.models.document_model import Document

class MetadataBuilder:
    @staticmethod
    def build(document: Document) -> dict:
        """
        Builds a flattened metadata dictionary from the Document and its relations.
        """
        course_offering = document.course_offering
        course = course_offering.course
        uploader = document.uploader
        
        metadata = {
            "document_id": str(document.id),
            "document_version": document.version,
            "course_offering_id": str(course_offering.id),
            "course_id": str(course.id),
            "course_code": course.code,
            "course_name": course.title,
            "semester": course_offering.semester.value,
            "year": course_offering.year,
            "document_title": document.title,
            "document_type": document.doc_type,
            "document_format": document.format.value,
            "status": document.status.value,
            "created_at": document.created_at.isoformat() if document.created_at else None,
            "s3_key": document.s3_key,
        }
        
        if uploader:
            metadata["uploader_id"] = str(uploader.id)
            
        # Flatten DocumentMetadata entries directly into the root dict
        # Ensure we don't overwrite primary keys unexpectedly
        reserved_keys = set(metadata.keys())
        for entry in document.metadata_entries:
            key = entry.key
            if key not in reserved_keys:
                metadata[key] = entry.value
                
        return metadata
