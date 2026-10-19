from repositorys.repository_manager import run, execute


class SessionRepository:
    async def insert(self, session_id, uid):
        await run(lambda conn: execute(conn, "INSERT INTO Session (session_id, uid) VALUES (%s, %s)", (session_id, uid)))

    async def find_user(self, session_id, hours):
        # hours 시간이 지난 세션은 없는 것으로 처리 (만료)
        row = await run(lambda conn: execute(conn,
            "SELECT u.* FROM Session s JOIN User u ON u.uid = s.uid"
            " WHERE s.session_id = %s AND s.created_at > NOW() - INTERVAL %s HOUR", (session_id, hours)
        ).fetchone())
        return dict(row) if row else None

    async def delete(self, session_id):
        await run(lambda conn: execute(conn, "DELETE FROM Session WHERE session_id = %s", (session_id,)))

    async def delete_expired(self, hours):
        await run(lambda conn: execute(conn, "DELETE FROM Session WHERE created_at <= NOW() - INTERVAL %s HOUR", (hours,)))
