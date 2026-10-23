# 동물병원 WAS

FastAPI + MySQL(RDS) 기반 동물병원 접수·진료 WAS입니다.
데스크(간호사)용 기능과 수의사용 기능을 각각 별도 프로세스에서 처리하고, 프로세스 안에서는 비동기로 여러 요청을 동시에 처리합니다.

## 실행

```bash
pip install -r requirements.txt
python start.py
```

- 주소: `http://127.0.0.1:8000` (Swagger 문서: `/docs`)
- 실행 전에 MySQL에 데이터베이스(`petclinic`), 테이블, 앱 계정이 있어야 합니다(아래 "DB 준비"). WAS는 테이블을 만들지 않습니다.
- `reload`는 끄고 실행합니다. 켜면 uvicorn이 서버를 다른 프로세스에서 다시 import해서 Pipe가 워커와 끊깁니다.
- 코드를 고친 뒤에는 서버를 직접 다시 실행해야 합니다.

### 설정 (환경변수)

설정값은 [config.py](config.py)에서 환경변수로 읽습니다. 로컬에서는 `.env.example`을 `.env`로 복사해서 고치면 되고, 클라우드에서는 환경변수로 직접 넣으면 됩니다(같은 값이 둘 다 있으면 환경변수가 우선). 아무것도 없으면 아래 기본값으로 실행합니다.

| 이름 | 기본값 | 설명 |
|---|---|---|
| `WAS_HOST` | `127.0.0.1` | 서버 주소. 클라우드(컨테이너/VM)는 `0.0.0.0` |
| `WAS_PORT` | `8000` | 서버 포트 |
| `DB_HOST` | `127.0.0.1` | MySQL 주소 (RDS 엔드포인트) |
| `DB_PORT` | `3306` | MySQL 포트 |
| `DB_NAME` | `petclinic` | 데이터베이스 이름 |
| `DB_USER` | `petclinic_app` | 애플리케이션 전용 계정 |
| `DB_PASSWORD` | (없음) | 계정 비밀번호 — `.env` 또는 환경변수로만, 저장소에 올리지 않음 |
| `DB_POOL_SIZE` | `5` | 프로세스당 DB 연결 수. 프로세스가 3개라 WAS 1대 = 15개, 2대 = 30개 (RDS `max_connections`보다 작게) |
| `COOKIE_SECURE` | `false` | HTTPS로 서비스하면 `true` (세션 쿠키를 HTTPS에서만 전송). HTTP에서 `true`면 로그인이 유지되지 않음 |
| `SESSION_HOURS` | `8` | 로그인 유지 시간(시간) |
| `SEED_PASSWORD` | (없음) | 값이 있으면 시작할 때 테스트 계정을 이 비밀번호로 만듦. 비우면 만들지 않음 |

- `.env`는 `.gitignore`에 들어 있어서 저장소에 올라가지 않습니다.
- 세션도 DB에 저장하므로, 모든 WAS가 같은 MySQL을 쓰면 WAS를 여러 대로 늘려도 로그인이 유지됩니다.
- Auto Scaling용 AMI를 만들 때는 `DB_PASSWORD`를 AMI에 넣지 말고, 사용자 데이터나 SSM Parameter Store에서 환경변수로 넣으세요.

### DB 준비 (MySQL 8.0 / RDS)

RDS 파라미터 그룹: `time_zone=Asia/Seoul`, `character_set_server=utf8mb4`, `collation_server=utf8mb4_0900_ai_ci`.
앱도 연결할 때 `time_zone='+09:00'`으로 맞추므로 시각은 한국 시간으로 저장됩니다.

**1. 테이블 생성 (admin 계정, 한 번만)**: [schema.sql](schema.sql)에 데이터베이스와 테이블 5개가 있습니다.
```bash
mysql -h <RDS 엔드포인트> -u admin -p < schema.sql
```

**2. WAS 전용 계정 (최소 권한: CRUD만)**
```sql
CREATE USER 'petclinic_app'@'10.0.2%.%' IDENTIFIED BY '<비밀번호>';
GRANT SELECT, INSERT, UPDATE, DELETE ON petclinic.* TO 'petclinic_app'@'10.0.2%.%';
```
- `10.0.2%.%`는 WAS 서브넷(10.0.21.x, 10.0.22.x)만 허용합니다.
- WAS는 테이블 생성·변경(CREATE/ALTER/DROP)을 하지 않으므로 그 권한이 필요 없습니다. 테이블 구조를 바꿀 때는 admin 계정으로 합니다.
- 시작할 때 하는 일은 테스트 계정 넣기(`INSERT IGNORE`, `SEED_PASSWORD`가 있을 때만)뿐이라 INSERT 권한이면 충분합니다.

