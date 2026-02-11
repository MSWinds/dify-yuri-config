from app import create_app
from services.account_service import AccountService

app = create_app()
with app.app_context():
    try:
        print("Testing authentication for kaijie.yu@cgu.edu...")
        user = AccountService.authenticate("kaijie.yu@cgu.edu", "password123")
        print(f"✅ Authentication SUCCESS! User ID: {user.id}")
    except Exception as e:
        print(f"❌ Authentication FAILED: {e}")
