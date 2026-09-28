#!/bin/sh
set -eu

# adobe/s3mock não exige autenticação para operações administrativas — um PUT
# simples no path do bucket já cria (200) ou confirma que já existe (409,
# BucketAlreadyOwnedByYou); qualquer outro status é erro de verdade. Ver
# docs/03-decisoes-tecnicas.md sobre a troca do MinIO real pelo s3mock (a
# imagem quay.io/minio/minio passou a exigir login em 2026, quebrando pull
# anônimo em CI e em clone novo).
status=$(curl -s -o /dev/null -w '%{http_code}' -X PUT "http://minio:9090/${MINIO_BUCKET}")
if [ "$status" = "200" ] || [ "$status" = "409" ]; then
  echo "Bucket '${MINIO_BUCKET}' pronto (status ${status})."
else
  echo "Falha ao criar bucket '${MINIO_BUCKET}' (status ${status})." >&2
  exit 1
fi
