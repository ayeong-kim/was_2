import os

# .env 파일이 있으면 읽어서 환경변수로 등록 (클라우드에서 직접 넣은 환경변수가 우선)
_env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(_env_file):
    with open(_env_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())

WAS_HOST = os.environ.get("WAS_HOST", "127.0.0.1")                          # 클라우드: 0.0.0.0
WAS_PORT = int(os.environ.get("WAS_PORT", "8000"))

# MySQL (RDS) 접속 정보
DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")                            # RDS 엔드포인트
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_NAME = os.environ.get("DB_NAME", "petclinic")
DB_USER = os.environ.get("DB_USER", "petclinic_app")                        # 애플리케이션 전용 계정
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() == "true"  # HTTPS면 true
SESSION_HOURS = int(os.environ.get("SESSION_HOURS", "8"))                   # 로그인 유지 시간
SEED_PASSWORD = os.environ.get("SEED_PASSWORD", "")                         # 테스트 계정 비밀번호 (비우면 계정 안 만듦)
