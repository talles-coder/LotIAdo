"""Cliente S3-compatible (MinIO) para o módulo documentos.

`boto3` é síncrono (não há cliente async oficial para MinIO/S3 nesta stack) —
por isso cada chamada roda em thread separada via `asyncio.to_thread`, para
não bloquear o event loop enquanto o objeto é enviado/lido do MinIO.
"""
import asyncio

import boto3
from botocore.client import Config as BotoConfig

from app.config import Settings


def _criar_client(endpoint_url: str, access_key: str, secret_key: str):
    client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=BotoConfig(signature_version="s3v4"),
    )
    # Sem isso, upload trava em "Connection was closed before we received a
    # valid response" contra servers S3-compatible mais estritos (ex.
    # adobe/s3mock, usado no CI e no docker-compose local por causa do
    # gating do MinIO — ver docs/03-decisoes-tecnicas.md) rodando atrás do
    # port-forward do Docker Desktop no Windows: o boto3 manda o header
    # `Expect: 100-continue` mas não espera a resposta 100 antes de já
    # mandar o corpo, e o NAT do Docker Desktop reordena os pacotes o
    # suficiente pra derrubar a conexão. Tirar o header faz o boto3 mandar
    # o corpo direto, sem o handshake — inofensivo contra qualquer S3
    # real (é só uma otimização opcional do protocolo).
    client.meta.events.register("before-send.s3.*", _remover_expect_header)
    return client


def _remover_expect_header(request, **kwargs):
    request.headers.pop("Expect", None)


class MinioStorage:
    """Upload, remoção e geração de URL assinada de objetos no bucket do tenant."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.bucket = settings.minio_bucket
        self.client = _criar_client(
            settings.minio_endpoint_url, settings.minio_root_user, settings.minio_root_password
        )

    async def upload(self, key: str, conteudo: bytes, content_type: str) -> None:
        await asyncio.to_thread(
            self.client.put_object,
            Bucket=self.bucket,
            Key=key,
            Body=conteudo,
            ContentType=content_type,
        )

    async def excluir(self, key: str) -> None:
        await asyncio.to_thread(self.client.delete_object, Bucket=self.bucket, Key=key)

    async def baixar(self, key: str) -> bytes:
        """Baixa o conteúdo do objeto (usado pelo worker de ingestão, FASE7-IMPL-01)."""
        objeto = await asyncio.to_thread(self.client.get_object, Bucket=self.bucket, Key=key)
        return await asyncio.to_thread(objeto["Body"].read)

    async def gerar_url_assinada(self, key: str, expira_em_segundos: int = 3600) -> str:
        """Gera uma URL assinada válida por `expira_em_segundos` (padrão: 1h).

        Usa `minio_public_endpoint_url` quando configurado (host alcançável
        pelo navegador/app, diferente do host usado pelo backend para falar
        com o MinIO — ver nota em app/config.py) — troca o client só para
        assinar a URL, sem afetar upload/exclusão.
        """
        client = self.client
        if self.settings.minio_public_endpoint_url:
            client = _criar_client(
                self.settings.minio_public_endpoint_url,
                self.settings.minio_root_user,
                self.settings.minio_root_password,
            )
        return await asyncio.to_thread(
            client.generate_presigned_url,
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expira_em_segundos,
        )
