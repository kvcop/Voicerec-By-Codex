"""Service layer package."""

from app.services.auth import (
    AUTH_SCHEME_BEARER,
    AuthService,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    LoginResult,
    get_auth_service,
)
from app.services.meeting_processing import (
    MeetingEvent,
    MeetingProcessingResult,
    MeetingProcessingService,
)
from app.services.pipeline import PipelineService, get_pipeline_service
from app.services.transcript import (
    MeetingNotFoundError,
    StreamItem,
    TranscriptService,
    get_transcript_service,
    resolve_raw_audio_dir,
)

__all__ = [
    'AUTH_SCHEME_BEARER',
    'AuthService',
    'EmailAlreadyExistsError',
    'InvalidCredentialsError',
    'LoginResult',
    'MeetingEvent',
    'MeetingNotFoundError',
    'MeetingProcessingResult',
    'MeetingProcessingService',
    'PipelineService',
    'StreamItem',
    'TranscriptService',
    'get_auth_service',
    'get_pipeline_service',
    'get_transcript_service',
    'resolve_raw_audio_dir',
]
