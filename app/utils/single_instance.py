import os
import hashlib
import tempfile
import time
from pathlib import Path

CMD_ACTIVATE = b"activate"
CMD_SHUTDOWN = b"shutdown"
RESP_OK = b"ok"
RESP_ACCEPTED = b"accepted"
RESP_FAIL = b"fail"
FORCE_RESTART_WAIT_TIMEOUT = 10.0


class _SingleInstanceLock:
    """跨平台进程互斥（同一二进制/脚本只允许一个主进程运行）。"""

    def __init__(self, lock_key: str):
        self.lock_key = str(lock_key)
        self._fp = None
        self.lock_path = None

    @staticmethod
    def _make_lock_path(lock_key: str) -> str:
        h = hashlib.sha256(lock_key.encode("utf-8")).hexdigest()[:16]
        filename = f"mfw_single_instance_{h}.lock"
        return os.path.join(tempfile.gettempdir(), filename)

    def acquire(self) -> bool:
        if self._fp is not None:
            return True

        self.lock_path = self._make_lock_path(self.lock_key)
        os.makedirs(os.path.dirname(self.lock_path), exist_ok=True)

        self._fp = open(self.lock_path, "a+", encoding="utf-8")
        self._fp.seek(0)

        try:
            if os.name == "nt":
                import msvcrt

                self._fp.seek(0, os.SEEK_END)
                if self._fp.tell() == 0:
                    self._fp.write("0")
                    self._fp.flush()
                self._fp.seek(0)
                msvcrt.locking(self._fp.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except Exception:
            try:
                self._fp.close()
            except Exception:
                pass
            self._fp = None
            return False

    def release(self) -> None:
        if self._fp is None:
            return
        try:
            if os.name == "nt":
                import msvcrt

                self._fp.seek(0)
                msvcrt.locking(self._fp.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._fp.fileno(), fcntl.LOCK_UN)
        finally:
            try:
                self._fp.close()
            finally:
                self._fp = None


class _ActivationServer:
    """接收后续实例的激活/关闭请求，并回写处理结果。"""

    def __init__(self, server_name: str):
        self.server_name = str(server_name)
        self._server = None
        self._on_activate = None
        self._on_shutdown = None

    @staticmethod
    def make_server_name(lock_key: str) -> str:
        h = hashlib.sha256(lock_key.encode("utf-8")).hexdigest()[:16]
        return f"mfw_single_instance_{h}"

    def set_on_activate(self, callback) -> None:
        self._on_activate = callback

    def set_on_shutdown(self, callback) -> None:
        self._on_shutdown = callback

    def start(self, parent=None) -> bool:
        from PySide6.QtNetwork import QLocalServer

        try:
            QLocalServer.removeServer(self.server_name)
        except Exception:
            pass

        self._server = QLocalServer(parent)
        self._server.newConnection.connect(self._handle_new_connection)
        if self._server.listen(self.server_name):
            return True

        try:
            self._server.close()
        except Exception:
            pass
        self._server = None
        return False

    def close(self) -> None:
        if self._server is None:
            return
        try:
            self._server.close()
        finally:
            try:
                from PySide6.QtNetwork import QLocalServer

                QLocalServer.removeServer(self.server_name)
            except Exception:
                pass
            self._server = None

    def _handle_new_connection(self) -> None:
        if self._server is None:
            return

        while self._server.hasPendingConnections():
            socket = self._server.nextPendingConnection()
            if socket is None:
                continue

            if socket.bytesAvailable() > 0:
                self._consume_activation_request(socket)
            else:
                socket.readyRead.connect(
                    lambda current_socket=socket: self._consume_activation_request(
                        current_socket
                    )
                )
            socket.disconnected.connect(socket.deleteLater)

    def _consume_activation_request(self, socket) -> None:
        try:
            payload = bytes(socket.readAll()).strip().lower()
        except Exception:
            payload = b""

        command = payload or CMD_ACTIVATE
        if command == CMD_SHUTDOWN:
            accepted = False
            if self._on_shutdown is not None:
                try:
                    accepted = bool(self._on_shutdown())
                except Exception:
                    accepted = False
            response = RESP_ACCEPTED if accepted else RESP_FAIL
        else:
            activated = False
            if self._on_activate is not None:
                try:
                    activated = bool(self._on_activate())
                except Exception:
                    activated = False
            response = RESP_OK if activated else RESP_FAIL

        try:
            socket.write(response)
            socket.flush()
            socket.waitForBytesWritten(800)
        except Exception:
            pass

        try:
            socket.disconnectFromServer()
        except Exception:
            pass


def _normalize_install_anchor(instance_key: str) -> Path:
    return Path(instance_key).resolve()


def _same_path(a: str | Path, b: Path) -> bool:
    try:
        return Path(a).resolve() == b
    except (OSError, ValueError):
        if os.name == "nt":
            return os.path.normcase(str(a)) == os.path.normcase(str(b))
        return False


def _is_updater_process_name(name: str) -> bool:
    lowered = name.lower()
    return lowered in {"mfwupdater", "mfwupdater.exe"} or lowered.startswith(
        "mfwupdater."
    )


def process_matches_install_anchor(
    *,
    pid: int,
    exe: str | None,
    cmdline: list[str],
    anchor_path: Path,
    exclude_pid: int | None = None,
) -> bool:
    """判断进程是否为同一安装目录下的 MFW 主程序（不含更新器）。"""
    if exclude_pid is not None and pid == exclude_pid:
        return False

    if exe and _same_path(exe, anchor_path):
        if not _is_updater_process_name(Path(exe).name):
            return True

    anchor_str = str(anchor_path)
    for arg in cmdline:
        if not arg:
            continue
        if _same_path(arg, anchor_path):
            return True
        if os.name == "nt" and os.path.normcase(arg) == os.path.normcase(anchor_str):
            return True
    return False


def is_instance_running(instance_key: str) -> bool:
    """同安装锚点是否已有实例占用单实例锁。"""
    probe = _SingleInstanceLock(str(instance_key))
    if probe.acquire():
        probe.release()
        return False
    return True


def is_running_with_admin_privileges() -> bool:
    """当前进程是否具备管理员/root 权限。"""
    if os.name == "nt":
        try:
            import ctypes

            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False

    get_euid = getattr(os, "geteuid", None)
    if callable(get_euid):
        try:
            return get_euid() == 0
        except Exception:
            return False
    return False


def try_activate_existing_instance(
    server_name: str,
    *,
    connect_ms: int = 800,
    response_ms: int = 500,
) -> bool:
    """请求已有实例前置窗口；仅当收到 RESP_OK 时视为成功。"""
    try:
        from PySide6.QtNetwork import QLocalSocket
    except Exception:
        return False

    socket = QLocalSocket()
    socket.connectToServer(server_name)
    if not socket.waitForConnected(connect_ms):
        return False

    try:
        socket.write(CMD_ACTIVATE)
        socket.flush()
        if not socket.waitForBytesWritten(800):
            return False
        if not socket.waitForReadyRead(response_ms):
            return False
        response = bytes(socket.readAll()).strip().lower()
        return response == RESP_OK
    except Exception:
        return False
    finally:
        try:
            socket.disconnectFromServer()
        except Exception:
            pass


def find_matching_instance_pids(
    instance_key: str, *, exclude_pid: int | None = None
) -> list[int]:
    """查找同安装锚点下仍在运行的 MFW 主进程 PID 列表。"""
    try:
        import psutil
    except Exception:
        return []

    anchor_path = _normalize_install_anchor(instance_key)
    matched: list[int] = []
    for proc in psutil.process_iter(["pid", "exe", "cmdline"]):
        try:
            pid = int(proc.info.get("pid") or 0)
            if pid <= 0:
                continue
            cmdline = proc.info.get("cmdline") or []
            if not isinstance(cmdline, list):
                cmdline = list(cmdline)
            exe = proc.info.get("exe")
            if process_matches_install_anchor(
                pid=pid,
                exe=exe,
                cmdline=cmdline,
                anchor_path=anchor_path,
                exclude_pid=exclude_pid,
            ):
                matched.append(pid)
        except Exception:
            continue
    return matched


def terminate_matching_instances(
    instance_key: str,
    *,
    exclude_pid: int | None = None,
    wait_timeout: float = 5.0,
) -> bool:
    """尝试终止同安装锚点的残留实例；返回是否至少结束了一个进程。"""
    try:
        import psutil
    except Exception:
        return False

    pids = find_matching_instance_pids(instance_key, exclude_pid=exclude_pid)
    if not pids:
        return False

    procs: list = []
    for pid in pids:
        try:
            procs.append(psutil.Process(pid))
        except Exception:
            continue

    if not procs:
        return False

    terminated_any = False
    for proc in procs:
        try:
            proc.terminate()
            terminated_any = True
        except Exception:
            continue

    if not terminated_any:
        return False

    gone, alive = psutil.wait_procs(procs, timeout=max(0.0, wait_timeout))
    for proc in alive:
        try:
            proc.kill()
        except Exception:
            continue
    if alive:
        psutil.wait_procs(alive, timeout=max(0.0, wait_timeout))

    return True


def request_instance_shutdown(server_name: str) -> bool:
    """通过本地套接字请求已有实例执行优雅关闭。"""
    try:
        from PySide6.QtNetwork import QLocalSocket
    except Exception:
        return False

    socket = QLocalSocket()
    socket.connectToServer(server_name)
    if not socket.waitForConnected(800):
        return False

    try:
        socket.write(CMD_SHUTDOWN)
        socket.flush()
        if not socket.waitForBytesWritten(800):
            return False
        if not socket.waitForReadyRead(1500):
            return False
        response = bytes(socket.readAll()).strip().lower()
        return response in {RESP_OK, RESP_ACCEPTED}
    except Exception:
        return False
    finally:
        try:
            socket.disconnectFromServer()
        except Exception:
            pass


def force_restart_existing_instance(
    instance_key: str, *, timeout: float = FORCE_RESTART_WAIT_TIMEOUT
) -> bool:
    """请求同安装锚点旧实例关闭并等待其退出。无旧实例时直接返回 True。"""
    if not is_instance_running(instance_key):
        return True

    server_name = _ActivationServer.make_server_name(str(instance_key))
    request_instance_shutdown(server_name)
    return wait_for_instance_available(instance_key, timeout=timeout)


def wait_for_instance_available(
    instance_key: str, *, timeout: float = 10.0, poll_interval: float = 0.25
) -> bool:
    """等待同安装锚点的单实例锁可被获取。"""
    probe = _SingleInstanceLock(str(instance_key))
    deadline = time.monotonic() + max(0.0, timeout)
    while time.monotonic() < deadline:
        if probe.acquire():
            probe.release()
            return True
        time.sleep(poll_interval)
    return False


def try_force_terminate_stale_instance(
    instance_key: str,
    *,
    exclude_pid: int | None = None,
    terminate_wait: float = 5.0,
    lock_wait: float = 5.0,
) -> bool:
    """在具备权限时强杀残留实例并等待单实例锁释放。"""
    if not is_running_with_admin_privileges():
        return False
    if not terminate_matching_instances(
        instance_key,
        exclude_pid=exclude_pid,
        wait_timeout=terminate_wait,
    ):
        return False
    return wait_for_instance_available(instance_key, timeout=lock_wait)


class SingleInstanceGuard:
    """单实例守卫：文件锁判重 + 本地套接字激活已有实例。"""

    def __init__(self, instance_key: str):
        self.instance_key = str(instance_key)
        self.server_name = _ActivationServer.make_server_name(self.instance_key)
        self._lock = _SingleInstanceLock(self.instance_key)
        self._activation_server = _ActivationServer(self.server_name)

    def acquire(self) -> bool:
        return self._lock.acquire()

    def release(self) -> None:
        self._lock.release()

    def start_activation_server(self, parent=None) -> bool:
        return self._activation_server.start(parent)

    def stop_activation_server(self) -> None:
        self._activation_server.close()

    def set_activation_callback(self, callback) -> None:
        self._activation_server.set_on_activate(callback)

    def set_shutdown_callback(self, callback) -> None:
        self._activation_server.set_on_shutdown(callback)

    def request_instance_shutdown(self) -> bool:
        return request_instance_shutdown(self.server_name)

    def notify_existing_instance(self) -> bool:
        """请求已有实例前置窗口；仅当旧实例正常响应时返回 True。"""
        return try_activate_existing_instance(self.server_name)
