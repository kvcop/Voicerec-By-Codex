"""Service layer package."""

from app.services.meeting_processing import (
    MeetingEvent,
    MeetingProcessingResult,
    MeetingProcessingService,
)
from app.services.transcript import (
<<<<<< codex/2025-09-27-add-domain-service-for-meeting-processing
    RAW_AUDIO_DIR,
    StreamItem,
=======
>>>>>> main
    TranscriptService,
    get_transcript_service,
    resolve_raw_audio_dir,
)

<<<<<< codex/2025-09-27-add-domain-service-for-meeting-processing
__all__ = [
    'RAW_AUDIO_DIR',
    'MeetingEvent',
    'MeetingProcessingResult',
    'MeetingProcessingService',
    'StreamItem',
    'TranscriptService',
    'get_transcript_service',
]
=======
__all__ = ['TranscriptService', 'get_transcript_service', 'resolve_raw_audio_dir']
>>>>>> main
