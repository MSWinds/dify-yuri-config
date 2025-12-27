import logging
from events.tenant_event import tenant_was_created
from services.account_service import AccountService, TenantService
from services.feature_service import FeatureService

logger = logging.getLogger(__name__)

@tenant_was_created.connect
def handle(sender, **kwargs):
    """
    Handle tenant creation event in Classroom Mode.
    Automatically adds defined teachers as admins to the new tenant.
    """
    try:
        tenant = sender
        system_features = FeatureService.get_system_features()
        
        # Check if Classroom Mode is enabled
        if not system_features.classroom_mode:
            return

        teachers_str = system_features.classroom_teachers
        if not teachers_str:
            logger.warning("Classroom Mode enabled but no teachers configured.")
            return

        teachers_emails = [e.strip() for e in teachers_str.split(',') if e.strip()]
        
        logger.info(f"[Classroom Mode] Processing new tenant {tenant.id} ({tenant.name}). Adding teachers: {teachers_emails}")

        for email in teachers_emails:
            # Find teacher account
            account = AccountService.get_user_through_email(email)
            
            if not account:
                logger.warning(f"[Classroom Mode] Teacher account not found: {email}. Skipping.")
                continue

            # Add teacher as admin
            # careful: check if already member to avoid duplicate constraint error
            if not TenantService.is_member(account, tenant):
                TenantService.create_tenant_member(tenant, account, role='admin')
                logger.info(f"[Classroom Mode] Added {email} as Admin to tenant {tenant.id}")
            else:
                # If already member (e.g. self-created), ensure role is admin?
                # For now just skip to be safe.
                logger.info(f"[Classroom Mode] {email} is already a member of {tenant.id}")

    except Exception as e:
        logger.exception(f"[Classroom Mode] Failed to add teachers to new tenant: {e}")
