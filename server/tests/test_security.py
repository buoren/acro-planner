"""
Security tests for the Acro Planner API

Tests authentication requirements, CORS restrictions, rate limiting,
and other security vulnerabilities identified during Phase 1 implementation.
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import status, HTTPException
import time
from unittest.mock import patch
from main import app
from database import get_db
from api.auth import require_auth, get_current_user


class TestEndpointAuthentication:
    """Test that all endpoints properly require authentication"""
    
    def test_users_list_requires_auth(self, test_client):
        """GET /users/ endpoint should require authentication"""
        response = test_client.get("/users/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "authentication" in response.json()["detail"].lower()
    
    def test_users_me_requires_auth(self, test_client):
        """GET /users/me endpoint should require authentication"""
        response = test_client.get("/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_user_detail_requires_auth(self, test_client):
        """GET /users/{id} endpoint should require authentication"""
        response = test_client.get("/users/some-id")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_user_promotion_requires_admin_auth(self, test_client):
        """POST /users/{id}/promote-admin endpoint should require admin authentication"""
        response = test_client.post("/users/some-id/promote-admin")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_users_by_role_requires_admin_auth(self, test_client):
        """GET /users/by-role/{role} endpoint should require admin authentication"""
        response = test_client.get("/users/by-role/attendee")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_public_endpoints_work_without_auth(self, test_client):
        """Verify that explicitly public endpoints still work without auth"""
        # Health check should always be public
        response = test_client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        
        # User registration should be public
        response = test_client.post("/users/register", json={
            "email": "test@example.com",
            "name": "Test User",
            "password": "testpass123"
        })
        # Should fail for reasons other than authentication (like validation or duplicate)
        assert response.status_code != status.HTTP_401_UNAUTHORIZED


class TestCORSOriginRestrictions:
    """Test CORS origin restrictions and validation"""
    
    def test_cors_allows_specific_origins_only(self, test_client):
        """CORS should only allow specific origins, not wildcard *"""
        # Test with unauthorized origin
        headers = {"Origin": "https://malicious-site.com"}
        response = test_client.options("/users/", headers=headers)
        
        # Should either reject the origin or not include it in Access-Control-Allow-Origin
        cors_header = response.headers.get("Access-Control-Allow-Origin")
        assert cors_header != "*", "CORS should not allow wildcard origins"
        
        if cors_header:
            assert "malicious-site.com" not in cors_header
    
    def test_cors_allows_legitimate_origins(self, test_client):
        """CORS should allow legitimate frontend origins"""
        legitimate_origins = [
            "http://localhost:3000",  # Development
            "http://localhost:5173",  # SvelteKit dev
            "http://localhost:8080",  # Flutter dev
            "https://storage.googleapis.com",  # Flutter production
        ]
        
        for origin in legitimate_origins:
            headers = {"Origin": origin}
            response = test_client.options("/health", headers=headers)
            cors_header = response.headers.get("Access-Control-Allow-Origin")
            
            # Either the specific origin should be allowed, or it should be in a list
            if cors_header:
                assert cors_header == origin or cors_header == "*" and False, \
                    f"Legitimate origin {origin} should be allowed, but CORS is too permissive"


class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def test_rate_limiting_on_registration_endpoint(self, test_client):
        """Registration endpoint should have rate limiting to prevent spam"""
        # Try to register multiple users rapidly (limit is 5 for /users/register)
        rate_limited = False
        
        for i in range(7):  # Try 7 rapid requests (should hit limit at 6th)
            try:
                response = test_client.post("/users/register", json={
                    "email": f"test{i}@example.com",
                    "name": f"Test User {i}",
                    "password": "testpass123"
                })
                
                # After 5 requests, should get rate limited
                if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                    # Verify rate limit response structure
                    assert "Rate limit exceeded" in str(response.json())
                    rate_limited = True
                    break
                    
            except HTTPException as e:
                # The HTTPException is raised during the request itself in middleware
                if e.status_code == 429:
                    rate_limited = True
                    break
                raise  # Re-raise if it's not a rate limit error
            except Exception as e:
                # Handle other exceptions that might include HTTPException details
                if "429" in str(e) or "Rate limit" in str(e):
                    rate_limited = True
                    break
                raise  # Re-raise if it's not a rate limit error
        
        assert rate_limited, "No rate limiting detected on registration endpoint after 7 attempts"
    
    def test_rate_limiting_on_login_endpoint(self, test_client):
        """Login endpoint should have rate limiting to prevent brute force"""
        # This would test auth/login endpoint if it existed
        # For now, test that repeated auth attempts get rate limited
        for i in range(20):  # Try many rapid requests
            response = test_client.get("/users/me")  # This will fail auth, but should get rate limited
            
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                break
        else:
            pytest.fail("No rate limiting detected on authentication attempts")
    
    def test_rate_limiting_headers_present(self, test_client):
        """Rate limiting should include appropriate headers"""
        response = test_client.get("/health")
        
        # Should include rate limit headers
        rate_limit_headers = [
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining", 
            "X-RateLimit-Reset",
            "Retry-After"  # When rate limited
        ]
        
        # At least some rate limiting headers should be present
        # This test might need to be adjusted based on actual implementation
        pass  # Will implement once rate limiting is added


class TestSessionAuthentication:
    """Test session-based authentication validation"""
    
    def test_invalid_session_rejected(self, test_client):
        """Invalid or expired sessions should be rejected"""
        # Test with invalid session cookie
        test_client.cookies.set("session", "invalid-session-token")
        response = test_client.get("/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_missing_session_rejected(self, test_client):
        """Requests without session should be rejected for protected endpoints"""
        # Ensure no session cookie is set
        test_client.cookies.clear()
        response = test_client.get("/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_session_validation_on_protected_endpoints(self, test_client):
        """All protected endpoints should validate session tokens"""
        protected_endpoints = [
            ("GET", "/users/"),
            ("GET", "/users/me"),
            ("GET", "/users/some-id"),
            ("POST", "/users/some-id/promote-admin"),
            ("GET", "/users/by-role/attendee"),
        ]
        
        for method, endpoint in protected_endpoints:
            response = getattr(test_client, method.lower())(endpoint)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
                f"{method} {endpoint} should require authentication"


class TestAuthorizationBypass:
    """Test prevention of authorization bypass attempts"""
    
    def test_cannot_bypass_admin_requirement(self, test_client):
        """Users cannot bypass admin requirements through parameter manipulation"""
        # Mock a non-admin user session
        with patch('server.api.auth.require_auth') as mock_auth:
            mock_auth.return_value = {
                'id': 'user123',
                'roles': ['attendee'],
                'is_admin': False,
                'is_host': False,
                'is_attendee': True,
            }
            
            # Try to access admin endpoint
            response = test_client.get("/users/by-role/admin")
            assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_cannot_bypass_authentication_with_fake_headers(self, test_client):
        """Fake authentication headers should not bypass authentication"""
        fake_auth_headers = {
            "X-User-ID": "fake-user-id",
            "Authorization": "Bearer fake-token",
            "X-Admin": "true",
            "X-Authenticated": "true"
        }
        
        response = test_client.get("/users/me", headers=fake_auth_headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_cannot_access_others_data_with_id_manipulation(self, test_client):
        """Users cannot access other users' data by manipulating IDs"""
        # This test would be more meaningful with actual user data
        # For now, test that unauthorized access attempts fail
        response = test_client.get("/users/other-user-id")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestSecurityHeaders:
    """Test security headers in responses"""
    
    def test_security_headers_present(self, test_client):
        """Security headers should be present in responses"""
        response = test_client.get("/health")
        
        expected_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY", 
            "X-XSS-Protection": "1; mode=block",
        }
        
        for header, expected_value in expected_headers.items():
            assert header in response.headers, f"Security header {header} missing"
            assert response.headers[header] == expected_value
    
    def test_https_security_headers_in_production(self, test_client):
        """HTTPS-specific security headers should be present in production"""
        response = test_client.get("/health")
        
        # These headers should be present in production (HTTPS) environment
        if app.state.environment == "production":
            assert "Strict-Transport-Security" in response.headers
    
    def test_no_sensitive_info_in_error_responses(self, test_client):
        """Error responses should not leak sensitive information"""
        response = test_client.get("/users/non-existent-id")
        
        # Should not reveal internal paths, stack traces, or database info
        response_text = response.text.lower()
        sensitive_patterns = [
            "/users/buoren",  # Internal paths
            "traceback",      # Stack traces
            "mysql",          # Database info
            "sqlalchemy",     # ORM info
            "secret",         # Secret keys
            "password",       # Password info
        ]
        
        for pattern in sensitive_patterns:
            assert pattern not in response_text, f"Sensitive info '{pattern}' leaked in error response"


