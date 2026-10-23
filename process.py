import asyncio
import itertools
import threading
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pipe
from config import DB_POOL_SIZE
from controllers.desk_controllers import DeskControllers
from controllers.vet_controllers import VetControllers


# ---------- 자식 프로세스: 요청을 받는 대로 task로 동시에 처리 ----------

def desk_worker(conn):
    asyncio.run(serve(conn, DeskControllers()))

def vet_worker(conn):
    asyncio.run(serve(conn, VetControllers()))

async def serve(conn, controller):
    loop = asyncio.get_running_loop()
    loop.set_default_executor(ThreadPoolExecutor(DB_POOL_SIZE))     # DB 스레드 수 = 연결 수 (스레드마다 연결 1개)
    receiver = ThreadPoolExecutor(1)                                # 받기 전용 스레드 (DB 연결 안 씀)
    tasks = set()                                                   # 실행 중인 task가 GC 되지 않게 보관
    while True:
        rid, method, args = await loop.run_in_executor(receiver, conn.recv)   # 메인이 보낸 값 받기
        task = asyncio.create_task(handle(conn, controller, rid, method, args))
        tasks.add(task)
        task.add_done_callback(tasks.discard)

async def handle(conn, controller, rid, method, args):
    try:
        result = await getattr(controller, method)(*args)           # control.regist_owner(data)
    except Exception as e:                                          # 예외로 워커가 죽지 않게 메인으로 돌려보냄
        result = e
    conn.send((rid, result))                                        # 요청 id와 같이 돌려줌


# ---------- 메인 프로세스: 요청 id로 응답을 짝지어서 여러 요청을 동시에 보냄 ----------

class Channel:
    def __init__(self, conn):
        self.conn = conn
        self.ids = itertools.count()
        self.waiting = {}                       # 요청 id -> (event loop, future)
        self.send_lock = threading.Lock()

    def start(self):                            # 응답 받는 스레드 (메인 프로세스에서 한 번)
        threading.Thread(target=self.receive, daemon=True).start()

    def receive(self):
        while True:
            try:
                rid, result = self.conn.recv()
            except (EOFError, OSError):         # 워커 죽음 → 기다리던 요청 모두 에러로 끝냄
                for loop, future in list(self.waiting.values()):
                    loop.call_soon_threadsafe(settle, future, ConnectionError("worker 종료"))
                return
            loop, future = self.waiting.pop(rid)
            loop.call_soon_threadsafe(settle, future, result)

    async def request(self, method, *args):
        loop = asyncio.get_running_loop()
        rid = next(self.ids)
        future = loop.create_future()
        self.waiting[rid] = (loop, future)
        try:
            with self.send_lock:
                self.conn.send((rid, method, args))
        except Exception:
            self.waiting.pop(rid, None)
            raise
        return await future

def settle(future, result):
    if future.done():                           # 클라이언트가 끊어서 취소된 요청
        return
    if isinstance(result, Exception):
        future.set_exception(result)
    else:
        future.set_result(result)


desk_main, desk_child = Pipe()
vet_main, vet_child = Pipe()
desk_channel = Channel(desk_main)
vet_channel = Channel(vet_main)
