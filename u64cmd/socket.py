"""Implementation of Ultimate1541 DMA Socket Protocol"""

import socket
import struct

# u1541 + u64
SOCKET_CMD_DMA = 0xFF01
SOCKET_CMD_DMARUN = 0xFF02
SOCKET_CMD_KEYB = 0xFF03
SOCKET_CMD_RESET = 0xFF04
SOCKET_CMD_WAIT = 0xFF05
SOCKET_CMD_DMAWRITE = 0xFF06
SOCKET_CMD_REUWRITE = 0xFF07
SOCKET_CMD_KERNALWRITE = 0xFF08
SOCKET_CMD_DMAJUMP = 0xFF09
SOCKET_CMD_MOUNT_IMG = 0xFF0A
SOCKET_CMD_RUN_IMG = 0xFF0B
SOCKET_CMD_POWEROFF = 0xFF0C
SOCKET_CMD_RUN_CRT = 0xFF0D

# u64 only
SOCKET_CMD_VICSTREAM_ON = 0xFF20
SOCKET_CMD_AUDIOSTREAM_ON = 0xFF21
SOCKET_CMD_DEBUGSTREAM_ON = 0xFF22
SOCKET_CMD_VICSTREAM_OFF = 0xFF30
SOCKET_CMD_AUDIOSTREAM_OFF = 0xFF31
SOCKET_CMD_DEBUGSTREAM_OFF = 0xFF32

# Undocumented, shall only be used by developers.
SOCKET_CMD_LOADSIDCRT = 0xFF71
SOCKET_CMD_LOADBOOTCRT = 0xFF72
SOCKET_CMD_READFLASH = 0xFF75
SOCKET_CMD_DEBUG_REG = 0xFF76

REU_MAX_SIZE = 65536 - 4

STREAM_ID_VIC = 0
STREAM_ID_AUDIO = 1
STREAM_ID_DEBUG = 2

STREAM_NAMES = ("vic", "audio", "debug")
STREAM_MAP = {"vic": STREAM_ID_VIC, "audio": STREAM_ID_AUDIO, "debug": STREAM_ID_DEBUG}


class U64Socket:
    def __init__(self, host, port=64):
        self._addr = (host, port)
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect(self._addr)

    def close(self):
        self._sock.close()

    def _send_cmd(self, cmd_id, buf=None):
        """send a DMA socket command packet."""
        # have buf data?
        if buf:
            buf_len = len(buf)
        else:
            buf_len = 0
        # long command
        if cmd_id in (SOCKET_CMD_MOUNT_IMG, SOCKET_CMD_RUN_IMG, SOCKET_CMD_RUN_CRT):
            # 24 bit len
            hdr = struct.pack("<HL", cmd_id, buf_len & 0xFFFFFF)[:-1]
            assert buf_len <= 0xFFFFFF
        else:
            hdr = struct.pack("<HH", cmd_id, buf_len & 0xFFFF)
            assert buf_len <= 0xFFFF
        # write header and buf
        if buf:
            all = hdr + buf
        else:
            all = hdr
        self._sock.sendall(all)

    def cmd_dma(self, data):
        self._send_cmd(SOCKET_CMD_DMA, data)

    def cmd_dma_run(self, data):
        self._send_cmd(SOCKET_CMD_DMARUN, data)

    def cmd_dma_jump(self, data):
        self._send_cmd(SOCKET_CMD_DMAJUMP, data)

    def cmd_dma_write(self, offset, data):
        """Write bytes directly into C64 memory"""
        off = struct.pack("<H", offset)
        self._send_cmd(SOCKET_CMD_DMAWRITE, off + data)

    def cmd_keyb(self, text):
        """Type in text"""
        if type(text) not in (bytes, bytearray):
            raise ValueError("text must be bytes!")
        self._send_cmd(SOCKET_CMD_KEYB, text)

    def cmd_reset(self):
        """reset the C64"""
        self._send_cmd(SOCKET_CMD_RESET)

    def cmd_poweroff(self):
        self._send_cmd(SOCKET_CMD_POWEROFF)

    def cmd_reu_write(self, offset, data):
        # do not write more than 64k
        if len(data) > REU_MAX_SIZE:
            raise ValueError(f"data size > {REU_MAX_SIZE}")
        # 24 bit offset
        off = struct.pack("<L", offset)[:-1]
        self._send_cmd(SOCKET_CMD_REUWRITE, off + data)

    def cmd_kernal_write(self, data):
        # strange: 2 bytes are skipped at the beginning (PRG?)
        self._send_cmd(SOCKET_CMD_KERNALWRITE, bytes(2) + data)

    def cmd_mount_image(self, data):
        self._send_cmd(SOCKET_CMD_MOUNT_IMG, data)

    def cmd_run_image(self, data):
        self._send_cmd(SOCKET_CMD_RUN_IMG, data)

    def cmd_run_cart(self, data):
        self._send_cmd(SOCKET_CMD_RUN_CRT, data)

    def cmd_stream_on(self, stream_id, duration=0, addr=None):
        # data
        hdr = struct.pack("<H", duration)
        if addr:
            hdr += addr.encode("ascii")
        self._send_cmd(SOCKET_CMD_VICSTREAM_ON + stream_id, hdr)

    def cmd_stream_off(self, stream_id):
        self._send_cmd(SOCKET_CMD_VICSTREAM_OFF + stream_id)