class TestInputValidation:
    """Test input validation and sanitization"""
    
    def test_sql_injection_prevention(self, test_client):
        """API should prevent SQL injection attempts"""
        sql_injection_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM users --",
            "<script>alert('xss')</script>",
        ]
        
        for payload in sql_injection_payloads:
            # Test in various endpoints
            response = test_client.get(f"/users/{payload}")
            assert response.status_code in [400, 404, 422], \
                f"SQL injection payload not properly handled: {payload}"
    
    def test_request_size_limits(self, test_client):
        """Large requests should be rejected"""
        large_payload = {"name": "x" * 10000}  # Very large name
        response = test_client.post("/users/register", json=large_payload)
        assert response.status_code in [400, 413, 422], "Large requests should be rejected"
    
    def test_malformed_json_handling(self, test_client):
        """Malformed JSON should be handled gracefully"""
        response = test_client.post(
            "/users/register", 
            data="{'invalid': json}",  # Malformed JSON
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422, "Malformed JSON should return 422"


class TestProductionSecurityConfiguration:
    """Test production security configuration"""
    
    def test_debug_mode_disabled_in_production(self, test_client):
        """Debug mode should be disabled in production"""
        # Test that debug endpoints don't exist
        debug_endpoints = [
            "/debug",
            "/admin/debug", 
            "/docs",  # In production, docs might be disabled
        ]
        
        for endpoint in debug_endpoints:
            response = test_client.get(endpoint)
            # Should either be 404 (not found) or 403 (forbidden in production)
            if app.state.environment == "production":
                assert response.status_code in [404, 403]
    
    def test_error_details_limited_in_production(self, test_client):
        """Error details should be limited in production environment"""
        response = test_client.get("/users/trigger-error")  # This might not exist
        
        if response.status_code == 500 and app.state.environment == "production":
            error_response = response.json()
            # Should not contain detailed error info in production
            assert "traceback" not in str(error_response).lower()
            assert "sqlalchemy" not in str(error_response).lower()


# Integration test for complete authentication flow
class TestAuthenticationIntegration:
    """Integration tests for complete authentication workflow"""
    
    def test_complete_auth_flow_with_session(self, test_client):
        """Test complete authentication flow with session validation"""
        # 1. Try to access protected endpoint without auth - should fail
        response = test_client.get("/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # 2. Login (would need actual login endpoint)
        # For now, test that OAuth flow endpoints exist
        auth_endpoints = ["/auth/login", "/auth/callback", "/auth/logout"]
        for endpoint in auth_endpoints:
            response = test_client.get(endpoint)
            # Should not be 401 (these are auth endpoints themselves)
            assert response.status_code != status.HTTP_401_UNAUTHORIZED
        
        # 3. Access protected endpoint with valid session - should work
        # This would require mocking actual session validation
        pass
    
    def test_auth_state_consistency(self, test_client):
        """Test that authentication state is consistent across requests"""
        # Mock authenticated user
        with patch('server.api.auth.require_auth') as mock_auth:
            user_data = {
                'id': 'user123',
                'email': 'test@example.com',
                'name': 'Test User',
                'roles': ['attendee'],
                'is_admin': False,
                'is_host': False,
                'is_attendee': True,
            }
            mock_auth.return_value = user_data
            
            # Multiple requests should return consistent user data
            response1 = test_client.get("/users/me")
            response2 = test_client.get("/users/me")
            
            if response1.status_code == 200 and response2.status_code == 200:
                assert response1.json() == response2.json()