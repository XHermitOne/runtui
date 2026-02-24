"""PTY process lifecycle manager with cross-platform support."""

from __future__ import annotations

import errno
import os
import signal
import struct
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - import used for typing only
    from winpty import PtyProcess as WinPTYType


if os.name == "nt":  # Windows implementation ---------------------------------
    import socket

    try:  # pragma: no cover - exercised at runtime
        from winpty import PtyProcess as WinPTYProcess  # type: ignore
    except ImportError:  # pragma: no cover - handled gracefully at runtime
        WinPTYProcess = None  # type: ignore

    class PtyProcess:
        """Manage a child process hosted in a Windows pseudo-terminal."""

        def __init__(self) -> None:
            self._proc: WinPTYType | None = None  # type: ignore[name-defined]
            self._reader: socket.socket | None = None
            self._master_fd: int = -1
            self._child_pid: int = -1
            self._alive: bool = False
            self._exit_code: int | None = None

        @property
        def master_fd(self) -> int:
            return self._master_fd

        @property
        def child_pid(self) -> int:
            return self._child_pid

        @property
        def alive(self) -> bool:
            return self._alive

        def spawn(
            self,
            argv: list[str],
            rows: int = 24,
            cols: int = 80,
            cwd: str | None = None,
            env: dict[str, str] | None = None,
        ) -> None:
            if WinPTYProcess is None:  # type: ignore[name-defined]
                raise RuntimeError(
                    "pywinpty is required on Windows. Install it with 'pip install pywinpty'."
                )

            if env is None:
                env = os.environ.copy()
            env.setdefault("TERM", "xterm-256color")
            env["COLUMNS"] = str(cols)
            env["LINES"] = str(rows)

            try:
                proc = WinPTYProcess.spawn(argv, cwd=cwd, env=env, dimensions=(rows, cols))  # type: ignore[name-defined]
            except FileNotFoundError as exc:
                raise FileNotFoundError(f"Executable not found: {argv[0]}") from exc
            except Exception as exc:  # pragma: no cover - depends on runtime env
                raise RuntimeError("Failed to launch PTY process on Windows") from exc

            reader = getattr(proc, "fileobj", None)
            if reader is None:
                raise RuntimeError("pywinpty did not expose a reader socket")
            reader.setblocking(False)

            self._proc = proc
            self._reader = reader
            self._master_fd = proc.fileno()
            self._child_pid = getattr(proc, "pid", -1) or -1
            self._alive = True
            self._exit_code = None

        def read(self, size: int = 65536) -> bytes:
            if self._reader is None:
                raise EOFError("PTY not open")
            try:
                data = self._reader.recv(size)
            except BlockingIOError:
                return b""
            except OSError as exc:
                if getattr(exc, "winerror", None) in (10035, 10022):  # WSAEWOULDBLOCK
                    return b""
                raise

            if not data:
                self._alive = False
                self._update_exitstatus(force_check=True)
                raise EOFError("PTY EOF")
            return data

        def write(self, data: bytes) -> None:
            if not self._proc or not self._alive:
                return
            text = data.decode("utf-8", errors="ignore") if isinstance(data, bytes) else str(data)
            try:
                self._proc.write(text)
            except Exception:
                self._alive = False

        def resize(self, rows: int, cols: int) -> None:
            if not self._proc:
                return
            try:
                self._proc.setwinsize(rows, cols)
            except Exception:
                pass

        def terminate(self) -> int | None:
            if not self._proc:
                return None
            try:
                self._proc.terminate(force=True)
            except Exception:
                pass
            exit_status = self._update_exitstatus(force_check=True)
            try:
                self._proc.close()
            except Exception:
                pass
            if self._reader is not None:
                try:
                    self._reader.close()
                except OSError:
                    pass
                self._reader = None
            self._master_fd = -1
            self._child_pid = -1
            return exit_status

        def poll(self) -> int | None:
            if not self._proc:
                return 0
            if self._alive and self._proc.isalive():
                return None
            if self._exit_code is not None:
                return self._exit_code
            return self._update_exitstatus(force_check=True)

        def _update_exitstatus(self, force_check: bool = False) -> int | None:
            if not self._proc:
                return self._exit_code
            if not force_check and self._proc.isalive():
                return None
            try:
                status = self._proc.exitstatus
            except Exception:
                status = -1
            if status is None:
                status = -1
            self._exit_code = int(status)
            self._alive = False
            return self._exit_code


