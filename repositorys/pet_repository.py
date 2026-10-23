from repositorys.repository_manager import run, execute


class PetRepository:
    def insert(self, conn, oid, pet):               # 트랜잭션 안에서 호출 (conn을 받음)
        cur = execute(conn,
            "INSERT INTO Pet (oid, pname, gender, age, weight, type, breed, notes) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (oid, pet.pname, pet.gender, pet.age, pet.weight, pet.type, pet.breed, pet.notes),
        )
        return cur.lastrowid

    async def find(self, pid, branch):
        row = await run(lambda conn: execute(conn,
            "SELECT p.* FROM Pet p JOIN Owner o ON o.oid = p.oid WHERE p.pid = %s AND o.branch = %s", (pid, branch)
        ).fetchone())
        return dict(row) if row else None

    async def find_by_owner(self, oid):
        rows = await run(lambda conn: execute(conn, "SELECT * FROM Pet WHERE oid = %s ORDER BY pid", (oid,)).fetchall())
        return [dict(row) for row in rows]

    async def find_by_owners(self, oids):
        # 여러 보호자의 동물을 한 번에 조회
        if not oids:
            return []
        marks = ", ".join(["%s"] * len(oids))
        rows = await run(lambda conn: execute(conn, f"SELECT * FROM Pet WHERE oid IN ({marks}) ORDER BY pid", tuple(oids)).fetchall())
        return [dict(row) for row in rows]

    async def update(self, pid, fields):
        sets = ", ".join(f"{key} = %s" for key in fields)
        await run(lambda conn: execute(conn, f"UPDATE Pet SET {sets} WHERE pid = %s", (*fields.values(), pid)))
