"""PTY process lifecycle manager.

Wraps os.forkpty() to spawn a child process with a real pseudo-terminal.
Provides non-blocking read/write, resize (TIOCSWINSZ), and clean teardown.
"""

from __future__ import annotations

import errno
import fcntl
import os
import signal
import struct
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

    def spawn(self, argv: list[str], rows: int = 24, cols: int = 80,
              cwd: str | None = None, env: dict[str, str] | None = None) -> None:
        """Fork a child process with a PTY.

        Args:
            argv: Command and arguments, e.g. ["/bin/bash"].
            rows: Initial terminal rows.
            cols: Initial terminal columns.
            cwd: Working directory for the child.
            env: Environment variables for the child.
        """
        pid, fd = os.forkpty()

        if pid == 0:
            # --- Child process ---
            # Set the window size on the slave side before exec
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
            # --- Parent process ---
            self._master_fd = fd
            self._child_pid = pid
            self._alive = True
            # Set master fd to non-blocking
            flags = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    def read(self, size: int = 65536) -> bytes:
        """Read available data from the PTY master (non-blocking).

        Returns empty bytes if nothing available.
        Raises EOFError if the child has exited (EIO on master).
        """
        if self._master_fd < 0:
            raise EOFError("PTY not open")
        try:
            data = os.read(self._master_fd, size)
            if not data:
                raise EOFError("PTY EOF")
            return data
        except OSError as e:
            if e.errno == errno.EIO:
                # Child exited — the PTY slave side closed
                self._alive = False
                raise EOFError("Child process exited") from e
            if e.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
                return b""
            raise

    def write(self, data: bytes) -> None:
        """Write data to the PTY master (sends to child's stdin)."""
        if self._master_fd < 0:
            return
        try:
            os.write(self._master_fd, data)
        except OSError:
            pass

    def resize(self, rows: int, cols: int) -> None:
        """Notify the child of a terminal size change via TIOCSWINSZ."""
        if self._master_fd < 0:
            return
        _set_winsize(self._master_fd, rows, cols)

    def terminate(self) -> int | None:
        """Terminate the child process and clean up.

        Returns the exit status or None.
        """
        if not self._alive and self._master_fd < 0:
            return None

        exit_status = None

        # Send SIGHUP first, then SIGKILL if still alive
        if self._child_pid > 0 and self._alive:
            try:
                os.kill(self._child_pid, signal.SIGHUP)
            except ProcessLookupError:
                pass
            try:
                pid, status = os.waitpid(self._child_pid, os.WNOHANG)
                if pid == 0:
                    # Still alive, escalate
                    os.kill(self._child_pid, signal.SIGKILL)
                    pid, status = os.waitpid(self._child_pid, 0)
                exit_status = os.WEXITSTATUS(status) if os.WIFEXITED(status) else -1
            except ChildProcessError:
                pass

        # Close the master fd
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
        """Check if child is still running. Returns exit code or None if alive."""
        if not self._alive or self._child_pid < 0:
            return 0
        try:
            pid, status = os.waitpid(self._child_pid, os.WNOHANG)
            if pid == 0:
                return None  # Still running
            self._alive = False
            return os.WEXITSTATUS(status) if os.WIFEXITED(status) else -1
        except ChildProcessError:
            self._alive = False
            return 0


def _set_winsize(fd: int, rows: int, cols: int) -> None:
    """Set the terminal window size on a file descriptor."""
    winsize = struct.pack("HHHH", rows, cols, 0, 0)
    try:
        fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)
    except OSError:
        pass
