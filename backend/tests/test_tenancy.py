"""Tests for the tenancy module."""
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.tenancy.domain.models import Tenant


@pytest.mark.asyncio
async def test_create_tenant(db_session: AsyncSession):
    """Test creating a tenant."""
    tenant = Tenant(
        name="Test Tenant",
        slug="test-tenant",
        config={"color_scheme": "light"}
    )
    db_session.add(tenant)
    await db_session.commit()

    result = await db_session.execute(
        select(Tenant).where(Tenant.slug == "test-tenant")
    )
    fetched_tenant = result.scalar_one_or_none()

    assert fetched_tenant is not None
    assert fetched_tenant.name == "Test Tenant"
    assert fetched_tenant.slug == "test-tenant"
    assert fetched_tenant.config == {"color_scheme": "light"}


@pytest.mark.asyncio
async def test_tenant_has_timestamps(db_session: AsyncSession):
    """Test that tenant has created_at and updated_at timestamps."""
    tenant = Tenant(name="Tenant With Timestamps", slug="tenant-timestamps")
    db_session.add(tenant)
    await db_session.commit()

    result = await db_session.execute(
        select(Tenant).where(Tenant.slug == "tenant-timestamps")
    )
    fetched_tenant = result.scalar_one_or_none()

    assert fetched_tenant.created_at is not None
    assert fetched_tenant.updated_at is not None


@pytest.mark.asyncio
async def test_tenant_slug_unique(db_session: AsyncSession):
    """Test that tenant slug is unique."""
    tenant1 = Tenant(name="Tenant 1", slug="unique-slug")
    db_session.add(tenant1)
    await db_session.commit()

    tenant2 = Tenant(name="Tenant 2", slug="unique-slug")
    db_session.add(tenant2)

    with pytest.raises(Exception):
        await db_session.commit()
