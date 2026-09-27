"""Cliente S3-compatible (MinIO) para o módulo documentos.

`boto3` é síncrono (não há cliente async oficial para MinIO/S3 nesta stack) —
por isso cada chamada roda em thread separada via `asyncio.to_thread`, para
não bloquear o event loop enquanto o objeto é enviado/lido do MinIO.
"""
import asyncio

import boto3
from botocore.client import Config as BotoConfig

from app.config import Settings


class MinioStorage:
    """Upload, remoção e geração de URL assinada de objetos no bucket do tenant."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.bucket = settings.minio_bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.minio_endpoint_url,
            aws_access_key_id=settings.minio_root_user,
            aws_secret_access_key=settings.minio_root_password,
            config=BotoConfig(signature_version="s3v4"),
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

    async def gerar_url_assinada(self, key: str, expira_em_segundos: int = 3600) -> str:
        """Gera uma URL assinada válida por `expira_em_segundos` (padrão: 1h).

        Usa `minio_public_endpoint_url` quando configurado (host alcançável
        pelo navegador/app, diferente do host usado pelo backend para falar
        com o MinIO — ver nota em app/config.py) — troca o client só para
        assinar a URL, sem afetar upload/exclusão.
        """
        client = self.client
        if self.settings.minio_public_endpoint_url:
            client = boto3.client(
                "s3",
                endpoint_url=self.settings.minio_public_endpoint_url,
                aws_access_key_id=self.settings.minio_root_user,
                aws_secret_access_key=self.settings.minio_root_password,
                config=BotoConfig(signature_version="s3v4"),
            )
        return await asyncio.to_thread(
            client.generate_presigned_url,
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expira_em_segundos,
        )
