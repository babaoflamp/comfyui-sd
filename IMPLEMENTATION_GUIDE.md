# ComfyUI 확장 기능 구현 가이드

**작성일**: 2025년 10월 31일
**버전**: 1.0.0

## 📋 개요

이 가이드는 ComfyUI에 추가된 3가지 새로운 모듈을 통합하는 방법을 설명합니다.

### 추가된 기능

1. **인증 미들웨어** (`middleware/auth_middleware.py`)
   - JWT 기반 토큰 인증
   - 로그인/로그아웃 엔드포인트
   - 역할 기반 접근 제어 (RBAC) 지원

2. **API 문서화** (`api_server/openapi_spec.py`)
   - OpenAPI 3.0 자동 생성
   - Swagger UI 통합
   - ReDoc 통합

3. **향상된 로깅** (`app/enhanced_logger.py`)
   - 구조화된 JSON 로깅
   - 파일 로테이션
   - 성능 메트릭 추적

---

## 🔐 1. 인증 시스템 구현

### 1.1 기본 설정

```python
from middleware.auth_middleware import AuthMiddleware, AuthConfig

# 인증 설정
auth_config = AuthConfig(
    secret_key="your-secret-key",  # 프로덕션에서는 환경변수 사용
    algorithm="HS256",
    token_expiry_hours=24,
    require_auth=True  # 전역 인증 요구
)

# 미들웨어 생성
auth_middleware = AuthMiddleware(
    config=auth_config,
    public_paths=['/health', '/api/auth/login', '/']
)
```

### 1.2 서버 통합

```python
# server.py에서
from aiohttp import web
from middleware.auth_middleware import AuthMiddleware, setup_auth_routes

async def create_app():
    app = web.Application()

    # 인증 미들웨어 추가
    auth_middleware = AuthMiddleware()
    app.middlewares.append(auth_middleware.middleware_handler)

    # 인증 라우트 설정
    setup_auth_routes(app, auth_middleware)

    # 기타 라우트 추가...

    return app
```

### 1.3 보호된 라우트 생성

```python
from middleware.auth_middleware import require_auth
from aiohttp import web

@require_auth
async def protected_endpoint(request):
    """
    인증이 필요한 엔드포인트
    """
    user_id = request.get('user_id')
    return web.json_response({
        'message': f'Hello {user_id}!',
        'auth_payload': request.get('auth_payload')
    })

# 라우트 추가
app.router.add_get('/api/protected', protected_endpoint)
```

### 1.4 토큰 사용

```bash
# 1. 로그인
curl -X POST http://localhost:8188/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "password"
  }'

# 응답:
# {
#   "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "user_id": "user@example.com",
#   "token_type": "Bearer"
# }

# 2. 인증된 요청 수행
curl -X GET http://localhost:8188/api/protected \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# 3. 로그아웃
curl -X POST http://localhost:8188/api/auth/logout \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 1.5 고급 설정

#### 커스텀 검증

```python
async def custom_login(request):
    """
    커스텀 로그인 로직
    """
    data = await request.json()
    username = data.get('username')
    password = data.get('password')

    # 데이터베이스에서 사용자 확인
    user = await verify_user(username, password)
    if not user:
        return web.json_response(
            {'error': 'Invalid credentials'},
            status=401
        )

    # 토큰 생성
    auth_manager = request.app['auth_manager']
    token = auth_manager.generate_token(
        user_id=username,
        roles=user.get('roles', []),
        email=user.get('email')
    )

    return web.json_response({
        'token': token,
        'user': user
    })
```

#### 역할 기반 접근 제어 (RBAC)

```python
def require_role(*roles):
    """
    특정 역할이 필요한 엔드포인트 데코레이터
    """
    def decorator(f):
        @wraps(f)
        async def decorated(request, *args, **kwargs):
            if 'user_id' not in request:
                return web.json_response(
                    {'error': 'Unauthorized'},
                    status=401
                )

            user_roles = request.get('auth_payload', {}).get('roles', [])
            if not any(role in user_roles for role in roles):
                return web.json_response(
                    {'error': 'Forbidden'},
                    status=403
                )

            return await f(request, *args, **kwargs)
        return decorated
    return decorator

