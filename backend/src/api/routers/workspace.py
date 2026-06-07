from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()

@router.get("/{workspace_id}/stream")
def stream_agent(workspace_id: str):
    def fake_stream():
        yield "data: Hello\n\n"
    return StreamingResponse(fake_stream(), media_type="text/event-stream")
