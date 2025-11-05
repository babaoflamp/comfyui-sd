# ComfyUI 엔터프라이즈 통합

ComfyUI에 엔터프라이즈급 기능을 추가하는 통합 프로젝트입니다.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-GPL--3.0-green.svg)](LICENSE)
[![aiohttp](https://img.shields.io/badge/aiohttp-3.10+-orange.svg)](https://docs.aiohttp.org/)

## 📋 개요

이 프로젝트는 [ComfyUI](https://github.com/comfyanonymous/ComfyUI)를 위한 엔터프라이즈급 확장 기능을 제공합니다. ComfyUI는 강력한 노드 기반 Stable Diffusion 워크플로우 엔진이지만, 프로덕션 환경에서 필요한 인증, 문서화, 로깅 기능이 부족합니다. 이 프로젝트는 그러한 간극을 메웁니다.

### 주요 기능

- 🔐 **JWT 인증** - API 엔드포인트에 대한 토큰 기반 인증
- 📚 **API 문서화** - OpenAPI 3.0 명세 자동 생성 및 Swagger UI
- 📊 **향상된 로깅** - 구조화된 JSON 로깅, 파일 로테이션, 성능 메트릭

## 🚀 빠른 시작

### 사전 요구사항

- Python 3.9 이상
- ComfyUI 설치 (별도)
- Git

### 설치

```bash
# 저장소 클론
git clone https://github.com/babaoflamp/comfyui-sd.git
cd comfyui-sd

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
pip install PyJWT  # JWT 인증용
```

### 기본 사용법

```python
from aiohttp import web
from middleware.auth_middleware import AuthMiddleware, setup_auth_routes
from api_server.openapi_spec import setup_openapi_routes
from app.enhanced_logger import setup_enhanced_logger

# 로거 설정
logger = setup_enhanced_logger("myapp", level="INFO")

# 애플리케이션 생성
app = web.Application()

# 인증 미들웨어 추가
auth = AuthMiddleware(public_paths=['/health', '/api/auth/login'])
app.middlewares.append(auth.middleware_handler)

# 인증 및 문서화 라우트 설정
setup_auth_routes(app, auth)
setup_openapi_routes(app)

# 서버 실행
web.run_app(app, host='0.0.0.0', port=8188)
```

## 📦 모듈 상세

### 1. 인증 미들웨어 (`middleware/auth_middleware.py`)

JWT 기반 API 인증을 제공합니다.

**주요 구성요소:**
- `AuthConfig` - 인증 설정
- `AuthManager` - 토큰 생성 및 검증
- `AuthMiddleware` - aiohttp 미들웨어
- `@require_auth` - 라우트 보호 데코레이터

**사용 예제:**

```python
from middleware.auth_middleware import AuthMiddleware, require_auth
from aiohttp import web

# 보호된 엔드포인트
@require_auth
async def protected_route(request):
    user_id = request['user_id']
    return web.json_response({"message": f"안녕하세요, {user_id}님!"})

app.router.add_get('/api/protected', protected_route)
```

**API 사용:**

```bash
# 로그인
curl -X POST http://localhost:8188/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "password"}'

# 응답: {"token": "eyJhbG...", "user_id": "user", "token_type": "Bearer"}

# 인증된 요청
curl http://localhost:8188/api/protected \
  -H "Authorization: Bearer eyJhbG..."
```

### 2. OpenAPI 명세 (`api_server/openapi_spec.py`)

자동 API 문서화 기능을 제공합니다.

**주요 기능:**
- OpenAPI 3.0 명세 생성
- Swagger UI 통합
- ReDoc 통합

**사용 예제:**

```python
from api_server.openapi_spec import setup_openapi_routes

# 문서화 라우트 추가
setup_openapi_routes(app)
```

**접근 방법:**
- Swagger UI: http://localhost:8188/api/docs
- ReDoc: http://localhost:8188/api/redoc
- JSON 명세: http://localhost:8188/api/openapi.json

### 3. 향상된 로깅 (`app/enhanced_logger.py`)

구조화된 로깅 시스템을 제공합니다.

**주요 기능:**
- JSON 포맷 로깅
- 컬러 콘솔 출력
- 파일 로테이션
- 성능 메트릭 추적

**사용 예제:**

```python
from app.enhanced_logger import setup_enhanced_logger, LogContext
import logging

# 로거 설정
logger = setup_enhanced_logger(
    name="myapp",
    level=logging.INFO,
    log_file="/var/log/myapp/app.log",
    json_output=True
)

# 기본 로깅
logger.info("서버 시작", extra={"port": 8188, "mode": "production"})

# 컨텍스트 로깅
with LogContext(logger, "workflow_execution", workflow_id="wf_123"):
    logger.info("모델 로딩 중")
    # 작업 수행
    logger.info("실행 완료")
```

## 🔧 ComfyUI 통합

ComfyUI와 함께 사용하는 방법:

### 1. ComfyUI 설치

```bash
# ComfyUI 클론 (또는 기존 설치 사용)
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI
pip install -r requirements.txt
```

### 2. 모듈 통합

ComfyUI의 `server.py`에 다음 코드를 추가:

```python
# ComfyUI server.py 파일 상단에 추가
import sys
sys.path.insert(0, '/path/to/comfyui-sd')  # 이 프로젝트 경로

from middleware.auth_middleware import AuthMiddleware, setup_auth_routes
from api_server.openapi_spec import setup_openapi_routes
from app.enhanced_logger import setup_enhanced_logger

# 로거 설정
logger = setup_enhanced_logger("comfyui", level="INFO")

# 기존 app 생성 후
auth = AuthMiddleware(
    public_paths=['/', '/api/auth/login', '/api/docs']
)
app.middlewares.append(auth.middleware_handler)

# 라우트 설정
setup_auth_routes(app, auth)
setup_openapi_routes(app)
```

### 3. 선택적 인증 활성화

```python
from middleware.auth_middleware import AuthConfig

# 인증 설정
auth_config = AuthConfig(
    secret_key="your-production-secret-key",
    token_expiry_hours=24,
    require_auth=True  # 전역 인증 활성화
)

auth = AuthMiddleware(
    config=auth_config,
    public_paths=['/api/auth/login', '/api/docs']
)
```

## ⚙️ 설정

### 환경 변수

프로덕션 환경에서 권장하는 환경 변수:

```bash
# .env 파일
AUTH_SECRET_KEY=your-secure-random-secret-key-here
AUTH_TOKEN_EXPIRY_HOURS=24
AUTH_REQUIRE_AUTH=true

LOG_LEVEL=INFO
LOG_FILE=/var/log/comfyui/app.log
LOG_JSON_OUTPUT=true

SERVER_HOST=0.0.0.0
SERVER_PORT=8188
```

### 코드에서 환경 변수 사용

```python
import os
from middleware.auth_middleware import AuthConfig

config = AuthConfig(
    secret_key=os.getenv('AUTH_SECRET_KEY', 'dev-secret-key'),
    token_expiry_hours=int(os.getenv('AUTH_TOKEN_EXPIRY_HOURS', '24')),
    require_auth=os.getenv('AUTH_REQUIRE_AUTH', 'false').lower() == 'true'
)
```

## 🛡️ 보안 고려사항

### 프로덕션 체크리스트

- [ ] 강력한 시크릿 키 설정 (최소 32자)
- [ ] HTTPS/TLS 활성화
- [ ] 데이터베이스 기반 사용자 인증 구현
- [ ] 비밀번호 해싱 (bcrypt, argon2 등)
- [ ] CORS 정책 설정
- [ ] API 레이트 제한
- [ ] 입력 검증 및 새니타이제이션
- [ ] 보안 헤더 추가 (CSP, X-Frame-Options 등)
- [ ] 로그 모니터링 및 알림

### 보안 헤더 추가 예제

```python
async def security_headers_middleware(app, handler):
    async def middleware_handler(request):
        response = await handler(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000'
        return response
    return middleware_handler

app.middlewares.append(security_headers_middleware)
```

## 📚 추가 문서

- [CLAUDE.md](CLAUDE.md) - Claude Code 개발 가이드
- [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) - 구현 가이드 (상세)
- [PROJECT_ANALYSIS.md](PROJECT_ANALYSIS.md) - 프로젝트 분석

## 🧪 테스트

현재 자동화된 테스트는 없습니다. 테스트 추가 시:

```bash
# pytest 설치
pip install pytest pytest-asyncio pytest-aiohttp

# 테스트 실행
pytest tests/ -v

# 커버리지 포함
pytest tests/ --cov=. --cov-report=html
```

## 🤝 기여

기여를 환영합니다! 다음 단계를 따라주세요:

1. Fork the repository
2. 새 브랜치 생성 (`git checkout -b feature/amazing-feature`)
3. 변경사항 커밋 (`git commit -m 'Add amazing feature'`)
4. 브랜치에 Push (`git push origin feature/amazing-feature`)
5. Pull Request 생성

### 개발 가이드라인

- 코드는 ruff로 린팅 (`ruff check .`)
- print 대신 logging 사용
- 모든 함수에 타입 힌트 추가
- 비동기 함수는 `async def` 사용
- 의미 있는 커밋 메시지 작성

## 📄 라이센스

이 프로젝트는 [GPL-3.0 License](LICENSE) 하에 배포됩니다.

## 🔗 관련 프로젝트

- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) - 원본 ComfyUI 프로젝트
- [ComfyUI Frontend](https://github.com/Comfy-Org/ComfyUI_frontend) - ComfyUI 웹 프론트엔드
- [ComfyUI Desktop](https://github.com/Comfy-Org/desktop) - ComfyUI 데스크톱 애플리케이션

## 📞 지원

- 이슈: [GitHub Issues](https://github.com/babaoflamp/comfyui-sd/issues)
- ComfyUI Discord: https://comfy.org/discord
- ComfyUI 문서: https://docs.comfy.org/

## 🙏 감사의 말

- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) 팀에게 훌륭한 프로젝트를 만들어주셔서 감사합니다.
- aiohttp, PyJWT 등 오픈소스 커뮤니티에 감사드립니다.

---

**Made with ❤️ for the ComfyUI community**
