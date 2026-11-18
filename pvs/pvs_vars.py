"""PVS authenticated vars polling module

Newer PVS firmware disables the telemetry WebSocket and instead exposes an authenticated
HTTPS endpoint (``/vars``) that must be polled. A session cookie is obtained by calling
``/auth?login`` with HTTP basic auth, and is then sent along with every ``/vars`` request.
"""

import asyncio
import logging
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)

HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403


class PVSAuthError(Exception):
    """Raised when the PVS rejects the supplied credentials"""


class PVSVars:
    """Polls the PVS ``/vars`` endpoint using an authenticated session"""

    def __init__(  # noqa: PLR0913
        self,
        host: str,
        username: str,
        password: str,
        port: int = 443,
        poll_interval: float = 10,
        match: str = "/",
        timeout: float = 30,
        retry_delay: float = 30,
    ) -> None:
        """Initialize the PVS vars client"""
        port = int(port)
        self.base_url = f"https://{host}" if port == 443 else f"https://{host}:{port}"  # noqa: PLR2004
        self.username = username
        self.password = password
        self.poll_interval = float(poll_interval)
        self.match = match
        # Built by hand so the match value is sent literally (e.g. "match=/"), as the PVS expects
        self.vars_path = f"/vars?match={match}"
        self.timeout = timeout
        self.retry_delay = retry_delay

        self.client: httpx.AsyncClient | None = None
        self.authenticated = False
        self.running = False
        self.on_message: Callable[[dict[str, str]], None] | None = None

    def _new_client(self) -> httpx.AsyncClient:
        # The PVS uses a self-signed certificate, so verification has to be disabled
        return httpx.AsyncClient(
            base_url=self.base_url,
            verify=False,  # noqa: S501
            timeout=self.timeout,
        )

    async def login(self) -> None:
        """Retrieve a new session from the PVS"""
        if self.client is not None:
            await self.client.aclose()
        self.client = self._new_client()
        self.authenticated = False

        msg = f"Logging in to PVS at {self.base_url} as {self.username}..."
        logger.info(msg)

        response = await self.client.get(
            "/auth?login",
            auth=httpx.BasicAuth(self.username, self.password),
        )

        if response.status_code in (HTTP_UNAUTHORIZED, HTTP_FORBIDDEN):
            msg = f"PVS rejected credentials for user {self.username} ({response.status_code})"
            raise PVSAuthError(msg)
        response.raise_for_status()

        if not self.client.cookies:
            logger.warning("PVS login succeeded but no session cookie was returned")

        self.authenticated = True
        logger.info("Logged in to PVS successfully")

    async def fetch(self) -> dict[str, str]:
        """Fetch vars from the PVS, re-authenticating once if the session has expired"""
        if not self.authenticated or self.client is None:
            await self.login()

        response = await self.client.get(self.vars_path)

        if response.status_code in (HTTP_UNAUTHORIZED, HTTP_FORBIDDEN):
            logger.info("PVS session expired, logging in again")
            await self.login()
            response = await self.client.get(self.vars_path)

        response.raise_for_status()
        return self.parse(response.json())

    @staticmethod
    def parse(payload: dict) -> dict[str, str]:
        """Convert the ``values`` list into a ``{name: value}`` dict"""
        return {
            item["name"]: item["value"]
            for item in payload.get("values", [])
            if isinstance(item, dict) and "name" in item and "value" in item
        }

    async def run(self) -> None:
        """Poll the PVS until stopped"""
        self.running = True
        loop = asyncio.get_running_loop()

        while self.running:
            started = loop.time()
            delay = self.poll_interval

            try:
                data = await self.fetch()
                if self.on_message is None:
                    msg = f"Received {len(data)} vars from PVS"
                    logger.info(msg)
                else:
                    self.on_message(data)
            except PVSAuthError:
                logger.exception("PVS authentication failed, check the PVS username/password")
                self.authenticated = False
                delay = self.retry_delay
            except (httpx.HTTPError, ValueError) as e:
                msg = f"Error polling PVS: {e!r}"
                logger.error(msg)  # noqa: TRY400
                self.authenticated = False
                delay = self.retry_delay
            except Exception:
                logger.exception("Unexpected error polling PVS")
                delay = self.retry_delay

            if not self.running:
                break

            elapsed = loop.time() - started
            await asyncio.sleep(max(0.0, delay - elapsed))

    async def stop(self) -> None:
        """Stop polling and close the HTTP client"""
        logger.info("Stopping PVS poller...")
        self.running = False
        if self.client is not None:
            await self.client.aclose()
            self.client = None
        self.authenticated = False