### 테스트 계정

`SEED_PASSWORD`가 설정되어 있을 때만, 서버를 시작하면서 없는 아이디를 추가합니다(이미 있는 계정은 그대로 둡니다). 비밀번호는 모두 `SEED_PASSWORD` 값입니다.

이미 만든 계정의 비밀번호를 바꿀 때는 DB에서 직접 바꿉니다.

```sql
-- 해시: python3 -c "import hashlib; print(hashlib.sha256(b'새비밀번호').hexdigest())"
UPDATE User SET password = '<해시>' WHERE login_id = 'desk1';
DELETE FROM Session WHERE uid = (SELECT uid FROM User WHERE login_id = 'desk1');   -- 기존 로그인 끊기
```

| 지점 | 데스크 | 수의사 |
|---|---|---|
| 강남점 | desk1 (김간호) | vet1 (이수의), vet2 (박수의) |
| 홍대점 | desk2 (최간호) | vet3 (정수의), vet4 (한수의) |
| 서초점 | desk3 (윤간호) | vet5 (강수의), vet6 (조수의) |
| 잠실점 | desk4 (임간호) | vet7 (신수의), vet8 (오수의) |
| 분당점 | desk5 (서간호) | vet9 (권수의), vet10 (황수의) |

## 구조

```
main 프로세스 ─ login_router → LoginControllers → UserService → UserRepository
     │                                                        └ SessionRepository
     │
     ├─ Pipe ─ desk 프로세스 ─ desk_router → DeskControllers → OwnerService        → OwnerRepository
     │                                                      ├ PetService          → PetRepository
     │                                                      ├ ConsultationService → ConsultationRepository
     │                                                      └ UserService         → UserRepository
     │
     └─ Pipe ─ vet 프로세스 ─ vet_router → VetControllers → ConsultationService → ConsultationRepository
```

- 라우터는 main 프로세스에서 요청을 받아 `(요청 id, 메서드 이름, 인자)`를 Pipe로 보냅니다.
- 워커 프로세스는 받은 요청마다 asyncio task를 만들어 동시에 처리하고, `(요청 id, 결과)`를 돌려보냅니다.
- DB 작업은 별도 스레드에서 실행합니다. 그래서 한 요청이 DB를 기다리는 동안 같은 프로세스에서 다른 요청을 처리할 수 있습니다.
- 워커에서 예외가 나면 워커는 계속 살아 있고, 예외는 main으로 전달되어 500으로 응답합니다.
- 워커 프로세스가 죽으면 그 프로세스로 가는 요청은 멈추지 않고 바로 에러로 끝납니다.
- 주인 등록, 동물 추가는 트랜잭션으로 묶여 있어서, 중간에 실패하면 모두 취소됩니다.

```
start.py                    서버 시작 (테스트 계정 → 워커 실행 → uvicorn)
schema.sql                  테이블 생성 SQL (클라우드에서 admin 계정으로 실행)
process.py                  워커 프로세스, Pipe 통신(Channel)
routers/                    라우터, 세션 확인
routers/datamodels/         요청·응답 모델 (pydantic)
controllers/                프로세스별 컨트롤러
services/                   서비스
repositorys/                레포지토리, DB 연결·트랜잭션
```

- DB 연결: 프로세스마다 DB 작업 스레드 `DB_POOL_SIZE`개, 스레드마다 연결 1개를 계속 씁니다(처음 쓸 때 연결, 끊겼으면 다시 연결). 트랜잭션(보호자+동물 등록)은 한 스레드·한 연결 안에서 끝납니다.
- 연결은 autocommit이라 SQL마다 바로 확정되고, 트랜잭션만 `BEGIN`~`COMMIT`으로 묶습니다. 30초 넘게 안 쓴 연결만 `ping`으로 확인합니다.
- RDS 장애 조치 직후에는 최근에 쓴 연결로 보낸 요청이 스레드당 1건 에러(500)가 날 수 있고, 그 연결은 버리고 다음 요청부터 새로 연결합니다.
- RDS 장애 조치로 응답이 없는 연결은 20초(`read_timeout`) 뒤 끊고 다시 연결합니다. 웹 서버의 `WAS_TIMEOUT`(30초)보다 짧아야 합니다.
- 워커(desk/vet)가 죽으면 main도 종료합니다. systemd에서 `Restart=always`(예: `RestartSec=3`)로 실행해야 WAS 전체가 다시 시작됩니다. `on-failure`는 SIGTERM 종료를 정상 종료로 봐서 재시작하지 않습니다.

