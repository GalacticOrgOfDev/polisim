"""
Tests for API authentication (Phase 5, Sprint 5.1)
"""

import os
import pytest
import json
from datetime import datetime, timedelta, timezone

from api.rest_server import create_api_app
from api.models import User, APIKey, Base
from api.database import get_db_session, configure_engine, dispose_engine
from api.auth import create_jwt_token, decode_jwt_token, AuthError


@pytest.fixture(autouse=True)
def in_memory_db():
    """Configure isolated in-memory SQLite database for each test."""
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    engine = configure_engine(os.environ['DATABASE_URL'])
    Base.metadata.create_all(engine)
    try:
        yield
    finally:
        try:
            Base.metadata.drop_all(engine)
        except Exception:
            pass
        finally:
            dispose_engine()


@pytest.fixture
def app():
    """Create test Flask app."""
    app = create_api_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def db_session():
    """Create test database session with cleanup."""
    session = get_db_session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_user(db_session):
    """Create test user with unique credentials."""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    
    user = User(
        email=f"test_{unique_id}@example.com",
        username=f"testuser_{unique_id}",
        full_name="Test User",
        role="user",
        is_active=True,
        is_verified=True,
    )
    user.set_password("testpassword123")
    db_session.add(user)
    db_session.commit()
    return user


class TestJWTTokens:
    """Test JWT token creation and validation."""
    
    def test_create_jwt_token(self):
        """Test JWT token creation."""
        token = create_jwt_token(1, "test@example.com", "user")
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 20
    
    def test_decode_valid_token(self):
        """Test decoding valid JWT token."""
        token = create_jwt_token(1, "test@example.com", "user")
        payload = decode_jwt_token(token)
        
        assert payload['user_id'] == 1
        assert payload['email'] == "test@example.com"
        assert payload['role'] == "user"
        assert 'exp' in payload
        assert 'iat' in payload
    
    def test_decode_invalid_token(self):
        """Test decoding invalid JWT token."""
        with pytest.raises(AuthError) as exc_info:
            decode_jwt_token("invalid.token.here")
        assert exc_info.value.status_code == 401
    
    def test_expired_token(self):
        """Test expired JWT token."""
        # Create token with negative expiration (already expired)
        import jwt
        from api.auth import JWT_SECRET_KEY, JWT_ALGORITHM
        
        payload = {
            'user_id': 1,
            'email': 'test@example.com',
            'role': 'user',
            'exp': datetime.now(timezone.utc) - timedelta(hours=1),
            'iat': datetime.now(timezone.utc) - timedelta(hours=2),
        }
        expired_token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        
        with pytest.raises(AuthError) as exc_info:
            decode_jwt_token(expired_token)
        assert "expired" in exc_info.value.message.lower()


class TestUserAuthentication:
    """Test user registration and login."""
    
    def test_register_new_user(self, client):
        """Test user registration."""
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        
        response = client.post('/api/auth/register', json={
            'email': f'newuser_{unique_id}@example.com',
            'username': f'newuser_{unique_id}',
            'password': 'securepass123',
            'full_name': 'New User',
        })
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'token' in data
        assert f'newuser_{unique_id}@example.com' in data['user']['email']
        assert f'newuser_{unique_id}' in data['user']['username']
    
    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email."""
        response = client.post('/api/auth/register', json={
            'email': test_user.email,
            'username': 'differentuser',
            'password': 'password123',
        })
        
        assert response.status_code == 409
        data = json.loads(response.data)
        assert 'already exists' in data['error'].lower()
    
    def test_register_missing_fields(self, client):
        """Test registration with missing fields."""
        response = client.post('/api/auth/register', json={
            'email': 'test@example.com',
            # Missing username and password
        })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'missing' in data['error'].lower()
    
    def test_login_valid_credentials(self, client, test_user):
        """Test login with valid credentials."""
        response = client.post('/api/auth/login', json={
            'email': test_user.email,
            'password': 'testpassword123',
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'token' in data
        assert data['user']['email'] == test_user.email
    
    def test_login_invalid_password(self, client, test_user):
        """Test login with invalid password."""
        response = client.post('/api/auth/login', json={
            'email': test_user.email,
            'password': 'wrongpassword',
        })
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'invalid' in data['error'].lower()
    
    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user."""
        response = client.post('/api/auth/login', json={
            'email': 'nonexistent@example.com',
            'password': 'password123',
        })
        
        assert response.status_code == 401


