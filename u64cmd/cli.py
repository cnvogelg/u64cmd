"""command line interface for u64cmd"""

import time
import struct
import click
import u64cmd.socket as socket
import u64cmd.util as util


class BasedIntParamType(click.ParamType):
    name = "integer"

    def convert(self, value, param, ctx):
        if isinstance(value, int):
            return value

        try:
            if value[:2].lower() == "0x":
                return int(value[2:], 16)
            elif value[:1] == "0":
                return int(value, 8)
            return int(value, 10)
        except ValueError:
            self.fail(f"{value!r} is not a valid integer", param, ctx)


BASED_INT = BasedIntParamType()

pass_socket = click.make_pass_decorator(socket.U64Socket, ensure=True)


def dump_keycodes(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo("Use '{keycode}' in your type string:")
    for key, value in util.CTRL_TABLE.items():
        click.echo(f"{key:8} {value}")
    ctx.exit()


@click.group(chain=True)
@click.option(
    "--host",
    "-h",
    envvar="U64CMD_HOST",
    required=True,
    help="Host address of Ultimate64/II+",
)
@click.option(
    "--port",
    "-p",
    envvar="U64CMD_PORT",
    type=int,
    default=64,
    help="Port of DMA Service",
)
@click.option(
    "--dump-keycodes",
    "-D",
    is_flag=True,
    callback=dump_keycodes,
    expose_value=False,
    is_eager=True,
)
@click.version_option()
@click.pass_context
def cli(ctx, host, port):
    click.echo(f"connecting {host}:{port}")
    try:
        ctx.obj = socket.U64Socket(host, port)
    except OSError as e:
        click.echo(f"Socket Error: {e}")
        ctx.exit()


@cli.command("prg_load", help="Upload (and run) PRG file")
@click.argument("prg_file", type=click.Path(exists=True))
@click.option("--run", "-r", is_flag=True, help="RUN program after loading")
@click.option("--jump", "-j", is_flag=True, help="Jump to start address")
@click.help_option()
@pass_socket
def prg_load(sock, prg_file, run, jump):
    click.echo(f"loading prg file '{click.format_filename(prg_file)}'... ", nl=False)
    with open(prg_file, "rb") as fh:
        data = fh.read()
    if len(data) < 2:
        click.abort("invalid file")
    load_addr = struct.unpack_from("<H", data, 0)[0]
    click.echo(f"@{load_addr:04x}  ", nl=False)
    if jump:
        click.echo("jump")
        sock.cmd_dma_jump(data)
    elif run:
        click.echo("run")
        sock.cmd_dma_run(data)
    else:
        click.echo("load")
        sock.cmd_dma(data)


@cli.command("data_write", help="Upload data into C64 RAM")
@click.argument("data_file", type=click.Path(exists=True))
@click.option("--addr", "-a", type=BASED_INT, default=0xC000, help="load address")
@click.option("--offset", "-o", type=BASED_INT, default=0, help="skip file beginning")
@click.option("--size", "-s", type=BASED_INT, default=0, help="limit transfer size")
@pass_socket
def data_write(sock, data_file, addr, offset, size):
    click.echo(f"writing data file '{click.format_filename(data_file)}'... ", nl=False)
    with open(data_file, "rb") as fh:
        data = fh.read()
    if offset > 0:
        data = data[offset:]
    if size > 0:
        data = data[0:size]
    click.echo(f"@{addr:04x} +{offset:04x} #{len(data):04x}")
    sock.cmd_dma_write(addr, data)


@cli.command("stream_on", help="Enable U64 stream")
@click.argument("stream_name", type=click.Choice(socket.STREAM_NAMES))
@click.option("--duration", "-d", type=BASED_INT, default=0, help="streaming duration")
@click.option("--addr", "-a", type=click.STRING, help="receiving host address")
@pass_socket
def stream_on(sock, stream_name, duration, addr):
    stream_id = socket.STREAM_MAP[stream_name]
    click.echo(
        f"enable streaming {stream_name}/{stream_id} (duration={duration}, addr={addr})"
    )
    sock.cmd_stream_on(stream_id, duration, addr)


@cli.command("stream_off", help="Disable U64 stream")
@click.argument("stream_name", type=click.Choice(socket.STREAM_NAMES))
@pass_socket
def stream_off(sock, stream_name):
    stream_id = socket.STREAM_MAP[stream_name]
    click.echo(f"disable streaming {stream_name}/{stream_id}")
    sock.cmd_stream_off(stream_id)


@cli.command("poke", help="Write byte value")
@click.argument("addr", type=BASED_INT)
@click.argument("value", type=BASED_INT)
@pass_socket
def poke(sock, addr, value):
    addr &= 0xFFFF
    value &= 0xFF
    click.echo(f"poke({addr:04x},{value:02x})")
    sock.cmd_dma_write(addr, struct.pack("B", value))


@cli.command("pokew", help="Write word value")
@click.argument("addr", type=BASED_INT)
@click.argument("value", type=BASED_INT)
@pass_socket
def poke(sock, addr, value):
    addr &= 0xFFFF
    value &= 0xFFFF
    click.echo(f"poke({addr:04x},{value:02x})")
    sock.cmd_dma_write(addr, struct.pack(">H", value))


@cli.command("reu_load", help="Upload REU image")
@click.argument("reu_file", type=click.Path(exists=True))
@click.option("--addr", "-a", type=BASED_INT, default=0, help="REU load address")
@click.option("--offset", "-o", type=BASED_INT, default=0, help="skip file beginning")
@click.option("--size", "-s", type=BASED_INT, default=0, help="limit transfer size")
@pass_socket
def reu_load(sock, reu_file, addr, offset, size):
    click.echo(f"loading REU file '{click.format_filename(reu_file)}'... ", nl=False)
    # read data
    with open(reu_file, "rb") as fh:
        data = fh.read()
    # select size
    if size:
        total_size = size
    else:
        total_size = len(data)
    click.echo(f" {total_size//1024} kB +{offset:06x} @{addr:06x}")
    chunk_size = socket.REU_MAX_SIZE
    # upload loop
    with click.progressbar(length=total_size, label="REU Upload") as bar:
        chunks = util.gen_chunk_iter(data, offset, total_size, chunk_size)
        sum = 0
        for offset, chunk in chunks:
            sock.cmd_reu_write(addr + offset, chunk)
            bar.update(len(chunk))
            sum += len(chunk)
        print(sum, total_size)


@cli.command("disk_load", help="Mount/Autorun disk image")
@click.argument("disk_file", type=click.Path(exists=True))
@click.option("--run", "-r", is_flag=True, help="RUN first file on image")
@pass_socket
def img_load(sock, disk_file, run):
    click.echo(f"loading disk file '{click.format_filename(disk_file)}'... ", nl=False)
    # read data
    with open(disk_file, "rb") as fh:
        data = fh.read()
    if run:
        click.echo("run")
        sock.cmd_run_image(data)
    else:
        click.echo("mount")
        sock.cmd_mount_image(data)


@cli.command("crt_load", help="Upload/Activate CRT image")
@click.argument("crt_file", type=click.Path(exists=True))
@pass_socket
def crt_load(sock, crt_file):
    click.echo(f"loading crt file '{click.format_filename(crt_file)}'... ", nl=False)
    # read data
    with open(crt_file, "rb") as fh:
        data = fh.read()
    click.echo("run")
    sock.cmd_run_cart(data)


@cli.command("kernal_load", help="Upload/Activate Kernal image")
@click.argument("kernal_file", type=click.Path(exists=True))
@pass_socket
def crt_load(sock, kernal_file):
    click.echo(
        f"loading kernal file '{click.format_filename(kernal_file)}'... ", nl=False
    )
    # read data
    with open(kernal_file, "rb") as fh:
        data = fh.read()
    click.echo("done")
    sock.cmd_kernal_write(data)


@cli.command("reset", help="Reset C64")
@pass_socket
def reset(sock):
    click.echo("resetting device")
    sock.cmd_reset()


@cli.command("poweroff", help="Poweroff Ultimate64")
@pass_socket
def reset(sock):
    click.echo("power off device")
    sock.cmd_poweroff()


@cli.command("type", help="Inject text on C64")
@click.argument("text")
@pass_socket
def type(sock, text):
    click.echo(f"typing '{text}'")
    raw_text = util.decode_text(text)
    sock.cmd_keyb(raw_text)


if __name__ == "__main__":
    cli()