## DB

| 테이블 | 컬럼 |
|---|---|
| User | uid, login_id(UNIQUE, 대소문자 구분), password(sha256), name, role(`desk`/`vet`), branch |
| Session | session_id(쿠키 값), uid → User, created_at |
| Owner | oid, oname, pnum, address, branch(등록한 지점) |
| Pet | pid, oid → Owner, pname, gender, age, weight, type, breed, notes |
| Consultation | cid, pid → Pet, vet_uid → User, date(등록 시각 자동), purpose, diagnosis, status(`대기`/`진료중`/`종료`) |

- 타입은 ERD와 같습니다(VARCHAR 길이, `weight DECIMAL(5,2)`, 날짜 `DATETIME`). 길이·범위를 넘는 입력은 요청 단계에서 422로 막습니다.
- 방문 등록부터 진료 종료까지가 `Consultation`의 한 행입니다.
- 보호자는 등록한 간호사의 지점(`branch`)으로 저장됩니다. 동물과 진료는 보호자를 통해 지점이 정해집니다.
- 다른 지점의 보호자·동물·진료 이력은 조회·수정·방문 등록이 모두 안 됩니다(404). 같은 손님이 두 지점을 다니면 지점마다 따로 등록합니다.

## 인증

- `POST /login`에 성공하면 `session_id` 쿠키(httponly)가 생깁니다. 이후 요청에는 이 쿠키를 같이 보내야 합니다.
- `/desk/*`는 desk 계정만, `/vet/*`는 vet 계정만 호출할 수 있습니다. 아니면 401입니다.
- 세션은 DB `Session` 테이블에 저장합니다. 로그인하면 행이 생기고 로그아웃하면 지워집니다. WAS를 재시작해도 로그인이 유지됩니다.
- 요청마다 쿠키의 `session_id`로 `Session` ↔ `User`를 조회해서 사용자와 권한을 확인합니다.
- 세션은 `SESSION_HOURS`(기본 8시간)가 지나면 만료되어 401이 됩니다. 쿠키도 같은 시간 뒤에 사라지고, 만료된 행은 다음 로그인 때 정리됩니다.
- 로그인 후 홈 이동, 로그아웃 후 로그인 페이지 이동은 클라이언트가 응답의 `role`을 보고 처리합니다.

## 공통 응답 코드

| 코드 | 의미 |
|---|---|
| 200 | 성공 |
| 401 | 로그인 실패, 세션 없음, 권한 다름 |
| 404 | 대상이 없음, 또는 규칙에 맞지 않음 (남의 진료, 진료 순서 위반, 다른 지점 의사 배정 등) |
| 422 | 요청 형식 오류 (필수 값 누락·null, 동물 0마리 등) |
| 500 | 서버 내부 오류 |

## 데이터 모델

**User**
```json
{ "uid": 1, "name": "김간호", "role": "desk", "branch": "강남점" }
```

**Pet**
```json
{ "pid": 1, "pname": "코코", "gender": "수", "age": 2, "weight": "3.5",
  "type": "개", "breed": null, "notes": null }
```
- `weight`는 Decimal이라 응답에서 문자열로 나옵니다. 요청에는 숫자와 문자열 모두 쓸 수 있습니다.

**Owner**
```json
{ "oid": 1, "oname": "김민주", "pnum": "010-1234-5678", "address": "서울",
  "pets": [ Pet, ... ], "active_pids": [1] }
```
- `active_pids`: 진료가 끝나지 않은(`대기`·`진료중`) 동물 id. 웹은 이 값으로 방문 등록 버튼을 막습니다(진료 이력을 동물마다 따로 조회하지 않음).

**Consultation**
```json
{ "cid": 1, "pid": 1, "pname": "코코", "vet_uid": 2, "vet_name": "이수의",
  "date": "2026-10-19 14:30:00", "purpose": "기침", "diagnosis": null, "status": "대기" }
```

**ConsultationDetail**: Consultation + `"pet": Pet`

## API

### 로그인 (main 프로세스)

| 메서드 | 경로 | 기능 | 요청 | 응답 |
|---|---|---|---|---|
| POST | `/login` | 아이디·비밀번호 확인 → 세션 생성 | `{ "login_id", "password" }` | User + 쿠키 |
| DELETE | `/login` | 로그아웃, 세션 삭제 | - | `null` |

### 데스크 (desk 프로세스, desk 계정)

