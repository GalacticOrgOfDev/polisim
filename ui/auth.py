"""
Streamlit Authentication Module
Handles user authentication, session management, and protected pages.

Features:
- Login/registration forms
- JWT token management
- Session state persistence
- Protected page decorator
- User profile management
"""

import streamlit as st
import requests
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class StreamlitAuth:
    """Streamlit authentication manager."""
    
    # API configuration
    API_BASE = "http://localhost:5000"
    
    # Session state keys
    SESSION_TOKEN = "jwt_token"
    SESSION_USER = "user"
    SESSION_LOGIN_TIME = "login_time"
    SESSION_AUTH_MODE = "auth_mode"  # 'development' or 'production'
    SESSION_AUTH_NOTICE = "auth_notice"

    @staticmethod
    def _set_auth_notice(message: Optional[str]):
        st.session_state[StreamlitAuth.SESSION_AUTH_NOTICE] = message

    @staticmethod
    def clear_auth_notice():
        StreamlitAuth._set_auth_notice(None)
    
    @staticmethod
    def initialize():
        """Initialize authentication session state."""
        # Check if auth mode is set
        if StreamlitAuth.SESSION_AUTH_MODE not in st.session_state:
            st.session_state[StreamlitAuth.SESSION_AUTH_MODE] = "development"
        
        # Initialize auth state
        if StreamlitAuth.SESSION_TOKEN not in st.session_state:
            st.session_state[StreamlitAuth.SESSION_TOKEN] = None
        
        if StreamlitAuth.SESSION_USER not in st.session_state:
            st.session_state[StreamlitAuth.SESSION_USER] = None
        
        if StreamlitAuth.SESSION_LOGIN_TIME not in st.session_state:
            st.session_state[StreamlitAuth.SESSION_LOGIN_TIME] = None

        if StreamlitAuth.SESSION_AUTH_NOTICE not in st.session_state:
            st.session_state[StreamlitAuth.SESSION_AUTH_NOTICE] = None
    
    @staticmethod
    def is_authenticated() -> bool:
        """Check if user is currently authenticated."""
        StreamlitAuth.initialize()
        
        # In development mode, always authenticated
        if st.session_state.get(StreamlitAuth.SESSION_AUTH_MODE) == "development":
            StreamlitAuth.clear_auth_notice()
            return True
        
        # Check if token exists and is not expired
        token = st.session_state.get(StreamlitAuth.SESSION_TOKEN)
        login_time = st.session_state.get(StreamlitAuth.SESSION_LOGIN_TIME)
        
        if not token or not login_time:
            return False
        
        # Check if token is expired (24 hours)
        if datetime.now() - login_time > timedelta(hours=24):
            StreamlitAuth.logout(reason="Your session expired. Please sign in again.")
            return False
        
        return True
    
    @staticmethod
    def require_auth() -> bool:
        """
        Require authentication to access current page.
        Returns True if authenticated, otherwise shows login page and stops execution.
        """
        if not StreamlitAuth.is_authenticated():
            StreamlitAuth.show_auth_page()
            st.stop()
        return True
    
    @staticmethod
    def show_auth_page():
        """Display authentication page with login and registration."""
        st.title("🔐 PoliSim Authentication")

        notice = st.session_state.get(StreamlitAuth.SESSION_AUTH_NOTICE)
        if notice:
            st.warning(notice)
        
        # Development mode toggle
        with st.expander("⚙️ Development Settings", expanded=False):
            auth_mode = st.radio(
                "Authentication Mode",
                options=["development", "production"],
                index=0 if st.session_state.get(StreamlitAuth.SESSION_AUTH_MODE) == "development" else 1,
                help="Development mode bypasses authentication for local testing."
            )
            if st.button("Apply Mode"):
                st.session_state[StreamlitAuth.SESSION_AUTH_MODE] = auth_mode
                st.rerun()
        
        # If in development mode, show skip button
        if st.session_state.get(StreamlitAuth.SESSION_AUTH_MODE) == "development":
            st.info("📝 Development mode is enabled. Authentication is optional.")
            if st.button("Continue without login", type="primary"):
                st.rerun()
            st.divider()
        
        # Tab selection
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            StreamlitAuth._show_login_form()
        
        with tab2:
            StreamlitAuth._show_registration_form()
    
    @staticmethod
    def _show_login_form():
        """Display login form."""
        st.subheader("Login to Your Account")
        
        with st.form("login_form"):
            email = st.text_input(
                "Email",
                placeholder="your.email@example.com",
                key="login_email"
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_password"
            )
            remember_me = st.checkbox("Remember me", value=True)
            
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("Login", type="primary", use_container_width=True)
            with col2:
                forgot = st.form_submit_button("Forgot Password?", use_container_width=True)
            
            if submit:
                if not email or not password:
                    st.error("⚠️ Please enter both email and password.")
                else:
                    with st.spinner("Authenticating..."):
                        success, result = StreamlitAuth._authenticate(email, password)
                        
                        if success:
                            st.success(f"✓ Welcome back, {result['user']['username']}!")
                            st.balloons()
                            StreamlitAuth.clear_auth_notice()
                            
                            # Wait a moment before rerunning
                            import time
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ {result}")
            
            if forgot:
                st.info("🔗 Password reset functionality coming soon. Please contact support.")
    
    @staticmethod
    def _show_registration_form():
        """Display registration form."""
        st.subheader("Create New Account")
        
        with st.form("register_form"):
            email = st.text_input(
                "Email *",
                placeholder="your.email@example.com",
                key="register_email"
            )
            username = st.text_input(
                "Username *",
                placeholder="Choose a username",
                key="register_username"
            )
            full_name = st.text_input(
                "Full Name",
                placeholder="John Doe (optional)",
                key="register_full_name"
            )
            organization = st.text_input(
                "Organization",
                placeholder="Your organization (optional)",
                key="register_organization"
            )
            password = st.text_input(
                "Password *",
                type="password",
                placeholder="Choose a strong password",
                key="register_password"
            )
            password_confirm = st.text_input(
                "Confirm Password *",
                type="password",
                placeholder="Re-enter your password",
                key="register_password_confirm"
            )
            
            agree_terms = st.checkbox(
                "I agree to the Terms of Service and Privacy Policy",
                key="register_agree"
            )
            
            submit = st.form_submit_button("Create Account", type="primary", use_container_width=True)
            
            if submit:
                # Validation
                if not email or not username or not password or not password_confirm:
                    st.error("⚠️ Please fill in all required fields (*).")
                elif password != password_confirm:
                    st.error("⚠️ Passwords do not match.")
                elif len(password) < 8:
                    st.error("⚠️ Password must be at least 8 characters long.")
                elif not agree_terms:
                    st.error("⚠️ You must agree to the Terms of Service.")
                else:
                    with st.spinner("Creating account..."):
                        success, result = StreamlitAuth._register(
                            email=email,
                            username=username,
                            password=password,
                            full_name=full_name or None,
                            organization=organization or None
                        )
                        
                        if success:
                            st.success(f"✓ Account created successfully! Welcome, {username}!")
                            st.balloons()
                            StreamlitAuth.clear_auth_notice()
                            
                            # Wait a moment before rerunning
                            import time
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ {result}")
    
    @staticmethod
    def _authenticate(email: str, password: str) -> tuple[bool, Any]:
        """
        Authenticate user with API.
        Returns (success: bool, result: dict or error_message: str)
        """
        try:
            response = requests.post(
                f"{StreamlitAuth.API_BASE}/api/auth/login",
                json={"email": email, "password": password},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Store authentication data
                st.session_state[StreamlitAuth.SESSION_TOKEN] = data["token"]
                st.session_state[StreamlitAuth.SESSION_USER] = data["user"]
                st.session_state[StreamlitAuth.SESSION_LOGIN_TIME] = datetime.now()
                StreamlitAuth.clear_auth_notice()
                
                return True, data
            else:
                error_data = response.json()
                return False, error_data.get("error", "Authentication failed")
                
        except requests.exceptions.ConnectionError:
            return False, "Cannot connect to authentication server. Please ensure the API is running."
        except requests.exceptions.Timeout:
            return False, "Authentication request timed out. Please try again."
        except Exception as e:
            return False, f"Authentication error: {str(e)}"
    
    @staticmethod
    def _register(email: str, username: str, password: str, 
                  full_name: Optional[str] = None,
                  organization: Optional[str] = None) -> tuple[bool, Any]:
        """
        Register new user with API.
        Returns (success: bool, result: dict or error_message: str)
        """
        try:
            response = requests.post(
                f"{StreamlitAuth.API_BASE}/api/auth/register",
                json={
                    "email": email,
                    "username": username,
                    "password": password,
                    "full_name": full_name,
                    "organization": organization
                },
                timeout=10
            )
            
            if response.status_code == 201:
                data = response.json()
                
                # Store authentication data
                st.session_state[StreamlitAuth.SESSION_TOKEN] = data["token"]
                st.session_state[StreamlitAuth.SESSION_USER] = data["user"]
                st.session_state[StreamlitAuth.SESSION_LOGIN_TIME] = datetime.now()
                StreamlitAuth.clear_auth_notice()
                
                return True, data
            else:
                error_data = response.json()
                return False, error_data.get("error", "Registration failed")
                
        except requests.exceptions.ConnectionError:
            return False, "Cannot connect to authentication server. Please ensure the API is running."
        except requests.exceptions.Timeout:
            return False, "Registration request timed out. Please try again."
        except Exception as e:
            return False, f"Registration error: {str(e)}"
    
    @staticmethod
    def logout(reason: Optional[str] = None):
        """Logout current user and clear session."""
        StreamlitAuth._set_auth_notice(reason)
        st.session_state[StreamlitAuth.SESSION_TOKEN] = None
        st.session_state[StreamlitAuth.SESSION_USER] = None
        st.session_state[StreamlitAuth.SESSION_LOGIN_TIME] = None
        st.rerun()
    
    @staticmethod
    def get_current_user() -> Optional[Dict[str, Any]]:
        """Get current authenticated user."""
        return st.session_state.get(StreamlitAuth.SESSION_USER)
    
    @staticmethod
    def get_auth_header() -> Dict[str, str]:
        """Get authorization header for API requests."""
        token = st.session_state.get(StreamlitAuth.SESSION_TOKEN)
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}
    
    @staticmethod
    def show_user_widget():
        """Display compact user widget in sidebar."""
        StreamlitAuth.initialize()
        
        if StreamlitAuth.is_authenticated():
            user = StreamlitAuth.get_current_user()
            
            if user:
                with st.sidebar:
                    st.divider()
                    st.caption("Signed in")
                    st.markdown(StreamlitAuth.render_user_summary(user))
                    if st.button("🚪 Logout", help="Logout", key="logout_btn", use_container_width=True):
                        StreamlitAuth.logout(reason="Signed out.")
        else:
            with st.sidebar:
                st.divider()
                if st.button("🔐 Login", use_container_width=True):
                    st.session_state['show_auth'] = True
                    st.rerun()

    @staticmethod
    def render_user_summary(user: Dict[str, Any]) -> str:
        username = user.get('username', 'User')
        email = user.get('email', 'Email not available')
        role = user.get('role', 'user').title()
        return f"**{username}** ({role})\n{email}"


