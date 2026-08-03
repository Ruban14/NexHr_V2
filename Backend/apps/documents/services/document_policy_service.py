"""Document category, definition, and policy master operations."""

from __future__ import annotations


class DocumentPolicyService:
    """Document master-data API; delegates to MasterService implementations."""

    @classmethod
    def list_document_categories(cls, **kwargs):
        from apps.workforce.services.master_service import MasterService

        return MasterService.list_document_categories(**kwargs)

    @classmethod
    def create_document_category(cls, **kwargs):
        from apps.workforce.services.master_service import MasterService

        return MasterService.create_document_category(**kwargs)

    @classmethod
    def update_document_category(cls, **kwargs):
        from apps.workforce.services.master_service import MasterService

        return MasterService.update_document_category(**kwargs)

    @classmethod
    def list_document_definitions(cls, **kwargs):
        from apps.workforce.services.master_service import MasterService

        return MasterService.list_document_definitions(**kwargs)

    @classmethod
    def create_document_definition(cls, **kwargs):
        from apps.workforce.services.master_service import MasterService

        return MasterService.create_document_definition(**kwargs)

    @classmethod
    def update_document_definition(cls, **kwargs):
        from apps.workforce.services.master_service import MasterService

        return MasterService.update_document_definition(**kwargs)

    @classmethod
    def delete_document_definition(cls, **kwargs):
        from apps.workforce.services.master_service import MasterService

        return MasterService.delete_document_definition(**kwargs)

    @classmethod
    def list_document_policies(cls, **kwargs):
        from apps.workforce.services.master_service import MasterService

        return MasterService.list_document_policies(**kwargs)

    @classmethod
    def get_document_policy(cls, **kwargs):
        from apps.workforce.services.master_service import MasterService

        return MasterService.get_document_policy(**kwargs)

    @classmethod
    def create_document_policy(cls, **kwargs):
        from apps.workforce.services.master_service import MasterService

        return MasterService.create_document_policy(**kwargs)

    @classmethod
    def update_document_policy(cls, **kwargs):
        from apps.workforce.services.master_service import MasterService

        return MasterService.update_document_policy(**kwargs)

    @classmethod
    def delete_document_policy(cls, **kwargs):
        from apps.workforce.services.master_service import MasterService

        return MasterService.delete_document_policy(**kwargs)