else:  # POSIX implementation -----------------------------------------------------
    import fcntl
    import termios

    class PtyProcess:
        """Manages a child process running inside a PTY."""

        def __init__(self) -> None:
            self._master_fd: int = -1
            self._child_pid: int = -1
            self._alive: bool = False

        @property
        def master_fd(self) -> int:
            return self._master_fd

        @property
        def child_pid(self) -> int:
            return self._child_pid

        @property
        def alive(self) -> bool:
            return self._alive

        def spawn(
            self,
            argv: list[str],
            rows: int = 24,
            cols: int = 80,
            cwd: str | None = None,
            env: dict[str, str] | None = None,
        ) -> None:
            """Fork a child process with a PTY."""
            pid, fd = os.forkpty()

            if pid == 0:
                _set_winsize(0, rows, cols)
                if cwd:
                    try:
                        os.chdir(cwd)
                    except OSError:
                        pass
                if env is None:
                    env = os.environ.copy()
                env.setdefault("TERM", "xterm-256color")
                env["COLUMNS"] = str(cols)
                env["LINES"] = str(rows)
                try:
                    os.execvpe(argv[0], argv, env)
                except Exception:
                    os._exit(127)
            else:
                self._master_fd = fd
                self._child_pid = pid
                self._alive = True
                flags = fcntl.fcntl(fd, fcntl.F_GETFL)
                fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        def read(self, size: int = 65536) -> bytes:
            if self._master_fd < 0:
                raise EOFError("PTY not open")
            try:
                data = os.read(self._master_fd, size)
                if not data:
                    raise EOFError("PTY EOF")
                return data
            except OSError as e:
                if e.errno == errno.EIO:
                    self._alive = False
                    raise EOFError("Child process exited") from e
                if e.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
                    return b""
                raise

        def write(self, data: bytes) -> None:
            if self._master_fd < 0:
                return
            try:
                os.write(self._master_fd, data)
            except OSError:
                pass

        def resize(self, rows: int, cols: int) -> None:
            if self._master_fd < 0:
                return
            _set_winsize(self._master_fd, rows, cols)

        def terminate(self) -> int | None:
            if not self._alive and self._master_fd < 0:
                return None

            exit_status = None

            if self._child_pid > 0 and self._alive:
                try:
                    os.kill(self._child_pid, signal.SIGHUP)
                except ProcessLookupError:
                    pass
                try:
                    pid, status = os.waitpid(self._child_pid, os.WNOHANG)
                    if pid == 0:
                        os.kill(self._child_pid, signal.SIGKILL)
                        pid, status = os.waitpid(self._child_pid, 0)
                    exit_status = os.WEXITSTATUS(status) if os.WIFEXITED(status) else -1
                except ChildProcessError:
                    pass

            if self._master_fd >= 0:
                try:
                    os.close(self._master_fd)
                except OSError:
                    pass
                self._master_fd = -1

            self._alive = False
            self._child_pid = -1
            return exit_status

        def poll(self) -> int | None:
            if not self._alive or self._child_pid < 0:
                return 0
            try:
                pid, status = os.waitpid(self._child_pid, os.WNOHANG)
                if pid == 0:
                    return None
                self._alive = False
                return os.WEXITSTATUS(status) if os.WIFEXITED(status) else -1
            except ChildProcessError:
                self._alive = False
                return 0


    def _set_winsize(fd: int, rows: int, cols: int) -> None:
        winsize = struct.pack("HHHH", rows, cols, 0, 0)
        try:
            fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)
        except OSError:
            pass
