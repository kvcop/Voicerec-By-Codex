"""Service layer package."""

<<<<<< codex/2025-09-27-generate-python-stubs-and-async-wrappers
from app.services.pipeline import PipelineService, get_pipeline_service
=======
from app.services.meeting_processing import (
    MeetingEvent,
    MeetingProcessingResult,
    MeetingProcessingService,
)
>>>>>> main
from app.services.transcript import (
    MeetingNotFoundError,
    StreamItem,
    TranscriptService,
    get_transcript_service,
    resolve_raw_audio_dir,
)

__all__ = [
<<<<<< codex/2025-09-27-generate-python-stubs-and-async-wrappers
    'RAW_AUDIO_DIR',
    'PipelineService',
    'TranscriptService',
    'get_pipeline_service',
    'get_transcript_service',
=======
    'MeetingEvent',
    'MeetingNotFoundError',
    'MeetingProcessingResult',
    'MeetingProcessingService',
    'StreamItem',
    'TranscriptService',
    'get_transcript_service',
    'resolve_raw_audio_dir',
>>>>>> main
]
