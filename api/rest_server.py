"""
REST API Server for PoliSim
Provides HTTP endpoints for policy analysis and fiscal projections.

Features:
- Policy simulation endpoints
- Real data access
- Report generation
- Monte Carlo analysis
- Scenario comparison
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pathlib import Path

try:
    from flask import Flask, request, jsonify, send_file
    from flask_cors import CORS
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False

from pydantic import ValidationError

from api.config_manager import get_config
from core.policy_builder import CustomPolicy, PolicyLibrary
from core.monte_carlo_scenarios import MonteCarloPolicySimulator, PolicySensitivityAnalyzer, StressTestAnalyzer
from core.policy_enhancements import PolicyRecommendationEngine, PolicyImpactCalculator, InteractiveScenarioExplorer, FiscalGoal
from core.data_loader import load_real_data
from core.report_generator import ComprehensiveReportBuilder, ReportMetadata
import pandas as pd

# Authentication imports (Phase 5)
try:
    from api.models import User, APIKey, UserPreferences
    from api.auth import (
        create_jwt_token, authenticate_user, authenticate_api_key,
        require_auth, require_rate_limit, AuthError
    )
    from api.database import init_database, get_db_session
    HAS_AUTH = True
except ImportError:
    HAS_AUTH = False

# Validation models (Slice 5.7)
try:
    from api.validation_models import (
        SimulateRequest, ScenariosListRequest, IngestionHealthRequest,
        SimulateResponse, ScenariosListResponse, IngestionHealthResponse,
        SimulationResults, SensitivityParameter, SensitivityAnalysis,
        SimulationMetadata, ScenarioListItem, PaginationInfo, ScenariosListMetadata,
        IngestionInfo, ValidationInfo, IngestionMetrics, HistoryEntry,
        IngestionHealthMetadata, ErrorResponse, ErrorCode, FieldError,
        create_error_response
    )
    HAS_VALIDATION = True
except ImportError:
    HAS_VALIDATION = False

# V1 middleware (Slice 5.7)
try:
    from api.v1_middleware import (
        get_api_config, before_v1_request, after_v1_request,
        require_v1_auth, init_rate_limiter, apply_rate_limit
    )
    HAS_V1_MIDDLEWARE = True
except ImportError:
    HAS_V1_MIDDLEWARE = False


class APIError(Exception):
    """Custom API error."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code


def _get_cors_origins() -> list:
    """
    Get list of allowed CORS origins from environment configuration.
    
    Phase 6.2 Security Hardening: Implement whitelist-based CORS
    instead of allowing all origins.
    """
    config = get_config()
    return config.api.get_cors_origins()


