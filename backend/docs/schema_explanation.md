# Schema Explanation

## PostgreSQL (Relational) Database
The relational data is managed by SQLAlchemy and Alembic.

1. **Users**: Stores `User` identities. Roles include `ADMIN`, `STUDENT`, `TA`, `PROFESSOR`.
2. **Departments**: Organizes the university into `code` (e.g. `CSE`) and `name` (e.g. `Computer Science`).
3. **Courses**: Central `Course` entity linking back to a department.
4. **CourseOfferings**: Represents a specific instance of a course (e.g., `Autumn 2026`). Links to the base `Course`.
5. **Documents**: Represents an uploaded file (e.g., PDF notes, PyQ). Links to a `CourseOffering`. Contains `title`, `doc_type` (e.g., `PYQ`, `NOTES`), and the AWS `s3_key`. It also tracks Celery pipeline `ProcessingStatus`.
6. **DocumentMetadata**: Key-value pairs attached to a `Document` representing arbitrary extra data (e.g. `professor = Dr XYZ`).

## Qdrant (Vector) Database
The vector data is completely decoupled from PostgreSQL but shares IDs for synchronization.

### Flattened Payload Strategy
When a document is chunked and embedded by Celery, the system does **not** insert nested JSON into Qdrant. Instead, it uses `MetadataBuilder` to flatten all PostgreSQL relational attributes into standard top-level fields for lightning-fast Qdrant `Payload Index` search.

**Example Qdrant Point Payload:**
```json
{
  "document_id": "uuid",
  "course_offering_id": "uuid",
  "course_code": "CS101",
  "course_name": "Intro to Programming",
  "semester": "AUTUMN",
  "year": 2026,
  "document_type": "PYQ",
  "professor": "Dr XYZ",
  "chunk_index": 5,
  "content": "Dynamic programming is a method for solving complex problems..."
}
```

This allows extremely optimized exact-match filtering like:
```python
FieldCondition(key="course_code", match=MatchValue(value="CS101"))
```
