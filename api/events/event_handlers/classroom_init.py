import logging
from events.tenant_event import tenant_was_created
from extensions.ext_database import db
from models.account import TenantAccountJoin
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
        
        logger.info(f"[Classroom Mode] Processing new tenant {tenant.id} ({tenant.name}). Teachers configured: {teachers_emails}")

        # Get the owner of the new tenant
        owner_join = db.session.query(TenantAccountJoin).filter_by(
            tenant_id=tenant.id, 
            role='owner'
        ).first()
        
        tenant_owner = None
        if owner_join:
            tenant_owner = AccountService.get_account_by_id(owner_join.account_id)
        
        is_teacher_tenant = tenant_owner and tenant_owner.email in teachers_emails
        
        if is_teacher_tenant:
            # Scenario 2: Teacher creates workspace
            # Add this teacher to all existing STUDENT workspaces
            logger.info(f"[Classroom Mode] New tenant {tenant.id} belongs to teacher {tenant_owner.email}. Adding to existing student workspaces...")
            
            # Get student whitelist
            students_str = system_features.classroom_student_whitelist
            if students_str:
                student_emails = [e.strip() for e in students_str.split(',') if e.strip()]
                
                for student_email in student_emails:
                    # Find student account
                    student_account = AccountService.get_user_through_email(student_email)
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
                                logger.info(f"[Classroom Mode] Added new teacher {tenant_owner.email} to student workspace {student_tenant.id} ({student_tenant.name})")
        else:
            # Scenario 1: Student creates workspace
            # Add all existing teachers to this new student workspace
            logger.info(f"[Classroom Mode] New tenant {tenant.id} belongs to student. Adding all existing teachers...")
            
            for email in teachers_emails:
                # Find teacher account
                account = AccountService.get_user_through_email(email)
                
                if not account:
                    logger.warning(f"[Classroom Mode] Teacher account not found: {email}. Skipping.")
                    continue

                # Add teacher as admin to the student's workspace
                if not TenantService.is_member(account, tenant):
                    TenantService.create_tenant_member(tenant, account, role='admin')
                    logger.info(f"[Classroom Mode] Added teacher {email} as Admin to student tenant {tenant.id}")
                else:
                    logger.info(f"[Classroom Mode] Teacher {email} is already a member of {tenant.id}")

    except Exception as e:
        logger.exception(f"[Classroom Mode] Failed to add teachers to new tenant: {e}")