def create_api_app() -> "Flask":
    """Create and configure Flask application."""
    if not HAS_FLASK:
        raise ImportError("Flask and flask-cors required. Install with: pip install flask flask-cors")
    
    app = Flask(__name__)
    
    # Configure CORS (6.2.2 - Security Hardening)
    # Define allowed origins for CORS - restrict to trusted domains
    cors_config = {
        "origins": _get_cors_origins(),
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        "allow_headers": ["Content-Type", "Authorization", "X-API-Key"],
        "expose_headers": ["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
        "supports_credentials": True,
        "max_age": 3600,  # Cache preflight for 1 hour
    }
    CORS(app, resources={r"/api/*": cors_config})
    
    # Initialize database (Phase 5)
    if HAS_AUTH:
        init_database()
    
    # Initialize v1 middleware (Slice 5.7) and configuration
    if HAS_V1_MIDDLEWARE:
        config_mgr = get_config()
        init_rate_limiter(
            config_mgr.api.rate_limit_per_minute,
            config_mgr.api.rate_limit_burst
        )
        app.before_request(before_v1_request)
        app.after_request(after_v1_request)
    
    # Error handler
    @app.errorhandler(APIError)
    def handle_api_error(error):
        response = jsonify({
            "error": error.message,
            "status": "error"
        })
        response.status_code = error.status_code
        return response
    
    # Auth error handler (Phase 5)
    if HAS_AUTH:
        @app.errorhandler(AuthError)
        def handle_auth_error(error):
            response = jsonify({
                "error": error.message,
                "status": "error"
            })
            response.status_code = error.status_code
            return response
    
    # Security headers handler (Phase 6.2 - Security Hardening)
    @app.after_request
    def apply_security_headers(response):
        """Apply security headers to all responses."""
        # Enforce HTTPS
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Prevent clickjacking attacks
        response.headers['X-Frame-Options'] = 'DENY'
        
        # XSS protection (legacy, but still useful for older browsers)
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Content Security Policy - restrict resource loading
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "upgrade-insecure-requests"
        )
        
        # Referrer policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Feature policy / Permissions policy
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response
    
    # ==================== AUTHENTICATION ENDPOINTS (Phase 5) ====================
    
    if HAS_AUTH:
        @app.route('/api/auth/register', methods=['POST'])
        def register():
            """Register new user account."""
            try:
                data = request.get_json()
                
                # Validate required fields
                required_fields = ['email', 'username', 'password']
                for field in required_fields:
                    if not data.get(field):
                        raise APIError(f"Missing required field: {field}", 400)
                
                session = get_db_session()
                
                # Check if user already exists
                existing_user = session.query(User).filter(
                    (User.email == data['email']) | (User.username == data['username'])
                ).first()
                
                if existing_user:
                    raise APIError("User with this email or username already exists", 409)
                
                # Create new user
                user = User(
                    email=data['email'],
                    username=data['username'],
                    full_name=data.get('full_name'),
                    organization=data.get('organization'),
                    role='user',  # Default role
                    is_active=True,
                    is_verified=False,  # Require email verification in production
                )
                user.set_password(data['password'])
                
                session.add(user)
                session.commit()
                
                # Create JWT token
                token = create_jwt_token(user.id, user.email, user.role)
                
                return jsonify({
                    "status": "success",
                    "message": "User registered successfully",
                    "user": user.to_dict(),
                    "token": token,
                }), 201
                
            except APIError:
                raise
            except Exception as e:
                raise APIError(f"Registration failed: {str(e)}", 500)
            finally:
                if 'session' in locals():
                    session.close()
        
        @app.route('/api/auth/login', methods=['POST'])
        def login():
            """Login with email and password."""
            try:
                data = request.get_json()
                
                # Validate required fields
                if not data.get('email') or not data.get('password'):
                    raise APIError("Email and password are required", 400)
                
                session = get_db_session()
                
                # Authenticate user
                user = authenticate_user(session, data['email'], data['password'])
                
                if not user:
                    raise APIError("Invalid email or password", 401)
                
                # Create JWT token
                token = create_jwt_token(user.id, user.email, user.role)
                
                return jsonify({
                    "status": "success",
                    "message": "Login successful",
                    "user": user.to_dict(),
                    "token": token,
                })
                
            except AuthError as e:
                raise APIError(e.message, e.status_code)
            except APIError:
                raise
            except Exception as e:
                raise APIError(f"Login failed: {str(e)}", 500)
            finally:
                if 'session' in locals():
                    session.close()
        
        @app.route('/api/auth/me', methods=['GET'])
        @require_auth()
        def get_current_user():
            """Get current user profile."""
            from flask import g
            return jsonify({
                "status": "success",
                "user": g.current_user.to_dict(include_sensitive=True),
            })
        
        @app.route('/api/auth/api-keys', methods=['GET'])
        @require_auth()
        def list_api_keys():
            """List user's API keys."""
            from flask import g
            user = g.current_user
            
            return jsonify({
                "status": "success",
                "api_keys": [key.to_dict() for key in user.api_keys if key.is_active],
            })
        
        @app.route('/api/auth/api-keys', methods=['POST'])
        @require_auth()
        def create_api_key():
            """Create new API key."""
            from flask import g
            try:
                data = request.get_json() or {}
                user = g.current_user
                session = g.db_session
                
                # Generate API key
                key_value = APIKey.generate_key()
                
                api_key = APIKey(
                    user_id=user.id,
                    key=key_value,
                    name=data.get('name', f'API Key {len(user.api_keys) + 1}'),
                    prefix=key_value[:8],
                    rate_limit=data.get('rate_limit', 1000),
                )
                
                session.add(api_key)
                session.commit()
                
                return jsonify({
                    "status": "success",
                    "message": "API key created successfully",
                    "api_key": api_key.to_dict(include_full_key=True),
                    "warning": "Save this key now. You won't be able to see it again.",
                }), 201
                
            except Exception as e:
                raise APIError(f"Failed to create API key: {str(e)}", 500)
        
        # ==================== USER PREFERENCES ENDPOINTS (Sprint 5.4) ====================
        
        @app.route('/api/users/preferences', methods=['GET'])
        @require_auth()
        def get_user_preferences():
            """Get current user's preferences."""
            from flask import g
            user = g.current_user
            session = g.db_session
            
            try:
                # Get or create preferences
                prefs = session.query(UserPreferences).filter_by(user_id=user.id).first()
                
                if not prefs:
                    # Create default preferences
                    prefs = UserPreferences(user_id=user.id)
                    session.add(prefs)
                    session.commit()
                
                return jsonify({
                    "status": "success",
                    "preferences": prefs.to_dict(),
                })
                
            except Exception as e:
                raise APIError(f"Failed to get preferences: {str(e)}", 500)
        
        @app.route('/api/users/preferences', methods=['PUT'])
        @require_auth()
        def update_user_preferences():
            """Update current user's preferences."""
            from flask import g
            user = g.current_user
            session = g.db_session
            data = request.get_json()
            
            try:
                # Get or create preferences
                prefs = session.query(UserPreferences).filter_by(user_id=user.id).first()
                
                if not prefs:
                    prefs = UserPreferences(user_id=user.id)
                    session.add(prefs)
                
                # Update fields
                updatable_fields = [
                    'theme', 'tooltips_enabled', 'show_advanced_options', 'decimal_places',
                    'number_format', 'currency_symbol', 'chart_theme', 'default_chart_type',
                    'color_palette', 'legend_position', 'animation_enabled', 'animation_speed',
                    'cache_duration_policies', 'cache_duration_cbo_data', 'cache_duration_charts',
                    'auto_refresh_data', 'max_monte_carlo_iterations', 'debug_mode',
                    'experimental_features', 'api_endpoint', 'email_notifications',
                    'notify_simulation_complete', 'notify_policy_updates', 'notify_new_features',
                    'notify_weekly_digest', 'language', 'timezone', 'date_format',
                    'custom_theme_config'
                ]
                
                for field in updatable_fields:
                    if field in data:
                        setattr(prefs, field, data[field])
                
                session.commit()
                
                return jsonify({
                    "status": "success",
                    "message": "Preferences updated successfully",
                    "preferences": prefs.to_dict(),
                })
                
            except Exception as e:
                session.rollback()
                raise APIError(f"Failed to update preferences: {str(e)}", 500)
        
        @app.route('/api/users/preferences/reset', methods=['POST'])
        @require_auth()
        def reset_user_preferences():
            """Reset current user's preferences to defaults."""
            from flask import g
            user = g.current_user
            session = g.db_session
            
            try:
                # Get preferences
                prefs = session.query(UserPreferences).filter_by(user_id=user.id).first()
                
                if prefs:
                    # Delete existing preferences
                    session.delete(prefs)
                    session.commit()
                
                # Create new default preferences
                prefs = UserPreferences(user_id=user.id)
                session.add(prefs)
                session.commit()
                
                return jsonify({
                    "status": "success",
                    "message": "Preferences reset to defaults",
                    "preferences": prefs.to_dict(),
                })
                
            except Exception as e:
                session.rollback()
                raise APIError(f"Failed to reset preferences: {str(e)}", 500)
    
    # ==================== END AUTHENTICATION ENDPOINTS ====================
    
    # Health check
    @app.route('/api/health', methods=['GET'])
    def health():
        """Health check endpoint."""
        return jsonify({
            "status": "healthy",
            "version": "1.0",
            "authentication": "enabled" if HAS_AUTH else "disabled",
            "timestamp": datetime.now().isoformat()
        })
    
    # Policy endpoints
    @app.route('/api/policies', methods=['GET'])
    def list_policies():
        """List available policy templates."""
        try:
            library = PolicyLibrary()
            templates = [
                {"name": t.name, "type": t.policy_type, "parameters": len(t.parameters)}
                for t in library.templates.values()
            ]
            return jsonify({
                "status": "success",
                "count": len(templates),
                "policies": templates
            })
        except Exception as e:
            raise APIError(f"Failed to list policies: {str(e)}")
    
    @app.route('/api/policies/<policy_type>', methods=['GET'])
    def get_policy_template(policy_type):
        """Get policy template details."""
        try:
            library = PolicyLibrary()
            if policy_type not in library.templates:
                raise APIError(f"Policy type {policy_type} not found", 404)
            
            template = library.templates[policy_type]
            return jsonify({
                "status": "success",
                "name": template.name,
                "type": template.policy_type,
                "description": template.description,
                "parameters": [
                    {
                        "name": p.name,
                        "type": p.parameter_type,
                        "default": p.default_value,
                        "unit": p.unit,
                    }
                    for p in template.parameters.values()
                ]
            })
        except APIError:
            raise
        except Exception as e:
            raise APIError(f"Failed to get policy template: {str(e)}")
    
    # ==================== SLICE 5.7: V1 API ENDPOINTS ====================
    
    # Simulation endpoint (POST /api/v1/simulate)
    @app.route('/api/v1/simulate', methods=['POST'])
    def simulate_v1():
        """
        Run policy simulation with Monte Carlo analysis.
        
        Slice 5.7: Versioned, validated, observable.
        """
        request_id = str(uuid.uuid4())
        api_version = "1.0"
        
        try:
            # Parse and validate request
            request_data = request.get_json()
            if not request_data:
                raise ValidationError({"": ["Request body must be valid JSON"]})
            
            if not HAS_VALIDATION:
                raise APIError("Validation models not available", 500)
            
            req = SimulateRequest(**request_data)
            
            # Run simulation
            simulator = MonteCarloPolicySimulator()
            start_time = datetime.now(timezone.utc)
            
            result = simulator.simulate_policy(
                policy_name=req.policy_name,
                revenue_change_pct=req.revenue_change_pct,
                spending_change_pct=req.spending_change_pct,
                years=req.years,
                iterations=req.iterations,
            )
            
            duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            
            # Build response
            sensitivity = None
            if req.include_sensitivity:
                try:
                    analyzer = PolicySensitivityAnalyzer()
                    sens_df = analyzer.tornado_analysis(
                        base_revenue=5980,
                        base_spending=6911,
                        parameter_ranges={"Revenue": (-10, 20), "Spending": (-30, 10)},
                    )
                    sensitivity = SensitivityAnalysis(
                        parameters=[
                            SensitivityParameter(
                                name=str(row['Parameter']),
                                impact_low=float(row.get('Low', 0)),
                                impact_high=float(row.get('High', 0)),
                                tornado_rank=int(idx) + 1,
                            )
                            for idx, (_, row) in enumerate(sens_df.iterrows())
                        ]
                    )
                except Exception as e:
                    # Log sensitivity failure, but don't fail the entire request
                    print(f"Warning: Sensitivity analysis failed: {e}")
            
            response = SimulateResponse(
                status="success",
                simulation_id=str(uuid.uuid4()),
                policy_name=req.policy_name,
                years=req.years,
                iterations=req.iterations,
                results=SimulationResults(
                    mean_deficit=float(result.mean_deficit),
                    median_deficit=float(result.median_deficit),
                    std_dev=float(result.std_dev_deficit),
                    p10_deficit=float(result.p10_deficit),
                    p90_deficit=float(result.p90_deficit),
                    probability_balanced=float(result.probability_balanced) / 100.0,  # Convert percentage to probability
                    confidence_bounds=[float(result.p10_deficit), float(result.p90_deficit)],
                ),
                sensitivity=sensitivity,
                metadata=SimulationMetadata(
                    timestamp=datetime.now(timezone.utc),
                    api_version=api_version,
                    duration_ms=duration_ms,
                ),
            )
            
            return jsonify(response.model_dump()), 200
            
        except ValidationError as e:
            """Handle Pydantic validation errors."""
            field_errors = []
            for error in e.errors():
                field_name = ".".join(str(x) for x in error['loc'])
                field_errors.append(
                    FieldError(
                        field=field_name,
                        message=error['msg'],
                        value=request_data.get(field_name) if 'field_name' in locals() else None,
                    )
                )
            error_resp = create_error_response(
                error_code=ErrorCode.VALIDATION_ERROR,
                message="Request validation failed",
                request_id=request_id,
                api_version=api_version,
                field_errors=field_errors,
            )
            return jsonify(error_resp.model_dump()), 400
        except APIError as e:
            error_resp = create_error_response(
                error_code=ErrorCode.INTERNAL_ERROR if e.status_code >= 500 else ErrorCode.VALIDATION_ERROR,
                message=e.message,
                request_id=request_id,
                api_version=api_version,
            )
            return jsonify(error_resp.model_dump()), e.status_code
        except Exception as e:
            error_resp = create_error_response(
                error_code=ErrorCode.INTERNAL_ERROR,
                message=f"Simulation failed: {str(e)}",
                request_id=request_id,
                api_version=api_version,
            )
            return jsonify(error_resp.model_dump()), 500
    
    # Backward compatibility: old /api/simulate/policy endpoint
    @app.route('/api/simulate/policy', methods=['POST'])
    def simulate_policy():
        """Run policy simulation (legacy endpoint, redirect to v1)."""
        try:
            data = request.get_json()
            
            # Validate input
            if not data or 'revenue_change_pct' not in data:
                raise APIError("Missing required parameters: revenue_change_pct, spending_change_pct")
            
            revenue_change = data.get('revenue_change_pct', 0)
            spending_change = data.get('spending_change_pct', 0)
            years = data.get('years', 10)
            iterations = data.get('iterations', 5000)
            
            # Run simulation
            simulator = MonteCarloPolicySimulator()
            result = simulator.simulate_policy(
                policy_name=data.get('policy_name', 'Custom Policy'),
                revenue_change_pct=revenue_change,
                spending_change_pct=spending_change,
                years=years,
                iterations=iterations,
            )
            
            return jsonify({
                "status": "success",
                "policy_name": result.policy_name,
                "iterations": result.iterations,
                "mean_deficit": float(result.mean_deficit),
                "median_deficit": float(result.median_deficit),
                "std_dev": float(result.std_dev_deficit),
                "p10_deficit": float(result.p10_deficit),
                "p90_deficit": float(result.p90_deficit),
                "probability_balanced": float(result.probability_balanced),
                "confidence_bounds": [float(result.p10_deficit), float(result.p90_deficit)],
            })
        except APIError:
            raise
        except Exception as e:
            raise APIError(f"Simulation failed: {str(e)}")
    
    # Scenarios listing endpoint (GET /api/v1/scenarios)
    @app.route('/api/v1/scenarios', methods=['GET'])
    def scenarios_list_v1():
        """
        List available policy scenarios with filtering and pagination.
        
        Slice 5.7: Versioned, validated, observable.
        """
        request_id = str(uuid.uuid4())
        api_version = "1.0"
        
        try:
            # Parse and validate query params
            if not HAS_VALIDATION:
                raise APIError("Validation models not available", 500)
            
            req = ScenariosListRequest(
                page=request.args.get('page', 1, type=int),
                per_page=request.args.get('per_page', 20, type=int),
                filter_type=request.args.get('filter_type', 'all', type=str),
                search=request.args.get('search', None, type=str),
                sort_by=request.args.get('sort_by', 'created_at', type=str),
                sort_order=request.args.get('sort_order', 'desc', type=str),
            )
            
            # Load scenarios from proper scenarios file, not catalog (which contains PDFs)
            # Try multiple possible scenario file locations
            scenarios_files = [
                Path('policies/scenarios.json'),
                Path('policies/scenario_usgha_base.json'),
            ]
            scenarios_data = []
            
            for scenarios_file in scenarios_files:
                if scenarios_file.exists():
                    try:
                        with open(scenarios_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            # Handle both list and dict formats
                            if isinstance(data, list):
                                # If it's a list of scenario objects
                                scenarios_data = [s for s in data if isinstance(s, dict)]
                            elif isinstance(data, dict):
                                # If it's a dict with 'scenarios' key
                                if 'scenarios' in data and isinstance(data['scenarios'], list):
                                    scenarios_data = [s for s in data['scenarios'] if isinstance(s, dict)]
                                else:
                                    # Single scenario object
                                    scenarios_data = [data] if 'name' in data else []
                            
                            if scenarios_data:
                                break  # Found valid scenarios, stop searching
                    except (json.JSONDecodeError, UnicodeDecodeError) as e:
                        # Log error and try next file
                        import logging
                        logging.getLogger(__name__).warning(f"Failed to load {scenarios_file}: {e}")
                        continue
            
            # If no scenarios found, return empty list with proper response
            if not scenarios_data:
                response = ScenariosListResponse(
                    status="success",
                    scenario_count=0,
                    returned_count=0,
                    pagination=PaginationInfo(page=1, per_page=20, total_pages=0),
                    scenarios=[],
                    metadata=ScenariosListMetadata(
                        timestamp=datetime.now(timezone.utc),
                        api_version=api_version,
                    ),
                )
                return jsonify(response.model_dump()), 200
            
            # Apply filtering - safely handle dict items
            if req.filter_type.value != 'all':
                scenarios_data = [
                    s for s in scenarios_data 
                    if isinstance(s, dict) and s.get('type') == req.filter_type.value
                ]
            
            # Apply search - safely handle dict items
            if req.search:
                search_lower = req.search.lower()
                scenarios_data = [
                    s for s in scenarios_data
                    if isinstance(s, dict) and search_lower in (
                        (s.get('name', '') or '') + (s.get('description', '') or '')
                    ).lower()
                ]
            
            # Apply sorting
            sort_field_map = {
                'name': 'name',
                'created_at': 'created_at',
                'impact_deficit': 'projected_deficit',
            }
            sort_field = sort_field_map.get(req.sort_by.value, 'created_at')
            
            try:
                scenarios_data.sort(
                    key=lambda x: x.get(sort_field, ''),
                    reverse=(req.sort_order.value == 'desc')
                )
            except (TypeError, ValueError) as e:
                # Sorting failed, likely due to type mismatch in sort field
                import logging
                logging.getLogger(__name__).debug(f"Failed to sort scenarios by {sort_field}: {e}")
                # Return unsorted data rather than raising error
            
            # Pagination
            total_count = len(scenarios_data)
            total_pages = (total_count + req.per_page - 1) // req.per_page
            start_idx = (req.page - 1) * req.per_page
            end_idx = start_idx + req.per_page
            paginated_data = scenarios_data[start_idx:end_idx]
            
            # Build response
            scenario_items = [
                ScenarioListItem(
                    id=s.get('id', str(uuid.uuid4())),
                    name=s.get('name', 'Unnamed Scenario'),
                    type=s.get('type', 'custom'),
                    description=s.get('description', ''),
                    revenue_change_pct=float(s.get('revenue_change_pct', 0)),
                    spending_change_pct=float(s.get('spending_change_pct', 0)),
                    projected_deficit=float(s.get('projected_deficit', 0)),
                    created_at=datetime.fromisoformat(s.get('created_at', datetime.now(timezone.utc).isoformat())),
                    created_by=s.get('created_by', 'system'),
                    is_public=s.get('is_public', True),
                    tags=s.get('tags', []),
                )
                for s in paginated_data
            ]
            
            response = ScenariosListResponse(
                status="success",
                scenario_count=total_count,
                returned_count=len(scenario_items),
                pagination=PaginationInfo(
                    page=req.page,
                    per_page=req.per_page,
                    total_pages=max(1, total_pages),
                ),
                scenarios=scenario_items,
                metadata=ScenariosListMetadata(
                    timestamp=datetime.now(timezone.utc),
                    api_version=api_version,
                ),
            )
            
            return jsonify(response.model_dump()), 200
            
        except ValidationError as e:
            """Handle Pydantic validation errors."""
            field_errors = []
            for error in e.errors():
                field_name = ".".join(str(x) for x in error['loc'])
                field_errors.append(
                    FieldError(
                        field=field_name,
                        message=error['msg'],
                        value=request.args.get(field_name),
                    )
                )
            error_resp = create_error_response(
                error_code=ErrorCode.VALIDATION_ERROR,
                message="Query parameter validation failed",
                request_id=request_id,
                api_version=api_version,
                field_errors=field_errors,
            )
            return jsonify(error_resp.model_dump()), 400
        except APIError as e:
            error_resp = create_error_response(
                error_code=ErrorCode.INTERNAL_ERROR if e.status_code >= 500 else ErrorCode.VALIDATION_ERROR,
                message=e.message,
                request_id=request_id,
                api_version=api_version,
            )
            return jsonify(error_resp.model_dump()), e.status_code
        except Exception as e:
            error_resp = create_error_response(
                error_code=ErrorCode.INTERNAL_ERROR,
                message=f"Scenario listing failed: {str(e)}",
                request_id=request_id,
                api_version=api_version,
            )
            return jsonify(error_resp.model_dump()), 500
    
    # Sensitivity analysis
    @app.route('/api/analyze/sensitivity', methods=['POST'])
    def sensitivity_analysis():
        """Run sensitivity analysis."""
        try:
            data = request.get_json()
            
            base_revenue = data.get('base_revenue', 5980)
            base_spending = data.get('base_spending', 6911)
            parameter_ranges = data.get('parameter_ranges', {
                'Revenue': (-10, 20),
                'Spending': (-30, 10),
            })
            
            analyzer = PolicySensitivityAnalyzer()
            result_df = analyzer.tornado_analysis(
                base_revenue=base_revenue,
                base_spending=base_spending,
                parameter_ranges=parameter_ranges,
            )
            
            return jsonify({
                "status": "success",
                "analysis": "sensitivity",
                "parameters": result_df.to_dict(orient='records'),
            })
        except Exception as e:
            raise APIError(f"Sensitivity analysis failed: {str(e)}")
    
    # Stress testing
    @app.route('/api/analyze/stress', methods=['POST'])
    def stress_test():
        """Run stress test analysis."""
        try:
            data = request.get_json()
            
            policy_params = {
                'revenue_change_pct': data.get('revenue_change_pct', 0),
                'spending_change_pct': data.get('spending_change_pct', 0),
            }
            
            analyzer = StressTestAnalyzer()
            result_df = analyzer.run_stress_test(policy_params)
            
            return jsonify({
                "status": "success",
                "analysis": "stress_test",
                "scenarios": result_df.to_dict(orient='records'),
            })
        except Exception as e:
            raise APIError(f"Stress test failed: {str(e)}")
    
    # Recommendation endpoint
    @app.route('/api/recommend/policies', methods=['POST'])
    def recommend_policies():
        """Get policy recommendations."""
        try:
            data = request.get_json()
            
            fiscal_goal = data.get('fiscal_goal', 'minimize_deficit')
            limit = data.get('limit', 5)
            
            # Map string to enum
            goal_map = {
                'minimize_deficit': FiscalGoal.MINIMIZE_DEFICIT,
                'maximize_revenue': FiscalGoal.MAXIMIZE_REVENUE,
                'balance_budget': FiscalGoal.BALANCE_BUDGET,
                'sustainable_debt': FiscalGoal.SUSTAINABLE_DEBT,
                'growth_focused': FiscalGoal.GROWTH_FOCUSED,
                'equity_focused': FiscalGoal.EQUITY_FOCUSED,
            }
            
            goal = goal_map.get(fiscal_goal.lower(), FiscalGoal.MINIMIZE_DEFICIT)
            
            engine = PolicyRecommendationEngine()
            recommendations = engine.recommend_policies(goal=goal, limit=limit)
            
            return jsonify({
                "status": "success",
                "fiscal_goal": fiscal_goal,
                "recommendations": [
                    {
                        "policy": rec.policy_name,
                        "overall_score": float(rec.overall_score),
                        "fiscal_impact": float(rec.fiscal_impact),
                        "sustainability": float(rec.sustainability_score),
                        "feasibility": float(rec.feasibility_score),
                        "equity": float(rec.equity_score),
                        "growth": float(rec.growth_impact),
                    }
                    for rec in recommendations
                ]
            })
        except Exception as e:
            raise APIError(f"Recommendation failed: {str(e)}")
    
    # Impact calculation
    @app.route('/api/calculate/impact', methods=['POST'])
    def calculate_impact():
        """Calculate fiscal impact of policy."""
        try:
            data = request.get_json()
            
            revenue_change = data.get('revenue_change_pct', 0)
            spending_change = data.get('spending_change_pct', 0)
            years = data.get('years', 10)
            
            calculator = PolicyImpactCalculator()
            impact_df = calculator.calculate_impact(
                policy_name=data.get('policy_name', 'Policy'),
                revenue_change_pct=revenue_change,
                spending_change_pct=spending_change,
                years=years,
            )
            
            return jsonify({
                "status": "success",
                "policy": data.get('policy_name', 'Policy'),
                "projections": impact_df.to_dict(orient='records'),
                "total_deficit": float(impact_df['Deficit'].sum()),
                "avg_deficit": float(impact_df['Deficit'].mean()),
            })
        except Exception as e:
            raise APIError(f"Impact calculation failed: {str(e)}")
    
    # Data endpoints
    @app.route('/api/data/baseline', methods=['GET'])
    def get_baseline_data():
        """Get baseline fiscal data."""
        try:
            data = load_real_data()
            return jsonify({
                "status": "success",
                "revenue": float(data['revenue']),
                "spending": float(data['spending']),
                "deficit": float(data['deficit']),
                "gdp": float(data['gdp']),
                "deficit_pct_gdp": float(data['deficit_pct_gdp']),
            })
        except Exception as e:
            raise APIError(f"Failed to load baseline data: {str(e)}")
    
    @app.route('/api/data/historical', methods=['GET'])
    def get_historical_data():
        """Get historical fiscal data."""
        try:
            # Return sample historical data
            historical = pd.DataFrame({
                'Year': list(range(2015, 2025)),
                'Revenue': [3300, 3450, 3600, 3750, 3900, 3980, 4100, 4200, 4300, 4400],
                'Spending': [3800, 3950, 4100, 4250, 4400, 4550, 4700, 4850, 5000, 5150],
            })
            historical['Deficit'] = historical['Spending'] - historical['Revenue']
            
            return jsonify({
                "status": "success",
                "historical": historical.to_dict(orient='records'),
            })
        except Exception as e:
            raise APIError(f"Failed to load historical data: {str(e)}")

    # Optional security knobs for ingestion health endpoint
    ingestion_health_require_auth = os.getenv("INGESTION_HEALTH_REQUIRE_AUTH", "false").lower() in {"1", "true", "yes", "on"}
    ingestion_health_rate_limit = os.getenv("INGESTION_HEALTH_RATE_LIMIT", "false").lower() in {"1", "true", "yes", "on"}

    # Ingestion health endpoint v1 (GET /api/v1/data/ingestion-health)
    @app.route('/api/v1/data/ingestion-health', methods=['GET'])
    def get_ingestion_health_v1():
        """
        Report CBO data ingestion status, freshness, and schema validity.
        
        Slice 5.7: Versioned, validated, observable.
        """
        request_id = str(uuid.uuid4())
        api_version = "1.0"
        
        try:
            # Parse and validate query params
            if not HAS_VALIDATION:
                raise APIError("Validation models not available", 500)
            
            req = IngestionHealthRequest(
                include_history=request.args.get('include_history', 'false', type=str).lower() in {'1', 'true', 'yes', 'on'}
            )
            
            # If history requested and not authenticated, return 401
            if req.include_history and ingestion_health_require_auth and HAS_AUTH:
                # Check if user is authenticated (simplified check)
                auth_header = request.headers.get('Authorization', '')
                if not auth_header.startswith('Bearer '):
                    error_resp = create_error_response(
                        error_code=ErrorCode.AUTH_REQUIRED,
                        message="Authentication required for historical data",
                        request_id=request_id,
                        api_version=api_version,
                    )
                    return jsonify(error_resp.model_dump()), 401
            
            from core.cbo_scraper import CBODataScraper
            
            scraper = CBODataScraper(use_cache=True)
            payload = None
            history = []
            
            # Try cached data first
            if scraper.cached_data:
                payload = scraper._attach_metadata(
                    scraper.cached_data,
                    cache_used=True,
                    schema_valid=getattr(scraper, 'cached_data_valid', True)
                )
            
            # Fall back to live fetch
            if payload is None:
                payload = scraper.get_current_us_budget_data()
            
            if not payload:
                error_resp = create_error_response(
                    error_code=ErrorCode.SERVICE_UNAVAILABLE,
                    message="No CBO data available",
                    request_id=request_id,
                    api_version=api_version,
                )
                return jsonify(error_resp.model_dump()), 503
            
            # Build history if requested
            if req.include_history and hasattr(scraper, 'history') and scraper.history:
                history = [
                    HistoryEntry(
                        timestamp=datetime.fromisoformat(entry.get('timestamp', datetime.now(timezone.utc).isoformat())),
                        checksum=entry.get('checksum', ''),
                        is_live=entry.get('is_live', False),
                        schema_valid=entry.get('schema_valid', True),
                    )
                    for entry in scraper.history[-30:]  # Last 30 entries
                ]
            
            # Build response
            response = IngestionHealthResponse(
                status="success",
                ingestion=IngestionInfo(
                    data_source=payload.get("data_source", "unknown"),
                    is_live=not payload.get("cache_used", False),
                    freshness_hours=float(payload.get("freshness_hours", 0)),
                    cache_age_hours=float(payload.get("cache_age_hours", 0)),
                    last_updated=datetime.fromisoformat(payload.get("last_updated", datetime.now(timezone.utc).isoformat())),
                    fetched_at=datetime.fromisoformat(payload.get("fetched_at", datetime.now(timezone.utc).isoformat())),
                ),
                validation=ValidationInfo(
                    schema_valid=payload.get("schema_valid", True),
                    checksum=payload.get("checksum", ""),
                    validation_errors=payload.get("validation_errors", []),
                ),
                metrics=IngestionMetrics(
                    data_points_ingested=len(payload.get("revenues", {})) + len(payload.get("spending", {})),
                    schema_version=payload.get("schema_version", "1.0"),
                ),
                history=history if req.include_history else None,
                metadata=IngestionHealthMetadata(
                    api_version=api_version,
                    timestamp=datetime.now(timezone.utc),
                ),
            )
            
            return jsonify(response.model_dump(exclude_none=True)), 200
            
        except ValidationError as e:
            """Handle Pydantic validation errors."""
            field_errors = []
            for error in e.errors():
                field_name = ".".join(str(x) for x in error['loc'])
                field_errors.append(
                    FieldError(
                        field=field_name,
                        message=error['msg'],
                        value=request.args.get(field_name),
                    )
                )
            error_resp = create_error_response(
                error_code=ErrorCode.VALIDATION_ERROR,
                message="Query parameter validation failed",
                request_id=request_id,
                api_version=api_version,
                field_errors=field_errors,
            )
            return jsonify(error_resp.model_dump()), 400
        except APIError as e:
            error_resp = create_error_response(
                error_code=ErrorCode.INTERNAL_ERROR if e.status_code >= 500 else ErrorCode.VALIDATION_ERROR,
                message=e.message,
                request_id=request_id,
                api_version=api_version,
            )
            return jsonify(error_resp.model_dump()), e.status_code
        except Exception as e:
            error_resp = create_error_response(
                error_code=ErrorCode.INTERNAL_ERROR,
                message=f"Ingestion health check failed: {str(e)}",
                request_id=request_id,
                api_version=api_version,
            )
            return jsonify(error_resp.model_dump()), 500

    # Legacy endpoint (backward compatibility)
    @app.route('/api/data/ingestion-health', methods=['GET'])
    def get_ingestion_health():
        """Report CBO ingestion/cache status including checksum and freshness (legacy)."""
        try:
            from core.cbo_scraper import CBODataScraper

            scraper = CBODataScraper(use_cache=True)
            payload = None

            if scraper.cached_data:
                payload = scraper._attach_metadata(
                    scraper.cached_data,
                    cache_used=True,
                    schema_valid=getattr(scraper, 'cached_data_valid', True)
                )

            if payload is None:
                payload = scraper.get_current_us_budget_data()

            if not payload:
                raise APIError("No CBO data available", 503)

            return jsonify({
                "status": "success",
                "data": {
                    "data_source": payload.get("data_source"),
                    "checksum": payload.get("checksum"),
                    "cache_used": payload.get("cache_used"),
                    "freshness_hours": payload.get("freshness_hours"),
                    "cache_age_hours": payload.get("cache_age_hours"),
                    "last_updated": payload.get("last_updated"),
                    "fetched_at": payload.get("fetched_at"),
                    "schema_valid": payload.get("schema_valid", True),
                    "validation_errors": payload.get("validation_errors", []),
                },
            })
        except ImportError:
            raise APIError("CBO scraper module not available", 500)
        except Exception as e:
            raise APIError(f"Failed to load ingestion status: {str(e)}", 500)

    # Apply optional auth/rate-limit wrappers only when enabled and auth stack is present
    if HAS_AUTH and ingestion_health_require_auth:
        get_ingestion_health = require_auth()(get_ingestion_health)
        if ingestion_health_rate_limit:
            get_ingestion_health = require_rate_limit(get_ingestion_health)
    
    
    @app.route('/api/data/refresh', methods=['POST'])
    @require_auth(roles=['admin'])
    def refresh_cbo_data():
        """
        Manually refresh CBO data from live sources (admin only).
        
        Phase 5.2: Manual refresh endpoint with authentication.
        Fetches latest data from CBO/Treasury/OMB, validates, and caches.
        
        Returns:
            JSON with updated data and timestamp
        """
        try:
            from core.cbo_scraper import CBODataScraper
            
            # Create scraper with notifications enabled
            scraper = CBODataScraper(use_cache=True, enable_notifications=True)
            
            # Fetch fresh data
            data = scraper.get_current_us_budget_data()
            
            if not data:
                raise APIError("Failed to fetch data from CBO/Treasury sources", 503)
            
            return jsonify({
                "status": "success",
                "message": "Data refreshed successfully",
                "data": {
                    "gdp": data['gdp'],
                    "national_debt": data['debt'],
                    "deficit": data['deficit'],
                    "total_revenue": sum(data['revenues'].values()),
                    "total_spending": sum(data['spending'].values()),
                    "interest_rate": data['interest_rate'],
                    "last_updated": data['last_updated'],
                    "data_source": data['data_source'],
                },
            })
        except ImportError:
            raise APIError("CBO scraper module not available", 500)
        except Exception as e:
            raise APIError(f"Failed to refresh data: {str(e)}", 500)
    
    @app.route('/api/data/history', methods=['GET'])
    @require_auth()
    def get_cbo_history():
        """
        Get historical CBO data (last 365 days of updates).
        
        Phase 5.2: Historical data tracking endpoint.
        Shows how CBO data has changed over time.
        
        Query params:
            limit (int): Max number of entries (default: 30)
        
        Returns:
            JSON with historical data entries
        """
        try:
            from core.cbo_scraper import CBODataScraper
            
            scraper = CBODataScraper()
            limit = request.args.get('limit', 30, type=int)
            
            # Get recent history
            history = scraper.history[-limit:] if scraper.history else []
            
            return jsonify({
                "status": "success",
                "count": len(history),
                "history": [
                    {
                        "timestamp": entry['timestamp'],
                        "hash": entry['hash'],
                        "gdp": entry['data'].get('gdp'),
                        "debt": entry['data'].get('debt'),
                        "deficit": entry['data'].get('deficit'),
                    }
                    for entry in history
                ],
            })
        except ImportError:
            raise APIError("CBO scraper module not available", 500)
        except Exception as e:
            raise APIError(f"Failed to retrieve history: {str(e)}", 500)

    
    # Report generation endpoint
    @app.route('/api/report/generate', methods=['POST'])
    def generate_report():
        """Generate fiscal policy report."""
        try:
            data = request.get_json()
            
            metadata = ReportMetadata(
                title=data.get('title', 'Fiscal Policy Report'),
                author=data.get('author', 'PoliSim API'),
                description=data.get('description', ''),
            )
            
            builder = ComprehensiveReportBuilder(metadata)
            builder.add_executive_summary(data.get('summary', 'Report generated via API.'))
            
            # Generate JSON (always available)
            report_dir = Path('reports/api_generated')
            report_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_path = report_dir / f"report_{timestamp}.json"
            
            builder.generate_json(str(json_path))
            
            return jsonify({
                "status": "success",
                "report": str(json_path),
                "format": "json",
                "timestamp": timestamp,
            })
        except Exception as e:
            raise APIError(f"Report generation failed: {str(e)}")
    
    # Scenario comparison
    @app.route('/api/scenarios/compare', methods=['POST'])
    def compare_scenarios():
        """Compare multiple policy scenarios."""
        try:
            data = request.get_json()
            scenarios = data.get('scenarios', [])
            
            if not scenarios:
                raise APIError("No scenarios provided")
            
            explorer = InteractiveScenarioExplorer()
            comparison = explorer.create_scenario_list(
                scenarios=[s.get('name', f'Scenario {i}') for i, s in enumerate(scenarios)]
            )
            
            results = []
            for scenario in scenarios:
                calc = PolicyImpactCalculator()
                impact = calc.calculate_impact(
                    policy_name=scenario.get('name', 'Scenario'),
                    revenue_change_pct=scenario.get('revenue_change_pct', 0),
                    spending_change_pct=scenario.get('spending_change_pct', 0),
                    years=scenario.get('years', 10),
                )
                
                results.append({
                    "scenario": scenario.get('name'),
                    "10_year_deficit": float(impact['Deficit'].sum()),
                    "avg_deficit": float(impact['Deficit'].mean()),
                    "final_year_deficit": float(impact['Deficit'].iloc[-1]),
                })
            
            return jsonify({
                "status": "success",
                "scenario_count": len(results),
                "scenarios": results,
            })
        except APIError:
            raise
        except Exception as e:
            raise APIError(f"Scenario comparison failed: {str(e)}")
    
    return app


def run_api_server(host: str = '127.0.0.1', port: int = 5000, debug: bool = False):
    """Run the REST API server."""
    try:
        app = create_api_app()
        print(f"Starting PoliSim REST API on {host}:{port}")
        print(f"API Documentation: http://{host}:{port}/api/health")
        app.run(host=host, port=port, debug=debug)
    except ImportError as e:
        print(f"Error: {e}")
        print("Install Flask with: pip install flask flask-cors")


if __name__ == "__main__":
    run_api_server(debug=True)
