from repositorys.repository_manager import run, execute


class OwnerRepository:
    def insert(self, conn, owner, branch):          # 트랜잭션 안에서 호출 (conn을 받음)
        cur = execute(conn,
            "INSERT INTO Owner (oname, pnum, address, branch) VALUES (%s, %s, %s, %s)",
            (owner.oname, owner.pnum, owner.address, branch),
        )
        return cur.lastrowid

    async def find(self, oid, branch):
        row = await run(lambda conn: execute(conn, "SELECT * FROM Owner WHERE oid = %s AND branch = %s", (oid, branch)).fetchone())
        return dict(row) if row else None

    async def find_by_name(self, oname, branch):
        # 검색어가 없으면 최근 등록 20명, 있으면 앞부분이 일치하는 보호자 전부 (최근 등록순)
        limit = "" if oname else " LIMIT 20"
        rows = await run(lambda conn: execute(conn, "SELECT * FROM Owner WHERE oname LIKE %s AND branch = %s ORDER BY oid DESC" + limit, (f"{oname}%", branch)).fetchall())
        return [dict(row) for row in rows]

    async def update(self, oid, fields):
        sets = ", ".join(f"{key} = %s" for key in fields)
        await run(lambda conn: execute(conn, f"UPDATE Owner SET {sets} WHERE oid = %s", (*fields.values(), oid)))
