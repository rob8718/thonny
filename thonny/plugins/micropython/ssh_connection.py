from thonny.plugins.micropython.connection import MicroPythonConnection
import shlex


class SshConnection(MicroPythonConnection):
    def __init__(self, client, executable, args):
        import threading

        self._client = client

        cmd_line_str = " ".join(map(shlex.quote, [executable] + args))
        self._stdin, self._stdout, self._stderr = self._client.exec_command(
            cmd_line_str, bufsize=0, timeout=None, get_pty=True
        )

        self._reading_thread = threading.Thread(target=self._listen_output, daemon=True)
        self._reading_thread.start()

    def write(self, data, block_size=255, delay=0.01):
        if isinstance(data, (bytes, bytearray)):
            data = data.decode(self.encoding)
        self._stdin.write(data)
        self._stdin.flush()
        return len(data)

    def _listen_output(self):
        "NB! works in background thread"
        try:
            while True:
                chars = self._stdout.read(1)
                if len(chars) > 0:
                    as_bytes = chars.encode(self.encoding)
                    self.num_bytes_received += len(as_bytes)
                    self._make_output_available(as_bytes)
                else:
                    self._error = "EOF"
                    break

        except Exception as e:
            self._error = str(e)

    def close(self):
        self._client.close()
        self._reading_thread.join()
        self._client = None
        self._reading_thread = None