| 메서드 | 경로 | 기능 | 요청 | 응답 |
|---|---|---|---|---|
| POST | `/desk/owner` | 주인 + 동물(1마리 이상) 등록 | `{ "oname", "pnum", "address"?, "pets": [PetRequest, ...] }` | Owner |
| GET | `/desk/owner/{owner_id}` | 주인, 동물 정보 보기 | - | Owner |
| GET | `/desk/owner?name=` | 주인 이름 검색 (앞부분 일치, 최근 등록순. 이름을 비우면 최근 등록 20명만) | - | [Owner] |
| PATCH | `/desk/owner/{owner_id}` | 주인 정보 수정 | `{ "oname"?, "pnum"?, "address"? }` | Owner |
| GET | `/desk/pet/{pet_id}` | 동물 상세 | - | Pet |
| PATCH | `/desk/pet/{pet_id}` | 동물 정보 수정 | PetRequest의 필드 중 일부 | Pet |
| POST | `/desk/pet` | 기존 주인에 동물(1마리 이상) 추가 | `{ "oid", "pets": [PetRequest, ...] }` | Owner (갱신된 전체) |
| POST | `/desk/pet/{pet_id}/consultation` | 방문 등록 (상태 `대기`) | `{ "vet_uid", "purpose" }` | Consultation |
| GET | `/desk/pet/{pet_id}/consultation` | 진료 이력 (최신순) | - | [Consultation] |
| GET | `/desk/vets` | 로그인한 간호사와 같은 지점의 수의사 목록 | - | [User] |

- **PetRequest:** `{ "pname", "type", "gender"?, "age"?, "weight"?, "breed"?, "notes"? }` (`?`는 생략 가능)
- **PATCH:** 보낸 필드만 수정합니다. 선택 항목(`address`, `gender`, `age`, `weight`, `breed`, `notes`)은 `null`로 비울 수 있습니다. 필수 항목(`oname`, `pnum`, `pname`, `type`)에 `null`을 보내면 422입니다.
- **지점:** 모든 데스크 API는 로그인한 간호사 지점의 데이터만 다룹니다. 다른 지점 데이터는 없는 것과 같이 404(검색·이력은 빈 목록)입니다.
- **방문 등록:** 같은 지점 수의사(`vet_uid`)만 배정할 수 있고, 아니면 404입니다. 날짜는 서버가 등록 시각으로 저장합니다.
- **동물 삭제 기능은 없습니다.**

### 수의사 (vet 프로세스, vet 계정)

| 메서드 | 경로 | 기능 | 요청 | 응답 |
|---|---|---|---|---|
| GET | `/vet/consultation` | 나에게 배정된 `대기`·`진료중` 목록 (등록순) | - | [Consultation] |
| PATCH | `/vet/consultation/{consultation_id}/start` | 진료 시작 (`대기` → `진료중`) | - | ConsultationDetail |
| GET | `/vet/consultation/{consultation_id}` | 현재 진료 정보 (동물 정보 포함) | - | ConsultationDetail |
| GET | `/vet/consultation/history/{pet_id}` | 동물의 진료 이력 (최신순) | - | [Consultation] |
| PATCH | `/vet/consultation/{consultation_id}` | 진단 작성 (`진료중`일 때만, 여러 번 수정 가능) | `{ "diagnosis" }` | ConsultationDetail |
| PATCH | `/vet/consultation/{consultation_id}/end` | 진료 종료 (`진료중` → `종료`) | - | ConsultationDetail |

- 자기에게 배정된 진료만 보고 바꿀 수 있습니다. 남의 진료나 순서에 맞지 않는 요청은 404입니다.
- 진료 이력(`/vet/consultation/history/{pet_id}`)은 자기 지점 동물만 조회됩니다.
- 목록의 맨 위 건만 시작하도록 강제하지는 않습니다. 순서는 클라이언트가 지킵니다.

## 원래 명세와 다른 점

- 명세는 지점 구분을 의사 배정에만 쓰지만, 보호자 명단이 지점 간에 공유되지 않도록 보호자를 지점별로 나눴습니다.
- 경로 앞에 `/login`, `/desk`, `/vet` prefix가 붙습니다.
- 명세의 `PATCH /pet{pet_id}`는 `PATCH /desk/pet/{pet_id}`로 구현했습니다(오타로 판단).
- 로그인 페이지 보여주기(`GET /`)와 동물 삭제(`DELETE /pet/{pet_id}`)는 없습니다.
- 방문 날짜는 입력받지 않고 서버가 자동으로 저장합니다.
- `User`에 `name` 컬럼을 추가했습니다(담당 의사 이름 표시용).
