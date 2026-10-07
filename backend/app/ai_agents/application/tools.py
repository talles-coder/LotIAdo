"""Tools do agente de IA: consulta (FASE9-IMPL-01) e ação (FASE9-IMPL-03).

Cada tool é uma função fina que chama um serviço de aplicação já existente e
formata o resultado para o LLM — nunca gera SQL nem acessa repositórios
diretamente. Exceções de "não encontrado"/"inválido" dos serviços são
capturadas e convertidas em `encontrado=False` + `mensagem`, para o agente
informar a ausência do dado em vez de propagar um erro.

As tools de **ação** (`cancelar_reserva`, `alterar_preco_lote`,
`alterar_responsavel_lote`) mudam estado real (mesmos serviços usados pelas
rotas HTTP normais, com a mesma auditoria automática de FASE1-IMPL-04) — o
que impede sua execução direta pelo agente não é nada nesta função, e sim o
`ToolSpec.acao=True` no `tool_registry`, aplicado em `AgenteService`.
"""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agents.domain.schemas import (
    AlterarPrecoLoteInput,
    AlterarPrecoLoteOutput,
    AlterarResponsavelLoteInput,
    AlterarResponsavelLoteOutput,
    BuscarDocumentosInput,
    BuscarDocumentosOutput,
    BuscarLotesInput,
    BuscarLotesOutput,
    CancelarReservaInput,
    CancelarReservaOutput,
    ChunkResumo,
    ClienteResumo,
    ConsultarClientesInput,
    ConsultarClientesOutput,
    ConsultarCondicoesComerciaisInput,
    ConsultarCondicoesComerciaisOutput,
    ConsultarCorretoresInput,
    ConsultarCorretoresOutput,
    ConsultarDisponibilidadeInput,
    ConsultarDisponibilidadeOutput,
    ConsultarLoteInput,
    ConsultarLoteOutput,
    ConsultarVendasInput,
    ConsultarVendasOutput,
    CorretorResumo,
    DistanciaEntreLotesInput,
    DistanciaEntreLotesOutput,
    LoteResumo,
    LotesDentroDeInput,
    LotesDeEsquinaInput,
    LotesGeoOutput,
    LotesProximosDeInput,
    ReservaResumo,
)
from app.ai_rag.application.busca_service import BuscaService
from app.ai_rag.domain.exceptions import LoteamentoDaBuscaNaoEncontradoError, LoteDaBuscaNaoEncontradoError
from app.clientes.application.cliente_service import ClienteService
from app.clientes.domain.exceptions import ClienteNaoEncontradoError
from app.corretores.application.corretor_service import CorretorService
from app.corretores.domain.exceptions import CorretorNaoEncontradoError
from app.geo.application.geo_query_service import GeoQueryService
from app.geo.domain.exceptions import AreaInvalidaError, FeicaoNaoEncontradaError, LoteSemGeometriaError
from app.loteamentos_lotes.application.lote_service import LoteService
from app.loteamentos_lotes.domain.exceptions import LoteNaoEncontradoError
from app.loteamentos_lotes.domain.models import Lote
from app.loteamentos_lotes.domain.state_machine import LoteStatus
from app.vendas_reservas.application.reserva_service import ReservaService
from app.vendas_reservas.domain.exceptions import ReservaNaoEncontradaError, ReservaNaoEstaAtivaError


def _lote_resumo(lote: Lote) -> LoteResumo:
    return LoteResumo.model_validate(lote)


async def consultar_lote(db: AsyncSession, tenant_id: UUID, entrada: ConsultarLoteInput) -> ConsultarLoteOutput:
    """Detalhes de um lote específico."""
    try:
        lote = await LoteService(db).obter(tenant_id, entrada.lote_id)
    except LoteNaoEncontradoError:
        return ConsultarLoteOutput(encontrado=False, mensagem="Lote não encontrado.")
    return ConsultarLoteOutput(encontrado=True, lote=_lote_resumo(lote))


async def buscar_lotes(db: AsyncSession, tenant_id: UUID, entrada: BuscarLotesInput) -> BuscarLotesOutput:
    """Lotes de um loteamento, filtrados por status/área mínima/preço máximo."""
    lotes = await LoteService(db).listar(tenant_id, entrada.loteamento_id)
    if entrada.status is not None:
        lotes = [lote for lote in lotes if lote.status == entrada.status]
    if entrada.area_m2_min is not None:
        lotes = [lote for lote in lotes if lote.area_m2 is not None and lote.area_m2 >= entrada.area_m2_min]
    if entrada.preco_max is not None:
        lotes = [lote for lote in lotes if lote.preco is not None and lote.preco <= entrada.preco_max]
    resumos = [_lote_resumo(lote) for lote in lotes]
    return BuscarLotesOutput(total=len(resumos), lotes=resumos)


