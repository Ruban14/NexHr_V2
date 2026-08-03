"""Backward-compatible re-export."""

from apps.documents.services.document_service import DocumentService, EmployeeDocumentService

__all__ = ['DocumentService', 'EmployeeDocumentService']
