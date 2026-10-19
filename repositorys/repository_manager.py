import asyncio
import contextvars
import hashlib
from contextlib import asynccontextmanager

import pymysql
from pymysql.constants import FIELD_TYPE
from pymysql.converters import conversions

from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, SEED_PASSWORD

_transaction = contextvars.ContextVar("transaction", default=None)   # 현재 작업의 트랜잭션 연결

# 조회 결과를 SQLite 때와 같은 형태로 받음 → 응답 JSON·웹 화면 그대로
_CONV = dict(conversions)
_CONV[FIELD_TYPE.DATETIME] = str        # DATETIME → "2026-10-19 14:30:00" 문자열
_CONV[FIELD_TYPE.NEWDECIMAL] = float    # DECIMAL(5,2) → 3.5 (3.50 아님)


def connect():
    return pymysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,                 # 결과를 dict로
        client_flag=pymysql.constants.CLIENT.FOUND_ROWS,        # UPDATE 결과 = 조건에 맞은 행 수 (값이 같아도 0 아님)
        conv=_CONV,
        init_command="SET time_zone = '+09:00'",              # 저장·비교 시각을 한국 시간으로 (RDS 기본은 UTC)
    )


def execute(conn, sql, params=None):
    # SQL 실행 후 커서 반환 (fetchone / fetchall / lastrowid / rowcount)
    cur = conn.cursor()
    cur.execute(sql, params)
    return cur


def _rollback(conn):
    # 연결이 끊겨 rollback이 실패해도 원래 에러를 그대로 올리기 위해 무시
    try:
        conn.rollback()
    except Exception:
        pass


async def run(work):
    # work(conn)을 스레드에서 실행 → DB를 기다리는 동안 다른 요청 처리 (비동기 I/O)
    conn = _transaction.get()
    if conn is not None:
        return await asyncio.to_thread(work, conn)

    def job():
        conn = connect()
        try:
            result = work(conn)
            conn.commit()
            return result
        except BaseException:
            _rollback(conn)
            raise
        finally:
            conn.close()
    return await asyncio.to_thread(job)


@asynccontextmanager
async def transaction():
    # 안에서 실행되는 run()을 한 연결로 묶음 → 전부 저장 또는 전부 취소
    conn = connect()
    token = _transaction.set(conn)
    try:
        yield
        conn.commit()
    except BaseException:
        _rollback(conn)
        raise
    finally:
        _transaction.reset(token)
        conn.close()


def init_db():
    # 테이블은 클라우드에서 schema.sql로 미리 만듦 → WAS 계정은 CRUD 권한만 (CREATE 없음)
    # 여기서는 테스트 계정만 넣음 (INSERT 권한이면 충분)
    if not SEED_PASSWORD:
        return
    conn = connect()
    try:
        # 테스트 계정: SEED_PASSWORD가 있을 때만 생성, 이미 있는 아이디는 건너뜀
        password = hashlib.sha256(SEED_PASSWORD.encode()).hexdigest()
        conn.cursor().executemany(
            "INSERT IGNORE INTO User (login_id, password, name, role, branch) VALUES (%s, %s, %s, %s, %s)",
            [
                ("desk1", password, "김간호", "desk", "강남점"),
                ("vet1", password, "이수의", "vet", "강남점"),
                ("vet2", password, "박수의", "vet", "강남점"),
                ("desk2", password, "최간호", "desk", "홍대점"),
                ("vet3", password, "정수의", "vet", "홍대점"),
                ("vet4", password, "한수의", "vet", "홍대점"),
                ("desk3", password, "윤간호", "desk", "서초점"),
                ("vet5", password, "강수의", "vet", "서초점"),
                ("vet6", password, "조수의", "vet", "서초점"),
                ("desk4", password, "임간호", "desk", "잠실점"),
                ("vet7", password, "신수의", "vet", "잠실점"),
                ("vet8", password, "오수의", "vet", "잠실점"),
                ("desk5", password, "서간호", "desk", "분당점"),
                ("vet9", password, "권수의", "vet", "분당점"),
                ("vet10", password, "황수의", "vet", "분당점"),
            ],
        )
        conn.commit()
    finally:
        conn.close()