async def consultar_disponibilidade(
    db: AsyncSession, tenant_id: UUID, entrada: ConsultarDisponibilidadeInput
) -> ConsultarDisponibilidadeOutput:
    """Status atual de um lote e se ele está disponível para reserva."""
    try:
        lote = await LoteService(db).obter(tenant_id, entrada.lote_id)
    except LoteNaoEncontradoError:
        return ConsultarDisponibilidadeOutput(encontrado=False, mensagem="Lote não encontrado.")
    return ConsultarDisponibilidadeOutput(
        encontrado=True, status=lote.status, disponivel=lote.status == LoteStatus.DISPONIVEL
    )


async def lotes_de_esquina(db: AsyncSession, tenant_id: UUID, entrada: LotesDeEsquinaInput) -> LotesGeoOutput:
    """Lotes que tocam ao menos duas ruas distintas do loteamento."""
    lotes = await GeoQueryService(db).lotes_de_esquina(
        tenant_id, entrada.loteamento_id, status=entrada.status, area_m2_min=entrada.area_m2_min
    )
    resumos = [_lote_resumo(lote) for lote in lotes]
    return LotesGeoOutput(encontrado=True, total=len(resumos), lotes=resumos)


async def lotes_proximos_de(db: AsyncSession, tenant_id: UUID, entrada: LotesProximosDeInput) -> LotesGeoOutput:
    """Lotes a até `raio_m` metros de uma feição de referência (rua, área verde...)."""
    try:
        lotes = await GeoQueryService(db).lotes_proximos_de(
            tenant_id,
            entrada.feicao_id,
            entrada.raio_m,
            status=entrada.status,
            area_m2_min=entrada.area_m2_min,
        )
    except FeicaoNaoEncontradaError:
        return LotesGeoOutput(encontrado=False, mensagem="Feição de referência não encontrada.")
    resumos = [_lote_resumo(lote) for lote in lotes]
    return LotesGeoOutput(encontrado=True, total=len(resumos), lotes=resumos)


async def lotes_dentro_de(db: AsyncSession, tenant_id: UUID, entrada: LotesDentroDeInput) -> LotesGeoOutput:
    """Lotes totalmente contidos numa área GeoJSON (Polygon/MultiPolygon)."""
    try:
        lotes = await GeoQueryService(db).lotes_dentro_de(
            tenant_id,
            entrada.area_geojson,
            loteamento_id=entrada.loteamento_id,
            status=entrada.status,
            area_m2_min=entrada.area_m2_min,
        )
    except AreaInvalidaError as exc:
        return LotesGeoOutput(encontrado=False, mensagem=str(exc))
    resumos = [_lote_resumo(lote) for lote in lotes]
    return LotesGeoOutput(encontrado=True, total=len(resumos), lotes=resumos)


async def distancia_entre_lotes(
    db: AsyncSession, tenant_id: UUID, entrada: DistanciaEntreLotesInput
) -> DistanciaEntreLotesOutput:
    """Distância mínima em metros entre os perímetros de dois lotes."""
    try:
        distancia_m = await GeoQueryService(db).distancia_entre_lotes(
            tenant_id, entrada.lote_a_id, entrada.lote_b_id
        )
    except LoteNaoEncontradoError:
        return DistanciaEntreLotesOutput(encontrado=False, mensagem="Um dos lotes não foi encontrado.")
    except LoteSemGeometriaError:
        return DistanciaEntreLotesOutput(
            encontrado=False, mensagem="Um dos lotes ainda não tem geometria desenhada."
        )
    return DistanciaEntreLotesOutput(encontrado=True, distancia_m=distancia_m)


async def consultar_clientes(
    db: AsyncSession, tenant_id: UUID, entrada: ConsultarClientesInput
) -> ConsultarClientesOutput:
    """Um cliente específico (`cliente_id`) ou todos os clientes do tenant."""
    service = ClienteService(db)
    if entrada.cliente_id is not None:
        try:
            cliente = await service.obter(tenant_id, entrada.cliente_id)
        except ClienteNaoEncontradoError:
            return ConsultarClientesOutput(encontrado=False, mensagem="Cliente não encontrado.")
        clientes = [cliente]
    else:
        clientes = await service.listar(tenant_id)
    resumos = [ClienteResumo.model_validate(cliente) for cliente in clientes]
    return ConsultarClientesOutput(encontrado=True, total=len(resumos), clientes=resumos)


async def consultar_corretores(
    db: AsyncSession, tenant_id: UUID, entrada: ConsultarCorretoresInput
) -> ConsultarCorretoresOutput:
    """Um corretor específico (`corretor_id`) ou todos os corretores do tenant."""
    service = CorretorService(db)
    if entrada.corretor_id is not None:
        try:
            corretor = await service.obter(tenant_id, entrada.corretor_id)
        except CorretorNaoEncontradoError:
            return ConsultarCorretoresOutput(encontrado=False, mensagem="Corretor não encontrado.")
        corretores = [corretor]
    else:
        corretores = await service.listar(tenant_id)
    resumos = [CorretorResumo.model_validate(corretor) for corretor in corretores]
    return ConsultarCorretoresOutput(encontrado=True, total=len(resumos), corretores=resumos)


