FROM postgis/postgis:16-3.4

# postgis/postgis is built on the official postgres image, which already
# configures the PGDG apt repository, so the prebuilt pgvector package for
# this Postgres major version is available directly.
# -o Acquire::Check-Valid-Until=false works around the base image's Debian
# bullseye "debian-security" mirror shipping an expired Release file; GPG
# signature verification of packages is unaffected.
RUN apt-get update -o Acquire::Check-Valid-Until=false \
    && apt-get install -y --no-install-recommends postgresql-16-pgvector \
    && rm -rf /var/lib/apt/lists/*