class TestProtectedEndpoints:
    """Test protected endpoint access."""
    
    def test_access_protected_without_auth(self, client):
        """Test accessing protected endpoint without authentication."""
        response = client.get('/api/auth/me')
        assert response.status_code == 401
    
    def test_access_protected_with_valid_token(self, client, test_user):
        """Test accessing protected endpoint with valid token."""
        token = create_jwt_token(test_user.id, test_user.email, test_user.role)
        
        response = client.get('/api/auth/me', headers={
            'Authorization': f'Bearer {token}'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['user']['email'] == test_user.email
    
    def test_access_protected_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token."""
        response = client.get('/api/auth/me', headers={
            'Authorization': 'Bearer invalid.token.here'
        })
        
        assert response.status_code == 401


class TestAPIKeys:
    """Test API key functionality."""
    
    def test_create_api_key(self, client, test_user):
        """Test API key creation."""
        token = create_jwt_token(test_user.id, test_user.email, test_user.role)
        
        response = client.post('/api/auth/api-keys', 
            headers={'Authorization': f'Bearer {token}'},
            json={'name': 'Test API Key'}
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'api_key' in data
        assert data['api_key']['key'].startswith('ps_')
    
    def test_list_api_keys(self, client, test_user, db_session):
        """Test listing API keys."""
        # Create API key
        api_key = APIKey(
            user_id=test_user.id,
            key=APIKey.generate_key(),
            name='Test Key',
            prefix='ps_12345',
        )
        db_session.add(api_key)
        db_session.commit()
        
        token = create_jwt_token(test_user.id, test_user.email, test_user.role)
        
        response = client.get('/api/auth/api-keys',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['api_keys']) >= 1
    
    def test_authenticate_with_api_key(self, client, test_user, db_session):
        """Test authentication with API key."""
        # Create API key
        key_value = APIKey.generate_key()
        api_key = APIKey(
            user_id=test_user.id,
            key=key_value,
            name='Test Key',
            prefix=key_value[:8],
        )
        db_session.add(api_key)
        db_session.commit()
        
        # Use API key to access protected endpoint
        response = client.get('/api/auth/me',
            headers={'X-API-Key': key_value}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['user']['email'] == test_user.email


class TestUserModel:
    """Test User model methods."""
    
    def test_set_password(self):
        """Test password hashing."""
        user = User(email="test@example.com", username="test")
        user.set_password("mypassword")
        
        assert user.password_hash is not None
        assert user.password_hash != "mypassword"
        assert len(user.password_hash) > 20
    
    def test_check_password_valid(self):
        """Test password verification."""
        user = User(email="test@example.com", username="test")
        user.set_password("mypassword")
        
        assert user.check_password("mypassword") is True
    
    def test_check_password_invalid(self):
        """Test password verification with wrong password."""
        user = User(email="test@example.com", username="test")
        user.set_password("mypassword")
        
        assert user.check_password("wrongpassword") is False
    
    def test_to_dict(self):
        """Test user serialization to dictionary."""
        user = User(
            id=1,
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            role="user",
        )
        
        data = user.to_dict()
        assert data['id'] == 1
        assert data['email'] == "test@example.com"
        assert data['username'] == "testuser"
        assert 'password_hash' not in data


class TestAPIKeyModel:
    """Test APIKey model methods."""
    
    def test_generate_key(self):
        """Test API key generation."""
        key = APIKey.generate_key()
        
        assert key.startswith('ps_')
        assert len(key) > 20
    
    def test_to_dict_without_full_key(self):
        """Test API key serialization without full key."""
        api_key = APIKey(
            id=1,
            user_id=1,
            key='ps_testkey123456789',
            name='Test Key',
            prefix='ps_testk',
        )
        
        data = api_key.to_dict(include_full_key=False)
        assert data['prefix'] == 'ps_testk'
        assert data['key'] == 'ps_testk...'
    
    def test_to_dict_with_full_key(self):
        """Test API key serialization with full key."""
        api_key = APIKey(
            id=1,
            user_id=1,
            key='ps_testkey123456789',
            name='Test Key',
            prefix='ps_testk',
        )
        
        data = api_key.to_dict(include_full_key=True)
        assert data['key'] == 'ps_testkey123456789'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
