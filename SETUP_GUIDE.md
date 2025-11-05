# ComfyUI 엔터프라이즈 통합 설정 가이드

이 가이드는 ComfyUI에 엔터프라이즈 기능을 통합하는 방법을 단계별로 설명합니다.

## 📋 사전 요구사항

- Python 3.9 이상
- Git
- 8GB 이상의 RAM (ComfyUI 실행 시)
- GPU (선택사항, CPU로도 실행 가능하지만 느림)

## 🚀 설치 방법

### 1. 프로젝트 클론

```bash
git clone https://github.com/babaoflamp/comfyui-sd.git
cd comfyui-sd
```

### 2. ComfyUI 설치

```bash
# ComfyUI 클론
git clone https://github.com/comfyanonymous/ComfyUI.git

# ComfyUI-Manager 설치 (선택사항이지만 권장)
mkdir -p ComfyUI/custom_nodes
cd ComfyUI/custom_nodes
git clone https://github.com/ltdrdata/ComfyUI-Manager.git
cd ../..
```

### 3. 의존성 설치

```bash
# 가상환경 생성 (권장)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# ComfyUI 의존성 설치
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -r ComfyUI/requirements.txt

# 엔터프라이즈 모듈 의존성 설치
pip install -r requirements.txt
pip install PyJWT
```

**참고**: Python 3.8은 지원하지 않습니다. Python 3.9 이상을 사용해주세요.

### 4. 엔터프라이즈 통합 설정

엔터프라이즈 기능을 통합하는 방법은 두 가지가 있습니다:

#### 방법 A: Custom Node로 자동 통합 (권장)

ComfyUI의 custom_nodes에 심볼릭 링크를 생성합니다:

```bash
# Linux/Mac
ln -s $(pwd)/ComfyUI/custom_nodes/comfyui-enterprise-integration ComfyUI/custom_nodes/

# 또는 직접 생성되어 있는 파일 사용
# ComfyUI/custom_nodes/comfyui-enterprise-integration/__init__.py가 이미 존재합니다
```

이 방법을 사용하면 ComfyUI 시작 시 자동으로 엔터프라이즈 기능이 로드됩니다.

#### 방법 B: 통합 스크립트 사용

```bash
python run_integrated.py
```

## 🏃 실행

### 기본 실행

```bash
cd ComfyUI
python main.py
```

또는 프로젝트 루트에서:

```bash
python run_integrated.py
```

### 포트 변경

```bash
cd ComfyUI
python main.py --listen 0.0.0.0 --port 8188
```

### CPU 모드로 실행 (GPU 없을 때)

```bash
cd ComfyUI
python main.py --cpu
```

## 🌐 접속

서버가 시작되면 다음 주소로 접속할 수 있습니다:

- **ComfyUI 인터페이스**: http://localhost:8188/
- **Swagger API 문서**: http://localhost:8188/api/docs
- **ReDoc API 문서**: http://localhost:8188/api/redoc
- **OpenAPI JSON**: http://localhost:8188/api/openapi.json

## 🔐 인증 사용하기

### 환경 변수 설정

인증 기능을 활성화하려면 환경 변수를 설정합니다:

```bash
# Linux/Mac
export AUTH_SECRET_KEY="your-very-secret-key-here-change-this"
export AUTH_TOKEN_EXPIRY_HOURS="24"
export AUTH_REQUIRE_AUTH="true"

# Windows
set AUTH_SECRET_KEY=your-very-secret-key-here-change-this
set AUTH_TOKEN_EXPIRY_HOURS=24
set AUTH_REQUIRE_AUTH=true
```

또는 `.env` 파일을 생성합니다:

```bash
# .env 파일
AUTH_SECRET_KEY=your-very-secret-key-here-change-this
AUTH_TOKEN_EXPIRY_HOURS=24
AUTH_REQUIRE_AUTH=true

LOG_LEVEL=INFO
LOG_JSON_OUTPUT=false
```

### 로그인

```bash
curl -X POST http://localhost:8188/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "password"
  }'
```

**응답 예시**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": "admin",
  "token_type": "Bearer"
}
```

### 인증된 요청

```bash
curl -X GET http://localhost:8188/api/some_endpoint \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 📦 디렉토리 구조

```
comfyui-sd/
├── ComfyUI/                          # ComfyUI 메인 (git clone으로 설치)
│   └── custom_nodes/
│       ├── ComfyUI-Manager/          # 노드 관리자
│       └── comfyui-enterprise-integration/  # 우리의 통합 모듈
├── api_server/
│   └── openapi_spec.py               # OpenAPI 문서 생성
├── app/
│   └── enhanced_logger.py            # 향상된 로깅
├── middleware/
│   └── auth_middleware.py            # JWT 인증
├── run_integrated.py                 # 통합 실행 스크립트
├── requirements.txt                  # Python 의존성
└── README.md                         # 프로젝트 소개
```

## 🔧 문제 해결

### Python 버전 오류

```bash
ERROR: No matching distribution found for numpy>=1.25.0
```

**해결**: Python 3.9 이상을 사용해주세요.

```bash
python3.9 -m venv venv
source venv/bin/activate
```

### CUDA/GPU 오류

ComfyUI는 GPU가 있으면 자동으로 사용합니다. GPU가 없다면:

```bash
python main.py --cpu
```

### 프론트엔드 패키지 오류

```bash
ERROR: Could not find a version that satisfies the requirement comfyui-frontend-package
```

**해결**: requirements.txt에서 해당 라인을 주석 처리합니다:

```bash
#comfyui-frontend-package==1.28.8
#comfyui-workflow-templates==0.2.11
#comfyui-embedded-docs==0.3.1
```

### 포트 충돌

```bash
OSError: [Errno 98] Address already in use
```

**해결**: 다른 포트를 사용합니다:

```bash
python main.py --port 8189
```

## 📝 추가 설정

### 모델 경로 설정

ComfyUI는 `models/` 디렉토리에서 모델을 찾습니다. 다른 경로를 사용하려면:

```bash
# extra_model_paths.yaml 생성
cp ComfyUI/extra_model_paths.yaml.example ComfyUI/extra_model_paths.yaml

# 파일을 편집하여 모델 경로 추가
```

### 로그 설정

로그를 파일로 저장하려면:

```bash
export LOG_FILE="/var/log/comfyui/app.log"
export LOG_JSON_OUTPUT="true"
```

## 🎯 다음 단계

1. ComfyUI-Manager를 사용하여 커스텀 노드 설치
2. 모델 다운로드 및 설치
3. 워크플로우 작성 및 테스트
4. API 문서를 참고하여 프로그래밍 방식으로 사용

## 💡 유용한 링크

- [ComfyUI 공식 문서](https://docs.comfy.org/)
- [ComfyUI GitHub](https://github.com/comfyanonymous/ComfyUI)
- [ComfyUI-Manager](https://github.com/ltdrdata/ComfyUI-Manager)
- [예제 워크플로우](https://comfyanonymous.github.io/ComfyUI_examples/)

## 🆘 지원

문제가 발생하면:
- [GitHub Issues](https://github.com/babaoflamp/comfyui-sd/issues)에 문의
- ComfyUI Discord: https://comfy.org/discord
