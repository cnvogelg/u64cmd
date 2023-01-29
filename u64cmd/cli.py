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


@click.group(chain=True)
@click.argument("host")
@click.option("--port", "-p", type=int, default=64)
@click.pass_context
def cli(ctx, host, port):
    click.echo(f"connecting '{host}':{port}")
    ctx.obj = socket.U64Socket(host, port)


@cli.command("prg_load")
@click.argument("prg_file", type=click.Path(exists=True))
@click.option("--run", "-r", is_flag=True)
@click.option("--jump", "-j", is_flag=True)
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


@cli.command("reu_load")
@click.argument("reu_file", type=click.Path(exists=True))
@click.option("--addr", "-a", type=BASED_INT, default=0)
@click.option("--offset", "-o", type=BASED_INT, default=0)
@click.option("--size", "-s", type=BASED_INT, default=0)
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


@cli.command("reset")
@pass_socket
def reset(sock):
    click.echo("resetting device")
    sock.cmd_reset()


@cli.command("poweroff")
@pass_socket
def reset(sock):
    click.echo("power off device")
    sock.cmd_poweroff()


@cli.command("keyb")
@click.argument("text")
@pass_socket
def keyb(sock, text):
    click.echo(f"typing '{text}'")
    raw_text = util.decode_text(text)
    sock.cmd_keyb(raw_text)


if __name__ == "__main__":
    cli()