# 사용 예
@require_role('admin', 'moderator')
async def admin_endpoint(request):
    return web.json_response({'message': 'Admin only'})
```

---

## 📚 2. API 문서화 구현

### 2.1 기본 설정

```python
from api_server.openapi_spec import setup_openapi_routes

# server.py에서
app = web.Application()

# OpenAPI 라우트 설정
setup_openapi_routes(app)
```

### 2.2 문서 접근

```
Swagger UI:  http://localhost:8188/api/docs
ReDoc:       http://localhost:8188/api/redoc
OpenAPI JSON: http://localhost:8188/api/openapi.json
```

### 2.3 커스텀 스키마 추가

```python
from api_server.openapi_spec import get_openapi_spec

spec = get_openapi_spec()

# 새 엔드포인트 추가
spec['paths']['/api/custom'] = {
    'get': {
        'tags': ['Custom'],
        'summary': 'Custom endpoint',
        'operationId': 'getCustom',
        'responses': {
            '200': {
                'description': 'Success',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'result': {'type': 'string'}
                            }
                        }
                    }
                }
            }
        }
    }
}
```

### 2.4 인증 요구사항 표시

```python
# OpenAPI 스키마에서
'security': [
    {'bearerAuth': []}  # JWT 토큰 필요
]

# 클라이언트는 다음과 같이 사용:
# Authorization: Bearer <token>
```

---

## 📊 3. 향상된 로깅 구현

### 3.1 기본 설정

```python
from app.enhanced_logger import setup_enhanced_logger

# 로거 생성
logger = setup_enhanced_logger(
    name="comfyui",
    level=logging.INFO,
    log_file="/var/log/comfyui/app.log",
    json_output=True,  # JSON 형식
    use_colors=True    # 콘솔 컬러
)
```

### 3.2 기본 로깅

```python
import logging

logger = logging.getLogger("comfyui")

# 기본 메시지
logger.info("Server started")
logger.warning("Low memory")
logger.error("Database connection failed")

# 추가 정보 포함
logger.info(
    "User logged in",
    extra={
        "user_id": "user123",
        "login_time": "2025-10-31T14:20:00Z",
        "ip": "192.168.1.100"
    }
)
```

### 3.3 컨텍스트 로깅

```python
from app.enhanced_logger import LogContext

# 컨텍스트와 함께 로깅
with LogContext(logger, "workflow_execution", workflow_id="wf_123"):
    logger.info("Loading model")
    # ... 작업 수행
    logger.info("Execution completed")

# 로그 출력:
# 2025-10-31T14:20:00Z [INFO] Starting workflow_execution (operation=workflow_execution, workflow_id=wf_123)
# 2025-10-31T14:20:02Z [INFO] Loading model (operation=workflow_execution, workflow_id=wf_123)
# 2025-10-31T14:20:05Z [INFO] Completed workflow_execution (operation=workflow_execution, workflow_id=wf_123, duration_sec=5.0)
```

### 3.4 성능 메트릭

```python
from app.enhanced_logger import MetricsLogger

metrics = MetricsLogger(logger)

# 메트릭 기록
start_time = time.time()
# ... 작업 수행
duration = (time.time() - start_time) * 1000
metrics.record_execution_time("inference", duration)

# 메모리 사용
import psutil
memory = psutil.virtual_memory().used
metrics.record_metric("memory_usage", memory / 1024 / 1024, "MB")

# 메트릭 로깅
metrics.log_metrics()
```

### 3.5 JSON 로깅 예제

```python
logger = setup_enhanced_logger(
    json_output=True  # JSON 형식 활성화
)

logger.info("API request received")

