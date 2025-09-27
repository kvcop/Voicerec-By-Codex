"""Client implementations for GPU gRPC services."""

from app.clients.grpc_clients import (
    DiarizeGrpcClient,
    SummarizeGrpcClient,
    TranscribeGrpcClient,
)

__all__ = [
    'DiarizeGrpcClient',
    'SummarizeGrpcClient',
    'TranscribeGrpcClient',
]
