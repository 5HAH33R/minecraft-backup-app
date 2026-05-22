from app.config import get_settings
from app.dependencies import get_current_user
from app.database import SessionLocal
from app.models.user import User
from jose import jwt
from datetime import datetime, timedelta
from app.utils.encryption import encrypt_credentials
import json

settings = get_settings()

# Create a test user
db = SessionLocal()

# Clean up if exists
test_user = db.query(User).filter(User.email == "test@jwt.com").first()
if test_user:
    db.delete(test_user)
    db.commit()

# Create test credentials
credentials = json.dumps({"token": "test"})
encrypted = encrypt_credentials(credentials)

# Create user
user = User(
    email="test@jwt.com",
    google_id="test_jwt_123",
    display_name="JWT Test",
    google_credentials=encrypted
)
db.add(user)
db.commit()
db.refresh(user)

print(f"Created test user with ID: {user.id}")

# Create JWT token
data = {"sub": user.id}
expire = datetime.utcnow() + timedelta(minutes=30)
data.update({"exp": expire})

token = jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

print(f"\nGenerated JWT token:\n{token}\n")

# Try to decode it
try:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    print(f"✅ Token decoded successfully!")
    print(f"Payload: {payload}")
    print(f"User ID from token: {payload.get('sub')}")
    
    # Try to get user
    found_user = db.query(User).filter(User.id == payload.get('sub')).first()
    if found_user:
        print(f"✅ User found: {found_user.email}")
    else:
        print(f"❌ User not found!")
        
except Exception as e:
    print(f"❌ Token decode failed: {e}")

# Cleanup
db.delete(user)
db.commit()
db.close()

print("\n✅ JWT test complete!")