import logging

from sqlalchemy import func

from events.tenant_event import tenant_was_created
from extensions.ext_database import db
from models.account import Account, Tenant, TenantAccountJoin
from services.account_service import AccountService, TenantService
from services.feature_service import FeatureService

logger = logging.getLogger(__name__)


@tenant_was_created.connect
def handle(sender, **kwargs):
    """
    Handle tenant creation event in Classroom Mode.
    
    Two scenarios:
    1. Student creates workspace → Add all existing teachers to it
    2. Teacher creates workspace → Add this teacher to all existing student workspaces
    
    Note: AccountService.load_user() calls db.session.close() which detaches
    all objects from the session. We must save tenant info before calling it
    and re-fetch the tenant afterward.
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
        
        # Save tenant info BEFORE calling load_user(), because load_user() 
        # calls db.session.close() which will detach the tenant object
        tenant_id = tenant.id
        tenant_name = tenant.name
        
        logger.info(
            "[Classroom Mode] Processing new tenant %s (%s). Teachers configured: %s",
            tenant_id,
            tenant_name,
            teachers_emails,
        )

        # Get the owner of the new tenant
        owner_join = db.session.query(TenantAccountJoin).filter_by(
            tenant_id=tenant_id, 
            role='owner'
        ).first()
        
        tenant_owner = None
        if owner_join:
            # WARNING: load_user() calls db.session.close(), which detaches all objects
            tenant_owner = AccountService.load_user(owner_join.account_id)
            
            # Re-fetch tenant from database since session was closed
            tenant = db.session.query(Tenant).get(tenant_id)
            if not tenant:
                logger.error("[Classroom Mode] Could not re-fetch tenant %s after load_user()", tenant_id)
                return
        
        is_teacher_tenant = tenant_owner and tenant_owner.email in teachers_emails
        
        if is_teacher_tenant:
            # Scenario 2: Teacher creates workspace
            # Add this teacher to all existing STUDENT workspaces
            logger.info(
                "[Classroom Mode] New tenant %s belongs to teacher %s. Adding to existing student workspaces...",
                tenant_id,
                tenant_owner.email,
            )
            
            # Get student whitelist
            students_str = system_features.classroom_student_whitelist
            if students_str:
                student_emails = [e.strip() for e in students_str.split(',') if e.strip()]
                
                for student_email in student_emails:
                    # Find student account
                    student_account = (
                        db.session.query(Account)
                        .filter(func.lower(Account.email) == student_email.lower())
                        .first()
                    )
                    if not student_account:
                        continue  # Student hasn't registered yet
                    
                    # Get all workspaces owned by this student
                    student_tenants = TenantService.get_join_tenants(student_account)
                    for student_tenant in student_tenants:
                        # Check if this student is the owner
                        student_owner_join = db.session.query(TenantAccountJoin).filter_by(
                            tenant_id=student_tenant.id,
                            role='owner'
                        ).first()
                        
                        if student_owner_join and student_owner_join.account_id == student_account.id:
                            # Add the new teacher to this student's workspace
                            if not TenantService.is_member(tenant_owner, student_tenant):
                                TenantService.create_tenant_member(student_tenant, tenant_owner, role='admin')
                                logger.info(
                                    "[Classroom Mode] Added new teacher %s to student workspace %s (%s)",
                                    tenant_owner.email,
                                    student_tenant.id,
                                    student_tenant.name,
                                )
        else:
            # Scenario 1: Student creates workspace
            # Add all existing teachers to this new student workspace
            logger.info("[Classroom Mode] New tenant %s belongs to student. Adding all existing teachers...", tenant_id)
            
            for email in teachers_emails:
                # Find teacher account
                account = db.session.query(Account).filter(func.lower(Account.email) == email.lower()).first()
                
                if not account:
                    logger.warning("[Classroom Mode] Teacher account not found: %s. Skipping.", email)
                    continue

                # Add teacher as admin to the student's workspace
                if not TenantService.is_member(account, tenant):
                    TenantService.create_tenant_member(tenant, account, role='admin')
                    logger.info("[Classroom Mode] Added teacher %s as Admin to student tenant %s", email, tenant_id)
                else:
                    logger.info("[Classroom Mode] Teacher %s is already a member of %s", email, tenant_id)

    except Exception:
        logger.exception("[Classroom Mode] Failed to add teachers to new tenant")