def show_user_profile_page():
    """Display user profile management page."""
    StreamlitAuth.require_auth()
    
    st.title("👤 User Profile")
    
    user = StreamlitAuth.get_current_user()
    
    if not user:
        st.warning("⚠️ User information not available.")
        return

    st.info(StreamlitAuth.render_user_summary(user))
    if st.button("🚪 Logout", key="profile_logout", use_container_width=True):
        StreamlitAuth.logout(reason="Signed out.")
    
    # User info section
    st.subheader("Account Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("Username", value=user.get('username', ''), disabled=True)
        st.text_input("Email", value=user.get('email', ''), disabled=True)
        st.text_input("Full Name", value=user.get('full_name', '') or 'Not set', disabled=True)
    
    with col2:
        st.text_input("Organization", value=user.get('organization', '') or 'Not set', disabled=True)
        st.text_input("Role", value=user.get('role', 'user').title(), disabled=True)
        
        # Account status
        is_active = user.get('is_active', False)
        is_verified = user.get('is_verified', False)
        
        status_text = "✓ Active" if is_active else "⚠️ Inactive"
        if not is_verified:
            status_text += " (Unverified)"
        st.text_input("Status", value=status_text, disabled=True)
    
    st.divider()
    
    # Edit profile section
    st.subheader("✏️ Edit Profile")
    
    with st.form("edit_profile_form"):
        new_full_name = st.text_input("Full Name", value=user.get('full_name', '') or '')
        new_organization = st.text_input("Organization", value=user.get('organization', '') or '')
        
        submit = st.form_submit_button("Update Profile", type="primary")
        
        if submit:
            st.info("🔧 Profile update functionality coming soon!")
    
    st.divider()
    
    # Change password section
    st.subheader("🔒 Change Password")
    
    with st.form("change_password_form"):
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        
        submit = st.form_submit_button("Change Password", type="primary")
        
        if submit:
            if new_password != confirm_password:
                st.error("⚠️ Passwords do not match.")
            elif len(new_password) < 8:
                st.error("⚠️ Password must be at least 8 characters long.")
            else:
                st.info("🔧 Password change functionality coming soon!")
    
    st.divider()
    
    # Account statistics
    st.subheader("📊 Account Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Policies Created", "0")  # TODO: Fetch from database
    
    with col2:
        st.metric("Simulations Run", "0")  # TODO: Fetch from database
    
    with col3:
        st.metric("Reports Generated", "0")  # TODO: Fetch from database
    
    # Member since
    created_at = user.get('created_at')
    if created_at:
        st.caption(f"Member since: {created_at}")
    
    st.divider()
    
    # Danger zone
    with st.expander("⚠️ Danger Zone", expanded=False):
        st.warning("**Warning:** The actions below are permanent and cannot be undone.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Delete All Data", type="secondary"):
                st.error("This will delete all your policies, simulations, and reports.")
                st.info("🔧 Data deletion coming soon!")
        
        with col2:
            if st.button("❌ Delete Account", type="secondary"):
                st.error("This will permanently delete your account.")
                st.info("🔧 Account deletion coming soon!")
