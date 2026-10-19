from repositorys.repository_manager import run, execute


class UserRepository:
    async def find_by_login_id(self, login_id):
        row = await run(lambda conn: execute(conn, "SELECT * FROM users WHERE login_id = %s", (login_id,)).fetchone())
        return dict(row) if row else None

    async def find_vets(self, branch):
        rows = await run(lambda conn: execute(conn, "SELECT * FROM users WHERE role = 'vet' AND branch = %s ORDER BY uid", (branch,)).fetchall())
        return [dict(row) for row in rows]
