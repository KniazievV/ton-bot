import asyncio
import logging

log = logging.getLogger(__name__)


async def _handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        await reader.read(2048)
        body = b"ok"
        resp = (
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: text/plain; charset=utf-8\r\n"
            b"Content-Length: 2\r\n"
            b"Connection: close\r\n"
            b"\r\n"
            + body
        )
        writer.write(resp)
        await writer.drain()
    except Exception:
        log.exception("health handler error")
    finally:
        writer.close()
        await writer.wait_closed()


async def run_healthcheck_server(port: int) -> None:
    server = await asyncio.start_server(_handle, host="0.0.0.0", port=port)
    log.info("Health server listening on 0.0.0.0:%s", port)
    async with server:
        await server.serve_forever()
