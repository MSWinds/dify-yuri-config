import sys
import os
import logging
import argparse
import socket
from dotenv import load_dotenv

# --- Environment Setup for Local Execution ---
# Must be done before importing Dify modules
script_dir = os.path.dirname(os.path.abspath(__file__))
docker_env_path = os.path.join(script_dir, '../docker/.env')

if os.path.exists(docker_env_path):
    # Load env vars from docker/.env if they aren't already set
    load_dotenv(docker_env_path)

# Patch DB_HOST if running locally (cannot resolve container names)
db_host = os.environ.get('DB_HOST')
if db_host == 'db_postgres':
    try:
        socket.gethostbyname('db_postgres')
    except socket.gaierror:
        print("⚠️  'db_postgres' not resolvable. Assuming LOCAL execution via 'uv'.")
        print("    -> Patching DB_HOST=localhost, REDIS_HOST=localhost")
        os.environ['DB_HOST'] = 'localhost'
        os.environ['REDIS_HOST'] = 'localhost'
        os.environ['CELERY_BROKER_URL'] = os.environ.get('CELERY_BROKER_URL', '').replace('redis:6379', 'localhost:6379')
        
        # Patch LOG_FILE to avoid trying to write to /app/logs on host
        log_file = os.environ.get('LOG_FILE', '')
        if log_file.startswith('/app/'):
            # Correct path replacement (lstrip is dangerous here)
            local_log_path = os.path.join(script_dir, '../api', log_file.replace('/app/', '', 1))
            # Ensure dir exists
            try:
                os.makedirs(os.path.dirname(local_log_path), exist_ok=True)
                os.environ['LOG_FILE'] = local_log_path
                print(f"    -> Patching LOG_FILE={local_log_path}")
            except Exception as e:
                print(f"    -> Failed to patch log path: {e}. Unsetting LOG_FILE.")
                del os.environ['LOG_FILE']

# Ensuring OPENDAL_FS_ROOT is set (required by Storage config)
if not os.environ.get('OPENDAL_FS_ROOT'):
    # Default to api/storage
    os.environ['OPENDAL_FS_ROOT'] = os.path.abspath(os.path.join(script_dir, '../api/storage'))

# Add api directory to path
sys.path.append(os.path.abspath(os.path.join(script_dir, '../api')))

# --- Imports ---
from app import create_app
from extensions.ext_database import db
from models.account import Account, TenantAccountJoin, Tenant, TenantAccountRole
from models.model import App, Conversation, Message, InstalledApp, RecommendedApp
from models.dataset import Dataset, Document, DocumentSegment, DatasetProcessRule
from models.provider import ProviderModelSetting
from models.tools import ApiToolProvider

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def delete_tenant_data(tenant_id):
    """
    删除指定 Tenant 下的所有业务数据
    """
    logger.info(f"    -> Cleaning up Tenant ID: {tenant_id}...")
    
    # 1. 删除 Apps 及相关
    apps = db.session.query(App).filter(App.tenant_id == tenant_id).all()
    for app in apps:
        # 这里还可以细化删除 conversation 等，但依赖 cascade
        db.session.query(Conversation).filter(Conversation.app_id == app.id).delete()
        db.session.query(InstalledApp).filter(InstalledApp.app_id == app.id).delete()
        db.session.delete(app)
    logger.info(f"       Deleted {len(apps)} Apps.")

    # 2. 删除知识库 (Datasets)
    datasets = db.session.query(Dataset).filter(Dataset.tenant_id == tenant_id).all()
    for ds in datasets:
        # 删除文档切片 (量大，使用 query delete)
        # 先找 documents
        doc_ids = [d.id for d in db.session.query(Document).filter(Document.dataset_id == ds.id).all()]
        if doc_ids:
            db.session.query(DocumentSegment).filter(DocumentSegment.document_id.in_(doc_ids)).delete(synchronize_session=False)
            db.session.query(Document).filter(Document.dataset_id == ds.id).delete(synchronize_session=False)
        
        db.session.delete(ds)
    logger.info(f"       Deleted {len(datasets)} Datasets.")

    # 3. 删除 Providers 配置
    db.session.query(ProviderModelSetting).filter(ProviderModelSetting.tenant_id == tenant_id).delete()
    db.session.query(ApiToolProvider).filter(ApiToolProvider.tenant_id == tenant_id).delete()

    # 4. 最后删除 Tenant 本身
    db.session.query(Tenant).filter(Tenant.id == tenant_id).delete()
    logger.info("       Tenant record deleted.")

def process_delete(emails, dry_run=True):
    for email in emails:
        print(f"\nProcessing User: {email}")
        account = db.session.query(Account).filter(Account.email == email).first()
        
        if not account:
            logger.warning(f"User {email} NOT FOUND. Skipping.")
            continue

        # 获取该用户关联的所有 Tenant
        joins = db.session.query(TenantAccountJoin).filter(TenantAccountJoin.account_id == account.id).all()
        
        tenants_to_delete = []
        tenants_to_leave = []

        for join in joins:
            tenant = db.session.query(Tenant).filter(Tenant.id == join.tenant_id).first()
            if not tenant:
                continue
            
            # 判断逻辑：如果是 Owner，就认为是个人创建的 Workspace，删除
            # 即便里面有其他人 (Admins/Members)，因为 Owner 只有一人，随 Owner 一起销毁是合理的清理逻辑
            member_count = db.session.query(TenantAccountJoin).filter(TenantAccountJoin.tenant_id == tenant.id).count()
            
            if join.role == TenantAccountRole.OWNER:
                tenants_to_delete.append((tenant, member_count))
            else:
                tenants_to_leave.append((tenant, join.role, member_count))

        print(f"  [Plan] for {account.name} ({account.id}):")
        if tenants_to_delete:
            print("    [DELETE FULLY] These Tenants (User is OWNER - Will delete Workspace):")
            for t, count in tenants_to_delete:
                print(f"      - {t.name} (ID: {t.id}, Members: {count})")
        
        if tenants_to_leave:
            print("    [LEAVE ONLY] These Tenants (User is NOT OWNER):")
            for t, role, count in tenants_to_leave:
                print(f"      - {t.name} (ID: {t.id}, Role: {role}, Members: {count})")

        if dry_run:
            print("  --- DRY RUN: No changes made ---")
            print("  Please check the above plan carefully. Tenants marked [DELETE FULLY] will be permanently removed.")
            continue

        # 执行删除
        # A. 删除关联的个人 Tenants
        for t, _ in tenants_to_delete:
             # 先删 Join 关系
            db.session.query(TenantAccountJoin).filter(TenantAccountJoin.tenant_id == t.id).delete()
            # 再删数据
            delete_tenant_data(t.id)

        # B. 退出公共 Tenants
        for t, _, _ in tenants_to_leave:
            db.session.query(TenantAccountJoin).filter(
                TenantAccountJoin.tenant_id == t.id, 
                TenantAccountJoin.account_id == account.id
            ).delete()
            logger.info(f"  Removed membership from {t.name}")

        # C. 删除 Account
        db.session.delete(account)
        db.session.commit()
        logger.info(f"SUCCESS: User {email} deleted.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Delete Dify users and their personal workspaces.")
    parser.add_argument("emails", nargs='+', help="List of email addresses to delete")
    parser.add_argument("--force", action="store_true", help="Execute deletion (default is dry-run)")
    
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        if not args.force:
            print("⚠️  RUNNING IN DRY-RUN MODE. Use --force to actually delete data.")
        
        process_delete(args.emails, dry_run=not args.force)