async def consultar_vendas(db: AsyncSession, tenant_id: UUID, entrada: ConsultarVendasInput) -> ConsultarVendasOutput:
    """A reserva/venda pelo seu id, ou a reserva/venda ativa de um lote."""
    service = ReservaService(db)
    try:
        if entrada.reserva_id is not None:
            reserva = await service.obter(tenant_id, entrada.reserva_id)
        elif entrada.lote_id is not None:
            reserva = await service.obter_atual_por_lote(tenant_id, entrada.lote_id)
        else:
            return ConsultarVendasOutput(
                encontrado=False, mensagem="Informe `reserva_id` ou `lote_id` para consultar."
            )
    except ReservaNaoEncontradaError:
        return ConsultarVendasOutput(encontrado=False, mensagem="Nenhuma reserva/venda encontrada.")
    return ConsultarVendasOutput(encontrado=True, reserva=ReservaResumo.model_validate(reserva))


async def buscar_documentos(
    db: AsyncSession, tenant_id: UUID, entrada: BuscarDocumentosInput
) -> BuscarDocumentosOutput:
    """Trechos de documentos mais relevantes para a pergunta, via busca semântica (RAG)."""
    try:
        resultados = await BuscaService(db).buscar(
            tenant_id,
            entrada.pergunta,
            loteamento_id=entrada.loteamento_id,
            lote_id=entrada.lote_id,
            top_k=entrada.top_k,
        )
    except (LoteamentoDaBuscaNaoEncontradoError, LoteDaBuscaNaoEncontradoError) as exc:
        return BuscarDocumentosOutput(encontrado=False, mensagem=str(exc) or "Loteamento/lote informado não existe.")
    if not resultados:
        return BuscarDocumentosOutput(encontrado=False, mensagem="Nenhum documento relevante encontrado.")
    resumos = [
        ChunkResumo(
            documento_id=resultado.documento_id,
            documento_nome=resultado.documento_nome,
            texto=resultado.texto,
            score=resultado.score,
        )
        for resultado in resultados
    ]
    return BuscarDocumentosOutput(encontrado=True, resultados=resumos)


async def consultar_condicoes_comerciais(
    db: AsyncSession, tenant_id: UUID, entrada: ConsultarCondicoesComerciaisInput
) -> ConsultarCondicoesComerciaisOutput:
    """Preço, área e características comerciais de um lote."""
    try:
        lote = await LoteService(db).obter(tenant_id, entrada.lote_id)
    except LoteNaoEncontradoError:
        return ConsultarCondicoesComerciaisOutput(encontrado=False, mensagem="Lote não encontrado.")
    return ConsultarCondicoesComerciaisOutput(
        encontrado=True,
        preco=lote.preco,
        area_m2=lote.area_m2,
        caracteristicas=lote.caracteristicas or {},
    )


async def cancelar_reserva(db: AsyncSession, tenant_id: UUID, entrada: CancelarReservaInput) -> CancelarReservaOutput:
    """Cancela uma reserva ativa, devolvendo o lote para disponível. Ação sensível: exige confirmação humana."""
    try:
        reserva = await ReservaService(db).cancelar(tenant_id, entrada.reserva_id)
    except ReservaNaoEncontradaError:
        return CancelarReservaOutput(encontrado=False, mensagem="Reserva não encontrada.")
    except ReservaNaoEstaAtivaError:
        return CancelarReservaOutput(encontrado=False, mensagem="Reserva não está ativa (já foi cancelada ou convertida em venda).")
    return CancelarReservaOutput(encontrado=True, reserva=ReservaResumo.model_validate(reserva))


async def alterar_preco_lote(db: AsyncSession, tenant_id: UUID, entrada: AlterarPrecoLoteInput) -> AlterarPrecoLoteOutput:
    """Altera o preço de um lote. Ação sensível: exige confirmação humana."""
    try:
        lote = await LoteService(db).atualizar(tenant_id, entrada.lote_id, preco=entrada.preco)
    except LoteNaoEncontradoError:
        return AlterarPrecoLoteOutput(encontrado=False, mensagem="Lote não encontrado.")
    return AlterarPrecoLoteOutput(encontrado=True, lote=_lote_resumo(lote))


async def alterar_responsavel_lote(
    db: AsyncSession, tenant_id: UUID, entrada: AlterarResponsavelLoteInput
) -> AlterarResponsavelLoteOutput:
    """Altera o corretor responsável por um lote. Ação sensível: exige confirmação humana."""
    try:
        await CorretorService(db).obter(tenant_id, entrada.corretor_id)
    except CorretorNaoEncontradoError:
        return AlterarResponsavelLoteOutput(encontrado=False, mensagem="Corretor não encontrado.")
    try:
        lote = await LoteService(db).atualizar(tenant_id, entrada.lote_id, corretor_id=entrada.corretor_id)
    except LoteNaoEncontradoError:
        return AlterarResponsavelLoteOutput(encontrado=False, mensagem="Lote não encontrado.")
    return AlterarResponsavelLoteOutput(encontrado=True, lote=_lote_resumo(lote))
