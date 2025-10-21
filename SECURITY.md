# Security Policy

## Overview

This document outlines the security measures implemented in the cashflow-scheduler application and provides guidance for secure deployment and operation.

## Security Features

### 1. API Security

#### CORS (Cross-Origin Resource Sharing)
- **Default:** Restrictive localhost-only origins for development
- **Production:** Must set `CORS_ORIGINS` environment variable with specific allowed origins
- **Credentials:** Disabled by default for security
- **Configuration:**
  ```bash
  export CORS_ORIGINS="https://your-domain.com,https://your-other-domain.com"
  ```

#### Rate Limiting
All API endpoints are rate-limited to prevent DoS attacks:
- `/solve`: 10 requests/minute
- `/set_eod`: 10 requests/minute
- `/export`: 20 requests/minute
- `/verify`: 30 requests/hour (verify service)

#### API Key Authentication (Optional)
API key authentication can be enabled for production deployments:

```bash
# Enable API authentication
export REQUIRE_API_KEY=true
export API_KEY=your-secret-api-key-here
```

When enabled, all requests must include the API key header:
```
X-API-Key: your-secret-api-key-here
```

#### Security Headers
All responses include the following security headers:
- `X-Frame-Options: DENY` - Prevents clickjacking
- `X-Content-Type-Options: nosniff` - Prevents MIME sniffing
- `X-XSS-Protection: 1; mode=block` - XSS protection
- `Content-Security-Policy: default-src 'self'` - Restricts resource loading
- `Referrer-Policy: strict-origin-when-cross-origin` - Controls referrer information
- `Strict-Transport-Security` - Enforces HTTPS (when using HTTPS)

### 2. Input Validation

#### Monetary Values
- Maximum amount: $10,000,000 (prevents integer overflow)
- Validation on all monetary inputs using `to_cents()` function
- Proper handling of Decimal precision

#### Request Parameters
- Day values: Must be in range 1-30
- EOD amounts: Must be within -$1,000,000 to $1,000,000
- Solver preference: Must be 'dp' or 'cpsat'
- Export format: Must be 'md', 'csv', or 'json'

#### Plan Data
- Actions: Must be exactly 30 elements
- Deposits/Bills: Validated day ranges and amounts
- JSON parsing with proper error handling

### 3. Path Traversal Protection

File loading includes protection against path traversal attacks:
- Resolves symlinks and relative paths
- Detects common traversal patterns (`../`, `/etc`, `/sys`)
- Optional directory restriction via `allowed_dir` parameter

### 4. Docker Security

#### Non-Root User
All Docker containers run as non-root user `appuser` (UID 1000):
- Limits potential damage from container escape
- Follows principle of least privilege

#### Minimal Image
- Uses `python:3.11-slim` base image
- Only installs necessary dependencies
- Removes package manager caches

### 5. Logging

Comprehensive logging for security monitoring:
- Invalid API key attempts
- JSON parsing errors
- Invalid input validation failures
- Unexpected errors with stack traces
- All logs include timestamps and severity levels

## Deployment Recommendations

### Required Configuration

1. **Set CORS Origins**
   ```bash
   export CORS_ORIGINS="https://yourdomain.com"
   ```

2. **Enable API Authentication (Production)**
   ```bash
   export REQUIRE_API_KEY=true
   export API_KEY=$(openssl rand -hex 32)  # Generate secure key
   ```

3. **Use HTTPS**
   - Always use HTTPS in production
   - Enables HSTS header automatically

### Optional But Recommended

4. **Set Up Monitoring**
   - Monitor rate limit violations
   - Track invalid authentication attempts
   - Set up alerts for unusual activity

5. **Regular Updates**
   ```bash
   pip install --upgrade pip-audit
   pip-audit  # Check for known vulnerabilities
   ```

6. **Environment Variables**
   Never commit secrets to version control:
   ```bash
   # .env file (add to .gitignore)
   API_KEY=your-secret-key
   CORS_ORIGINS=https://production-domain.com
   REQUIRE_API_KEY=true
   ```

## Security Best Practices

### For Developers

1. **Never Commit Secrets**
   - Use environment variables
   - Add `.env` to `.gitignore`
   - Use secret management tools (AWS Secrets Manager, etc.)

2. **Validate All Inputs**
   - Use type hints and Pydantic models
   - Validate ranges and formats
   - Sanitize user-provided data

3. **Keep Dependencies Updated**
   ```bash
   pip install --upgrade -r requirements.txt
   pip-audit
   ```

4. **Code Review**
   - Review security-sensitive changes carefully
   - Use automated security scanning in CI/CD

### For Operations

1. **Network Security**
   - Use firewalls to restrict access
   - Deploy behind reverse proxy (nginx, Traefik)
   - Use VPC/private networks when possible

2. **Secrets Management**
   - Rotate API keys regularly
   - Use secrets management tools
   - Never log secrets

3. **Monitoring**
   - Set up log aggregation (ELK, CloudWatch)
   - Monitor for suspicious patterns
   - Set up alerts for security events

4. **Backups**
   - Regular backups of plan data
   - Test restore procedures
   - Encrypt backups

## Known Limitations

1. **No User Management**
   - Single API key for all users
   - Consider adding OAuth2/JWT for multi-user scenarios

2. **No Request Size Limits**
   - Large payloads could consume memory
   - Consider adding middleware for max body size

3. **No WAF**
   - Consider using Web Application Firewall for production
   - AWS WAF, Cloudflare, etc.

## Vulnerability Reporting

If you discover a security vulnerability, please:

1. **Do NOT** open a public GitHub issue
2. Email the security team directly (configure this for your org)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Security Audit History

- **2025-10-21**: Initial security review and hardening
  - Added CORS restrictions
  - Implemented rate limiting
  - Added security headers
  - Improved input validation
  - Added integer overflow protection
  - Implemented API key authentication
  - Added path traversal protection
  - Docker security improvements (non-root user)

## Compliance

This application implements security controls aligned with:
- OWASP Top 10 mitigations
- CWE Top 25 protections
- Docker security best practices
- FastAPI security recommendations

## Additional Resources

- [OWASP API Security Project](https://owasp.org/www-project-api-security/)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)
