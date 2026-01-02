"""
Role-Based Access Control (RBAC) System

Phase 6.2.4: Implements role-based access control with:
- Role definitions and permissions
- Endpoint protection decorators
- Permission validation
- Role hierarchy
"""

import logging
from typing import Callable, List, Optional, Set, Dict, Any
from functools import wraps
from enum import Enum

from flask import request, jsonify

logger = logging.getLogger(__name__)


class Role(Enum):
    """User roles in the system."""
    ADMIN = "admin"
    EXPERT_REVIEWER = "expert_reviewer"
    USER = "user"
    PUBLIC = "public"


class Permission(Enum):
    """Permissions in the system."""
    # Simulation permissions
    CREATE_SIMULATION = "create:simulation"
    READ_SIMULATION = "read:simulation"
    UPDATE_SIMULATION = "update:simulation"
    DELETE_SIMULATION = "delete:simulation"
    RUN_SIMULATION = "run:simulation"
    
    # Scenario permissions
    CREATE_SCENARIO = "create:scenario"
    READ_SCENARIO = "read:scenario"
    UPDATE_SCENARIO = "update:scenario"
    DELETE_SCENARIO = "delete:scenario"
    
    # Admin permissions
    MANAGE_USERS = "manage:users"
    MANAGE_ROLES = "manage:roles"
    VIEW_AUDIT_LOG = "view:audit_log"
    MANAGE_SYSTEM = "manage:system"
    VIEW_ANALYTICS = "view:analytics"
    
    # Data permissions
    EXPORT_DATA = "export:data"
    IMPORT_DATA = "import:data"
    ACCESS_REAL_DATA = "access:real_data"


# Role to permissions mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        # Admin has all permissions
        Permission.CREATE_SIMULATION,
        Permission.READ_SIMULATION,
        Permission.UPDATE_SIMULATION,
        Permission.DELETE_SIMULATION,
        Permission.RUN_SIMULATION,
        Permission.CREATE_SCENARIO,
        Permission.READ_SCENARIO,
        Permission.UPDATE_SCENARIO,
        Permission.DELETE_SCENARIO,
        Permission.MANAGE_USERS,
        Permission.MANAGE_ROLES,
        Permission.VIEW_AUDIT_LOG,
        Permission.MANAGE_SYSTEM,
        Permission.VIEW_ANALYTICS,
        Permission.EXPORT_DATA,
        Permission.IMPORT_DATA,
        Permission.ACCESS_REAL_DATA,
    },
    Role.EXPERT_REVIEWER: {
        # Expert reviewers can read and analyze but not modify
        Permission.READ_SIMULATION,
        Permission.READ_SCENARIO,
        Permission.VIEW_ANALYTICS,
        Permission.EXPORT_DATA,
        Permission.ACCESS_REAL_DATA,
    },
    Role.USER: {
        # Regular users can create and manage their own content
        Permission.CREATE_SIMULATION,
        Permission.READ_SIMULATION,
        Permission.UPDATE_SIMULATION,
        Permission.DELETE_SIMULATION,
        Permission.RUN_SIMULATION,
        Permission.CREATE_SCENARIO,
        Permission.READ_SCENARIO,
        Permission.UPDATE_SCENARIO,
        Permission.DELETE_SCENARIO,
        Permission.EXPORT_DATA,
        Permission.ACCESS_REAL_DATA,
    },
    Role.PUBLIC: {
        # Public users have limited read access
        Permission.READ_SIMULATION,
        Permission.READ_SCENARIO,
        Permission.RUN_SIMULATION,
    },
}


class RBACManager:
    """Manages role-based access control."""
    
    def __init__(self):
        """Initialize RBAC manager."""
        self.role_permissions = ROLE_PERMISSIONS
        logger.info("RBAC manager initialized with 4 roles and 17 permissions")
    
    def get_role_permissions(self, role: Role) -> Set[Permission]:
        """Get all permissions for a role."""
        return self.role_permissions.get(role, set())
    
    def has_permission(self, user_roles: List[str], permission: Permission) -> bool:
        """
        Check if user has permission based on their roles.
        
        Args:
            user_roles: List of user role names
            permission: Permission to check
            
        Returns:
            True if user has permission
        """
        for role_name in user_roles:
            try:
                role = Role(role_name)
                if permission in self.get_role_permissions(role):
                    return True
            except ValueError:
                logger.warning(f"Unknown role: {role_name}")
        
        return False
    
    def get_user_permissions(self, user_roles: List[str]) -> Set[str]:
        """
        Get all permissions for a user based on their roles.
        
        Args:
            user_roles: List of user role names
            
        Returns:
            Set of permission strings
        """
        permissions = set()
        
        for role_name in user_roles:
            try:
                role = Role(role_name)
                role_perms = self.get_role_permissions(role)
                permissions.update(perm.value for perm in role_perms)
            except ValueError:
                logger.warning(f"Unknown role: {role_name}")
        
        return permissions
    
    def validate_role(self, role_name: str) -> bool:
        """Validate if role exists."""
        try:
            Role(role_name)
            return True
        except ValueError:
            return False


