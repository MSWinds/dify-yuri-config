from services.errors.base import BaseServiceError


class AccountNotFoundError(BaseServiceError):
    pass


class AccountRegisterError(BaseServiceError):
    pass


# New error for whitelist validation
class AccountNotWhitelistError(BaseServiceError):
    pass


class AccountLoginError(BaseServiceError):
    pass


class AccountPasswordError(BaseServiceError):
    pass


class AccountNotLinkTenantError(BaseServiceError):
    pass


class CurrentPasswordIncorrectError(BaseServiceError):
    pass


class LinkAccountIntegrateError(BaseServiceError):
    pass


class TenantNotFoundError(BaseServiceError):
    pass


class AccountAlreadyInTenantError(BaseServiceError):
    pass


class InvalidActionError(BaseServiceError):
    pass


class CannotOperateSelfError(BaseServiceError):
    pass


class NoPermissionError(BaseServiceError):
    pass


class MemberNotInTenantError(BaseServiceError):
    pass


class RoleAlreadyAssignedError(BaseServiceError):
    pass
