"""Bulk lote import from a CSV, with a column mapping supplied by the user (no AI).

O usuário decide, na tela de mapeamento, qual coluna do CSV corresponde a
cada campo do sistema (`identificacao`, `quadra`, `area_m2`, `preco`) — o
CSV pode ter colunas em qualquer ordem ou nome. Linhas inválidas (ex.:
identificação vazia, preço não numérico) são reportadas por número de linha
sem abortar o restante do import.
"""
import csv
import io
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.loteamentos_lotes.domain.exceptions import MapeamentoDeImportacaoInvalidoError
from app.loteamentos_lotes.domain.models import Lote
from app.loteamentos_lotes.infrastructure.repository import create_lotes_em_lote

CAMPO_OBRIGATORIO = "identificacao"
CAMPOS_MAPEAVEIS = ("identificacao", "quadra", "area_m2", "preco")


class _LinhaInvalidaError(Exception):
    """Erro interno: uma linha específica do CSV não pôde virar um Lote válido."""


@dataclass
class ErroDeImportacao:
    linha: int
    erro: str


@dataclass
class ResultadoDeImportacao:
    total_linhas: int
    importados: int
    erros: list[ErroDeImportacao] = field(default_factory=list)


def extrair_cabecalhos(conteudo_csv: str) -> list[str]:
    """Retorna os cabeçalhos (primeira linha) de um CSV, para o usuário mapear as colunas."""
    reader = csv.reader(io.StringIO(conteudo_csv))
    try:
        cabecalhos = next(reader)
    except StopIteration:
        return []
    return [cabecalho.strip() for cabecalho in cabecalhos]


class LoteImportService:
    """Importa lotes em lote a partir de um CSV, usando um mapeamento de colunas feito por um humano."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def importar(
        self,
        tenant_id: UUID,
        loteamento_id: UUID,
        conteudo_csv: str,
        mapeamento: dict[str, str],
    ) -> ResultadoDeImportacao:
        """Cria em lote os lotes válidos do CSV; linhas inválidas são reportadas, não abortam o import."""
        coluna_identificacao = mapeamento.get(CAMPO_OBRIGATORIO)
        if not coluna_identificacao:
            raise MapeamentoDeImportacaoInvalidoError(
                f"Mapeamento precisa indicar a coluna do CSV para o campo '{CAMPO_OBRIGATORIO}'"
            )

        reader = csv.DictReader(io.StringIO(conteudo_csv))
        if reader.fieldnames is None:
            raise MapeamentoDeImportacaoInvalidoError("CSV vazio ou sem cabeçalho")

        colunas_mapeadas = set(mapeamento.values())
        colunas_ausentes = colunas_mapeadas - set(reader.fieldnames)
        if colunas_ausentes:
            raise MapeamentoDeImportacaoInvalidoError(
                f"Coluna(s) mapeada(s) não encontrada(s) no CSV: {', '.join(sorted(colunas_ausentes))}"
            )

        lotes: list[Lote] = []
        erros: list[ErroDeImportacao] = []
        total_linhas = 0

        # `start=2`: a linha 1 do arquivo é o cabeçalho, então a primeira linha de dados é a 2.
        for numero_linha, linha in enumerate(reader, start=2):
            total_linhas += 1
            try:
                lote = self._linha_para_lote(tenant_id, loteamento_id, linha, mapeamento)
            except _LinhaInvalidaError as exc:
                erros.append(ErroDeImportacao(linha=numero_linha, erro=str(exc)))
                continue
            lotes.append(lote)

        if lotes:
            await create_lotes_em_lote(self.db, lotes)

        return ResultadoDeImportacao(total_linhas=total_linhas, importados=len(lotes), erros=erros)

    def _linha_para_lote(
        self,
        tenant_id: UUID,
        loteamento_id: UUID,
        linha: dict[str, str | None],
        mapeamento: dict[str, str],
    ) -> Lote:
        identificacao = _valor(linha, mapeamento.get("identificacao"))
        if not identificacao:
            raise _LinhaInvalidaError("Campo 'identificacao' obrigatório está vazio")

        quadra = _valor(linha, mapeamento.get("quadra"))
        area_m2 = _decimal(_valor(linha, mapeamento.get("area_m2")), "area_m2")
        preco = _decimal(_valor(linha, mapeamento.get("preco")), "preco")

        return Lote(
            tenant_id=tenant_id,
            loteamento_id=loteamento_id,
            identificacao=identificacao,
            quadra=quadra,
            area_m2=area_m2,
            preco=preco,
            caracteristicas={},
        )


def _valor(linha: dict[str, str | None], coluna: str | None) -> str | None:
    if coluna is None:
        return None
    valor = linha.get(coluna)
    if valor is None:
        return None
    valor = valor.strip()
    return valor or None


def _decimal(valor: str | None, campo: str) -> Decimal | None:
    if valor is None:
        return None
    try:
        return Decimal(valor.replace(",", "."))
    except InvalidOperation:
        raise _LinhaInvalidaError(f"Campo '{campo}' com valor inválido: '{valor}'")