# 출력:
# {
#   "timestamp": "2025-10-31T14:20:00.000Z",
#   "level": "INFO",
#   "logger": "comfyui",
#   "message": "API request received",
#   "module": "server",
#   "function": "handle_request",
#   "line": 123
# }
```

---

## 🔄 통합 예제

### 완전한 보안 API 서버

```python
from aiohttp import web
from middleware.auth_middleware import (
    AuthMiddleware, AuthConfig, setup_auth_routes
)
from api_server.openapi_spec import setup_openapi_routes
from app.enhanced_logger import setup_enhanced_logger
import logging

# 로거 설정
logger = setup_enhanced_logger(
    level=logging.INFO,
    log_file="/var/log/comfyui/app.log",
    json_output=True
)

# 인증 설정
auth_config = AuthConfig(
    secret_key="your-production-secret-key",
    token_expiry_hours=24,
    require_auth=False  # 선택적 인증
)

auth_middleware = AuthMiddleware(
    config=auth_config,
    public_paths=['/health', '/api/auth/login', '/api/docs']
)

async def init_app():
    app = web.Application()

    # 미들웨어 추가
    app.middlewares.append(auth_middleware.middleware_handler)

    # API 문서화 설정
    setup_openapi_routes(app)

    # 인증 라우트 설정
    setup_auth_routes(app, auth_middleware)

    # 커스텀 라우트
    async def health_check(request):
        logger.info("Health check")
        return web.json_response({"status": "healthy"})

    app.router.add_get('/health', health_check)

    return app

if __name__ == '__main__':
    app = init_app()
    logger.info("Starting ComfyUI server", extra={
        "version": "0.3.67",
        "port": 8188
    })
    web.run_app(app, host='127.0.0.1', port=8188)
```

---

## 🚀 배포 체크리스트

### 프로덕션 배포 전

- [ ] 프로덕션 시크릿 키 설정
- [ ] HTTPS/TLS 활성화
- [ ] 데이터베이스 사용자 검증 구현
- [ ] 로그 수집 시스템 연결
- [ ] 모니터링 설정
- [ ] 백업 전략 수립
- [ ] API 레이트 제한 추가
- [ ] CORS 정책 설정
- [ ] 보안 헤더 추가

### 보안 고려사항

```python
# HTTPS 강제
from aiohttp_security import setup as setup_security
from aiohttp_security import remember, forget

# CORS 설정
from aiohttp_cors import setup as setup_cors

cors = setup_cors(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*"
    )
})

# 보안 헤더
async def add_security_headers(app, handler):
    async def middleware_handler(request):
        response = await handler(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response
    return middleware_handler

app.middlewares.append(add_security_headers)
```

---

## 📖 참고 자료

### 공식 문서
- [aiohttp 문서](https://docs.aiohttp.org/)
- [JWT 토큰](https://jwt.io/)
- [OpenAPI 3.0](https://spec.openapis.org/oas/v3.0.0)
- [Swagger UI](https://swagger.io/tools/swagger-ui/)

### 보안 리소스
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [NIST 가이드](https://www.nist.gov/)

---

## 🆘 문제 해결

### JWT 토큰 문제

**문제**: "Invalid token"
```
해결:
1. 시크릿 키가 동일한지 확인
2. 토큰 만료 시간 확인
3. 토큰 형식 확인 (Bearer prefix)
```

### 로깅 문제

**문제**: 로그 파일이 생성되지 않음
```python
# 디렉토리 권한 확인
import os
log_dir = "/var/log/comfyui"
os.makedirs(log_dir, mode=0o755, exist_ok=True)

# 권한 확인
os.chmod(log_dir, 0o755)
```

### API 문서 문제

**문제**: Swagger UI가 로드되지 않음
```
해결:
1. /api/docs 엔드포인트 접근 확인
2. CDN 연결 확인 (cdn.jsdelivr.net)
3. 브라우저 캐시 초기화
```

---

## 📝 라이센스

이 구현 가이드와 추가된 모듈은 ComfyUI와 동일한 GPL-3.0 라이센스를 따릅니다.
