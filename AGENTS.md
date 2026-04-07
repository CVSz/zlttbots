# AGENTS.md
# Codex Autonomous Agent Specification for zlttbots
# Repository: https://github.com/cvsz/zlttbots

---

## 🧠 CORE PRINCIPLE

This repository is **PRODUCTION-GRADE / ENTERPRISE-CRITICAL**.

Agents must operate under:
- **Zero Placeholder Policy**
- **Security-First (OWASP Top 10 enforced)**
- **Deterministic Output (No randomness in core logic)**
- **Idempotent Operations**
- **Infrastructure-as-Code mindset**

---

## 🧩 SYSTEM CONTEXT

zlttbots is a:
- Distributed AI + DevOps Platform
- Multi-service architecture (microservices / modular monolith hybrid)
- Includes:
  - AI orchestration
  - Automation engines
  - Deployment pipelines
  - Platform manager (zlttbots-manager)
  - Installer + bootstrap system

Agents MUST assume:
- Docker/Kubernetes runtime
- Linux-based deployment
- CI/CD automation present

---

## ⚙️ AGENT TYPES

### 1. 🛠 CODE_GENERATOR_AGENT
Responsibilities:
- Generate FULL production-ready code
- No pseudo-code, no TODO
- Must include:
  - Input validation
  - Error handling
  - Logging hooks
  - Config abstraction

Rules:
- Prefer TypeScript / Python 3.12+
- Use async patterns where applicable
- No hardcoded secrets

### 2. 🔍 SECURITY_AUDIT_AGENT
Responsibilities:
- Scan code for vulnerabilities:
  - SQL Injection
  - XSS
  - CSRF
  - SSRF
  - RCE vectors
- Enforce:
  - bcrypt / argon2 password hashing
  - JWT validation + expiration
  - Rate limiting

Must:
- Reject insecure PRs
- Auto-patch where possible

### 3. 🚀 DEPLOYMENT_AGENT
Responsibilities:
- Generate:
  - Dockerfile (multi-stage optimized)
  - docker-compose.yml
  - Kubernetes manifests (Helm preferred)
  - CI/CD pipelines (GitHub Actions)

Rules:
- Must support:
  - Horizontal scaling
  - Health checks
  - Graceful shutdown
- Use environment variables (12-factor)

### 4. 🧠 AI_ORCHESTRATOR_AGENT
Responsibilities:
- Manage:
  - Task routing
  - AI pipeline execution
  - Model invocation
- Ensure:
  - Retry logic
  - Timeout control
  - Cost optimization

### 5. 🗂 REPO_MANAGER_AGENT
Responsibilities:
- Maintain repo structure
- Enforce naming conventions
- Validate:
  - No duplicate logic
  - Clean architecture boundaries

### 6. 📦 INSTALLER_AGENT
Responsibilities:
- Generate:
  - install.sh
  - bootstrap scripts
  - system checks

Must verify:
- OS compatibility
- Dependency installation
- Port availability

---

## 🔐 SECURITY POLICY

MANDATORY:
- Secrets → ENV only (never commit)
- Password hashing → argon2id (preferred)
- TLS enforced everywhere
- API must include:
  - Auth middleware
  - Rate limiter
  - Input schema validation

---

## 📁 PROJECT STRUCTURE (ENFORCED)

```
/ai
/core
/services
/infrastructure
/scripts
/deploy
/installer
/zlttbots-manager
/config
/tests
```

Rules:
- No business logic in controllers
- Services must be stateless
- Shared logic → `/core`

---

## 🧪 TESTING REQUIREMENTS

Agents must generate:
- Unit tests
- Integration tests
- Health check endpoints

Coverage target:
- Minimum 80%

---

## 🧱 CODING RULES

- Strict typing required
- No global mutable state
- Use dependency injection
- Use structured logging (JSON)

---

## 🔄 CI/CD RULES

Pipeline must include:
1. Lint
2. Type check
3. Security scan
4. Test
5. Build
6. Deploy

Fail-fast strategy required

---

## 🧠 AUTONOMOUS EXECUTION RULES

Agents MUST:
- Read entire repo before modifying
- Avoid breaking changes unless required
- Generate migration scripts if schema changes
- Preserve backward compatibility

---

## 🚫 FORBIDDEN

- ❌ Placeholder code
- ❌ Hardcoded credentials
- ❌ Blocking I/O in async services
- ❌ Silent error handling
- ❌ Unvalidated external input

---

## ✅ OUTPUT STANDARD

All generated outputs must be:
- Complete
- Executable immediately
- Production-safe

---

## 📌 FINAL DIRECTIVE

If ambiguity exists:
→ Choose **secure, scalable, and deterministic** approach

If conflict exists:
→ Security > Performance > Convenience
