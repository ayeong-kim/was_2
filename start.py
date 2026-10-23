import os
import signal
import threading
from multiprocessing import Process, Pipe
from multiprocessing.connection import wait
import uvicorn

from routers.router import app
from process import desk_worker, vet_worker, desk_child, vet_child, desk_channel, vet_channel
from repositorys.repository_manager import init_db
from config import WAS_HOST, WAS_PORT


def watch_workers(*workers):
    wait([worker.sentinel for worker in workers])   # 워커가 하나라도 죽으면
    os.kill(os.getpid(), signal.SIGTERM)            # main도 종료 → systemd(Restart=always)가 WAS 전체를 다시 시작


if __name__ == "__main__":
    init_db()
    desk = Process(target=desk_worker, args=(desk_child,), daemon=True)
    vet = Process(target=vet_worker, args=(vet_child,), daemon=True)
    desk.start()
    vet.start()
    desk_child.close()   # 메인은 child 끝을 안 씀 → 워커가 죽으면 요청이 멈추지 않고 에러로 끝남
    vet_child.close()
    desk_channel.start()
    vet_channel.start()
    threading.Thread(target=watch_workers, args=(desk, vet), daemon=True).start()

    uvicorn.run(app, host=WAS_HOST, port=WAS_PORT)   # reload 쓰면 Pipe가 워커와 끊김
