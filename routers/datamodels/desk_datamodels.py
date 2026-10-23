from decimal import Decimal
from pydantic import BaseModel, Field

# 길이·범위 제한은 DB 컬럼(ERD)과 같게 → 넘으면 DB 에러(500) 대신 422


# 주인, 애완동물(단일, 다중) 등록 기능 요청

class PetRequest(BaseModel):
    pname: str = Field(max_length=50)
    gender: str | None = Field(None, max_length=10)
    age: int | None = None
    weight: Decimal | None = Field(None, gt=-1000, lt=1000)     # DECIMAL(5,2)
    type: str = Field(max_length=20)
    breed: str | None = Field(None, max_length=50)
    notes: str | None = None

class OwnerRequest(BaseModel):
    oname: str = Field(max_length=50)
    pnum: str = Field(max_length=20)
    address: str | None = Field(None, max_length=255)
    pets: list[PetRequest] = Field(min_length=1)   # 최소 1마리

# 주인, 애완동물(단일, 다중) 등록 기능 응답

class PetResponse(BaseModel):
    pid: int
    pname: str
    gender: str | None = None
    age: int | None = None
    weight: Decimal | None = None
    type: str
    breed: str | None = None
    notes: str | None = None

class OwnerResponse(BaseModel):
    oid: int
    oname: str
    pnum: str
    address: str | None = None
    pets: list[PetResponse]
    active_pids: list[int] = []                    # 진료가 끝나지 않은(대기·진료중) 동물 id

# 주인 정보 수정 기능 요청 (str = None: 생략은 가능, null은 422)

class OwnerUpdate(BaseModel):
    oname: str = Field(None, max_length=50)
    pnum: str = Field(None, max_length=20)
    address: str | None = Field(None, max_length=255)

# 애완동물 정보 수정 기능 요청 (str = None: 생략은 가능, null은 422)

class PetUpdate(BaseModel):
    pname: str = Field(None, max_length=50)
    gender: str | None = Field(None, max_length=10)
    age: int | None = None
    weight: Decimal | None = Field(None, gt=-1000, lt=1000)     # DECIMAL(5,2)
    type: str = Field(None, max_length=20)
    breed: str | None = Field(None, max_length=50)
    notes: str | None = None

# 애완동물(단일, 다중) 추가 기능 요청

class PetAddRequest(BaseModel):
    oid: int
    pets: list[PetRequest] = Field(min_length=1)   # 최소 1마리

# 방문 등록 기능 요청

class ConsultationRequest(BaseModel):
    vet_uid: int
    purpose: str = Field(max_length=100)
