"""Create SQLAlchemy database connection engine."""

import asyncio
import socket
import threading
from socket import gethostbyname

import asyncssh
import sqlalchemy

from config import CONFIG, SSH_KNOWN_HOSTS, get_logger

logger = get_logger(__name__)


class PostgresCon:
    """Class for managing the connection to PostgreSQL."""

    def __init__(self, config_name: str, db_ip: str, db_port: str) -> None:
        """Initialize the PostgreSQL connection.

        Args:
            db_name (str): Name of the database.
            db_ip (str): IP address of the database server.
            db_port (str): Port number of the database server.

        """
        self.db_ip = db_ip
        self.db_port = db_port
        self.engine: sqlalchemy.engine.Engine

        try:
            self.db_name = CONFIG[config_name]["db_name"]
            self.db_pass = CONFIG[config_name]["db_password"]
            self.db_user = CONFIG[config_name]["db_user"]
        except KeyError as error:
            logger.exception(f"Loading db_auth for {config_name}, error: {error}")
            raise

    def set_engine(self) -> None:
        """Set up the SQLAlchemy engine."""
        try:
            if self.db_pass:
                db_login = f"postgresql+psycopg://{self.db_user}:{self.db_pass}"
            else:
                db_login = f"postgresql+psycopg://{self.db_user}"
            db_uri = f"{db_login}@{self.db_ip}:{self.db_port}/{self.db_name}"
            self.engine = sqlalchemy.create_engine(
                db_uri,
                pool_pre_ping=True,
                pool_recycle=1000,
                pool_size=10,
                max_overflow=5,
                pool_timeout=20,
                connect_args={
                    "connect_timeout": 15,
                    "application_name": "appgoblin",
                    "options": "-c lock_timeout=5000 -c statement_timeout=60000",
                    "keepalives": 1,
                    "keepalives_idle": 30,
                    "keepalives_interval": 10,
                    "keepalives_count": 5,
                },
            )
        except Exception as error:
            logger.exception(
                f"Failed to connect {self.db_name} @ {self.db_ip}, error: {error}",
            )
            raise


def manage_tunnel_thread(
    host: str,
    os_user: str,
    ssh_port: int,
    remote_port: int,
    ssh_pkey: str,
    ssh_pkey_password: str,
) -> int:
    """Manage SSH tunnel in a separate thread."""
    result = {}

    def runner() -> None:
        async def main() -> None:
            async with asyncssh.connect(
                host,
                username=os_user,
                port=ssh_port,
                known_hosts=SSH_KNOWN_HOSTS.as_posix(),
                client_keys=ssh_pkey,
                passphrase=ssh_pkey_password,
                family=socket.AF_INET,
            ) as conn:
                listener = await conn.forward_local_port(
                    listen_host="localhost",
                    listen_port=0,
                    dest_host="127.0.0.1",
                    dest_port=remote_port,
                )
                result["port"] = listener.get_port()
                await listener.wait_closed()

        asyncio.run(main())

    t = threading.Thread(target=runner, daemon=True)
    t.start()
    while "port" not in result:
        pass  # wait for listener to be ready
    return result["port"]


def start_ssh_tunnel(server_name: str) -> int:
    """Start an SSH tunnel to the remote database server."""
    ssh_port = CONFIG[server_name].get("ssh_port", 22)
    remote_port = CONFIG[server_name].get("remote_port", 5432)
    host = CONFIG[server_name]["host"]
    os_user = CONFIG[server_name]["os_user"]
    ssh_pkey = CONFIG[server_name].get("ssh_pkey")
    ssh_pkey_password = CONFIG[server_name].get("ssh_pkey_password")
    ssh_local_port = manage_tunnel_thread(
        host, os_user, ssh_port, remote_port, ssh_pkey, ssh_pkey_password
    )
    return ssh_local_port


def get_db_connection(server_name: str = "madrone") -> PostgresCon:
    """Get a database connection, optionally using an SSH tunnel.

    Args:
        server_name (str): The name of the server configuration to use.

    Returns:
        PostgresCon: A PostgreSQL connection object.

    """
    use_ssh = CONFIG[server_name].get("use_ssh", False)

    if use_ssh:
        ssh_local_port = start_ssh_tunnel(server_name)
        host = "127.0.0.1"
        db_port = str(ssh_local_port)
    else:
        db_port = CONFIG[server_name].get("remote_port", 5432)
        host = CONFIG[server_name]["host"]

    conn = PostgresCon(server_name, host, db_port)
    conn.set_engine()

    return conn


def get_host_ip(hostname: str) -> str:
    """Convert hostname to IPv4 address if needed."""
    # Check if hostname is already an IPv4 address
    if all(part.isdigit() and 0 <= int(part) <= 255 for part in hostname.split(".")):
        return hostname
    ip_address = gethostbyname(hostname)
    logger.info(f"Resolved {hostname} to {ip_address}")
    return ip_address
