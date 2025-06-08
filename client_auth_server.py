import asyncio
import struct

LOGIN = b"ping"
PASSWORD = b"ping111111"

class Socks5Handler:
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer

    async def handle(self):
        try:
            await self.negotiate()
            await self.authenticate()
            await self.connect()
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.writer.close()
            await self.writer.wait_closed()

    async def negotiate(self):
        header = await self.reader.read(2)
        if len(header) < 2 or header[0] != 0x05:
            raise Exception("Invalid greeting")
        nmethods = header[1]
        methods = await self.reader.read(nmethods)
        # Respond that we require username/password auth
        self.writer.write(b"\x05\x02")
        await self.writer.drain()

    async def authenticate(self):
        ver = await self.reader.read(1)
        if ver != b"\x01":
            raise Exception("Invalid auth version")
        ulen = await self.reader.read(1)
        ulen = ulen[0]
        username = await self.reader.read(ulen)
        plen = await self.reader.read(1)
        plen = plen[0]
        password = await self.reader.read(plen)
        if username == LOGIN and password == PASSWORD:
            self.writer.write(b"\x01\x00")
        else:
            self.writer.write(b"\x01\x01")
            raise Exception("Auth failed")
        await self.writer.drain()

    async def connect(self):
        req = await self.reader.read(4)
        if req[1] != 0x01:
            raise Exception("Only CONNECT supported")
        addr_type = req[3]
        if addr_type == 1:  # IPv4
            addr = await self.reader.read(4)
            address = ".".join(str(b) for b in addr)
        elif addr_type == 3:  # Domain
            domain_len = (await self.reader.read(1))[0]
            domain = await self.reader.read(domain_len)
            address = domain.decode()
        else:
            raise Exception("Unsupported address type")
        port = struct.unpack('>H', await self.reader.read(2))[0]
        print(f"Connecting to {address}:{port}")

        try:
            remote_reader, remote_writer = await asyncio.open_connection(address, port)
        except Exception:
            self.writer.write(b"\x05\x01\x00\x01\x00\x00\x00\x00\x00\x00")
            return

        self.writer.write(b"\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00")
        await self.writer.drain()

        # Пробрасываем данные
        await asyncio.gather(
            self.pipe(self.reader, remote_writer),
            self.pipe(remote_reader, self.writer)
        )

    async def pipe(self, reader, writer):
        try:
            while not reader.at_eof():
                data = await reader.read(4096)
                if not data:
                    break
                writer.write(data)
                await writer.drain()
        except:
            pass
        finally:
            writer.close()

async def main():
    server = await asyncio.start_server(
        lambda r, w: Socks5Handler(r, w).handle(), "0.0.0.0", 1080
    )
    print("SOCKS5 proxy with auth running on port 1080")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
