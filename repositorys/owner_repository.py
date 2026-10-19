from repositorys.repository_manager import run, execute


class OwnerRepository:
    async def insert(self, owner, branch):
        cur = await run(lambda conn: execute(conn,
            "INSERT INTO owners (oname, pnum, address, branch) VALUES (%s, %s, %s, %s)",
            (owner.oname, owner.pnum, owner.address, branch),
        ))
        return cur.lastrowid

    async def find(self, oid, branch):
        row = await run(lambda conn: execute(conn, "SELECT * FROM owners WHERE oid = %s AND branch = %s", (oid, branch)).fetchone())
        return dict(row) if row else None

    async def find_by_name(self, oname, branch):
        rows = await run(lambda conn: execute(conn, "SELECT * FROM owners WHERE oname LIKE %s AND branch = %s ORDER BY oid", (f"%{oname}%", branch)).fetchall())
        return [dict(row) for row in rows]

    async def update(self, oid, fields):
        sets = ", ".join(f"{key} = %s" for key in fields)
        await run(lambda conn: execute(conn, f"UPDATE owners SET {sets} WHERE oid = %s", (*fields.values(), oid)))
