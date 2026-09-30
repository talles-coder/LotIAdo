"""Geo domain exceptions."""


class FeicaoNaoEncontradaError(Exception):
    """Raised when a feição id does not match an active feição in the tenant."""


class LoteSemGeometriaError(Exception):
    """Raised when a spatial query needs a lote geometry that was not drawn yet."""


class AreaInvalidaError(Exception):
    """Raised when the GeoJSON area is not a valid Polygon/MultiPolygon."""
