import ssl

import httpx
import truststore


# Корпоративный TLS-proxy подменяет сертификаты: берём доверенные корни
# из системного хранилища Windows вместо certifi. Проверку не отключаем.
SSL_CONTEXT = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)


async def fetch_url(url: str) -> dict:
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=20.0,
        verify=SSL_CONTEXT,
        headers={"User-Agent": "regulatory-research-agent/0.1"},
    ) as client:
        response = await client.get(url)

        return {
            "requested_url": url,
            "final_url": str(response.url),
            "status_code": response.status_code,
            "content_type": response.headers.get("content-type"),
            "content": response.content,
        }