# Global RBAC manager
_rbac_manager: Optional[RBACManager] = None


def get_rbac_manager() -> RBACManager:
    """Get or create global RBAC manager."""
    global _rbac_manager
    if _rbac_manager is None:
        _rbac_manager = RBACManager()
    return _rbac_manager


def require_permission(*permissions: Permission) -> Callable:
    """
    Decorator to require specific permissions on an endpoint.
    
    Usage:
        @app.route('/api/admin/users')
        @require_permission(Permission.MANAGE_USERS)
        def manage_users():
            return jsonify({'users': []})
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get user roles from request context
            user_roles = request.headers.get('X-User-Roles', '').split(',')
            user_roles = [role.strip() for role in user_roles if role.strip()]
            
            if not user_roles:
                # Try to get from JWT token (if available)
                try:
                    from flask import g
                    if hasattr(g, 'user_roles'):
                        user_roles = g.user_roles
                except:
                    pass
            
            # Check permissions
            rbac = get_rbac_manager()
            has_access = any(rbac.has_permission(user_roles, perm) for perm in permissions)
            
            if not has_access:
                logger.warning(f"Access denied for roles {user_roles} to resource {func.__name__}")
                return jsonify({
                    'error': 'Insufficient permissions',
                    'required_permissions': [p.value for p in permissions],
                    'status': 'error'
                }), 403
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_role(*roles: Role) -> Callable:
    """
    Decorator to require specific roles on an endpoint.
    
    Usage:
        @app.route('/api/admin/dashboard')
        @require_role(Role.ADMIN)
        def admin_dashboard():
            return jsonify({'data': {}})
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get user roles from request context
            user_roles = request.headers.get('X-User-Roles', '').split(',')
            user_roles = [role.strip() for role in user_roles if role.strip()]
            
            if not user_roles:
                # Try to get from JWT token (if available)
                try:
                    from flask import g
                    if hasattr(g, 'user_roles'):
                        user_roles = g.user_roles
                except:
                    pass
            
            # Check roles
            required_role_names = {role.value for role in roles}
            user_role_names = set(user_roles)
            
            if not user_role_names.intersection(required_role_names):
                logger.warning(f"Access denied for roles {user_roles} to resource {func.__name__}")
                return jsonify({
                    'error': 'Insufficient role',
                    'required_roles': list(required_role_names),
                    'status': 'error'
                }), 403
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def get_current_user_roles() -> List[str]:
    """
    Get current user roles from request context.
    
    Returns:
        List of user role names
    """
    # Try to get from Flask g object (set by middleware)
    try:
        from flask import g
        if hasattr(g, 'user_roles'):
            return g.user_roles
    except:
        pass
    
    # Try to get from headers
    user_roles = request.headers.get('X-User-Roles', '')
    return [role.strip() for role in user_roles.split(',') if role.strip()]


def get_current_user_permissions() -> Set[str]:
    """
    Get current user permissions.
    
    Returns:
        Set of permission strings
    """
    rbac = get_rbac_manager()
    user_roles = get_current_user_roles()
    return rbac.get_user_permissions(user_roles)


def user_has_permission(permission: Permission) -> bool:
    """
    Check if current user has a specific permission.
    
    Args:
        permission: Permission to check
        
    Returns:
        True if user has permission
    """
    rbac = get_rbac_manager()
    user_roles = get_current_user_roles()
    return rbac.has_permission(user_roles, permission)


def user_has_role(role: Role) -> bool:
    """
    Check if current user has a specific role.
    
    Args:
        role: Role to check
        
    Returns:
        True if user has role
    """
    user_roles = get_current_user_roles()
    return role.value in user_roles
