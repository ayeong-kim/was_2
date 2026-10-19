from repositorys.repository_manager import run, execute

# 진료 + 담당 의사 이름 + 동물 정보 (Owner는 지점 확인용)
SELECT = """
    SELECT c.*, u.name AS vet_name, p.pname, p.gender, p.age, p.weight, p.type, p.breed, p.notes
    FROM Consultation c
    JOIN User u ON u.uid = c.vet_uid
    JOIN Pet p ON p.pid = c.pid
    JOIN Owner o ON o.oid = p.oid
"""


class ConsultationRepository:
    async def insert(self, pid, vet_uid, purpose):
        cur = await run(lambda conn: execute(conn,
            "INSERT INTO Consultation (pid, vet_uid, purpose) VALUES (%s, %s, %s)",
            (pid, vet_uid, purpose),
        ))
        return cur.lastrowid

    async def find(self, cid):
        row = await run(lambda conn: execute(conn, SELECT + " WHERE c.cid = %s", (cid,)).fetchone())
        return dict(row) if row else None

    async def find_by_pet(self, pid, branch):
        rows = await run(lambda conn: execute(conn, SELECT + " WHERE c.pid = %s AND o.branch = %s ORDER BY c.cid DESC", (pid, branch)).fetchall())
        return [dict(row) for row in rows]

    async def find_assigned(self, vet_uid):
        rows = await run(lambda conn: execute(conn, SELECT + " WHERE c.vet_uid = %s AND c.status IN ('대기', '진료중') ORDER BY c.cid", (vet_uid,)).fetchall())
        return [dict(row) for row in rows]

    async def update_status(self, cid, vet_uid, before, after):
        cur = await run(lambda conn: execute(conn,
            "UPDATE Consultation SET status = %s WHERE cid = %s AND vet_uid = %s AND status = %s",
            (after, cid, vet_uid, before),
        ))
        return cur.rowcount

    async def update_diagnosis(self, cid, vet_uid, diagnosis):
        cur = await run(lambda conn: execute(conn,
            "UPDATE Consultation SET diagnosis = %s WHERE cid = %s AND vet_uid = %s AND status = '진료중'",
            (diagnosis, cid, vet_uid),
        ))
        return cur.rowcount
