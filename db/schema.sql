-- Trade-rules encyclopedia — initial PostgreSQL schema (v0.1, 2026-09-06)
-- Principles encoded here: every fact carries its source, quote and snapshot; rates live in a
-- structured table; demo/test rows are flagged; nothing is published without a status.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE fact_status AS ENUM ('verified', 'stale', 'not_found', 'unavailable', 'prohibited', 'estimate', 'confirm_with_broker');
CREATE TYPE source_status AS ENUM ('to_verify', 'verified', 'unstable', 'retired');
CREATE TYPE shipment_mode AS ENUM ('b2b', 'parcel');
CREATE TYPE page_status AS ENUM ('generating', 'published', 'rebuilding', 'failed');
CREATE TYPE rate_kind AS ENUM ('import_mfn', 'import_pref', 'import_vat', 'import_excise', 'export_duty', 'export_quota', 'de_minimis');
CREATE TYPE sanction_scope AS ENUM ('goods_prohibited', 'persons_listed', 'payments_restricted', 'sectoral', 'none');

CREATE TABLE countries (
  code        CHAR(2) PRIMARY KEY,               -- ISO 3166-1 alpha-2
  name        JSONB NOT NULL,                    -- {"ru": "...", "en": "...", ...}
  languages   TEXT[] NOT NULL DEFAULT '{}',
  notes       TEXT
);

CREATE TABLE product_groups (
  hs6         CHAR(6) PRIMARY KEY,
  name        JSONB NOT NULL,
  parent_hs4  CHAR(4)
);

CREATE TABLE corridors (
  id            TEXT PRIMARY KEY,                -- e.g. 'cn-ca'
  from_country  CHAR(2) NOT NULL REFERENCES countries(code),
  to_country    CHAR(2) NOT NULL REFERENCES countries(code),
  modes         shipment_mode[] NOT NULL DEFAULT '{b2b}',
  languages     TEXT[] NOT NULL DEFAULT '{ru,en}',
  is_sanctioned BOOLEAN NOT NULL DEFAULT FALSE,   -- any of CA/US/EU/UK regimes applies to either side
  UNIQUE (from_country, to_country)
);

-- Whitelist of official sources. Mirrors data/sources.yaml; the YAML is the editable master.
CREATE TABLE sources (
  id            TEXT PRIMARY KEY,                -- e.g. 'ca-cbsa'
  country       CHAR(2) REFERENCES countries(code),  -- NULL for international / sanctions authorities
  agency        TEXT NOT NULL,
  domain        TEXT NOT NULL,
  path_prefix   TEXT,
  topics        TEXT[] NOT NULL DEFAULT '{}',
  priority      SMALLINT NOT NULL DEFAULT 2,
  status        source_status NOT NULL DEFAULT 'to_verify',
  last_checked  TIMESTAMPTZ
);

CREATE TABLE source_urls (
  id          BIGSERIAL PRIMARY KEY,
  source_id   TEXT NOT NULL REFERENCES sources(id),
  url         TEXT NOT NULL UNIQUE,
  topic       TEXT NOT NULL,
  language    TEXT,
  active      BOOLEAN NOT NULL DEFAULT TRUE
);

-- Immutable snapshots of fetched pages. Content stored on disk/object storage, referenced by path.
CREATE TABLE snapshots (
  id            BIGSERIAL PRIMARY KEY,
  source_url_id BIGINT NOT NULL REFERENCES source_urls(id),
  fetched_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  http_status   INT,
  content_hash  TEXT,
  content_path  TEXT,
  changed       BOOLEAN NOT NULL DEFAULT FALSE     -- hash differs from previous snapshot of the same URL
);
CREATE INDEX ON snapshots (source_url_id, fetched_at DESC);

-- A single sourced statement. The core rule: no quote -> no fact.
CREATE TABLE facts (
  id            BIGSERIAL PRIMARY KEY,
  corridor_id   TEXT REFERENCES corridors(id),      -- NULL for country-level facts reused across corridors
  country       CHAR(2) REFERENCES countries(code),  -- which side the fact belongs to
  hs6           CHAR(6) REFERENCES product_groups(hs6),  -- NULL if applies to all goods
  mode          shipment_mode,                       -- NULL if applies to both
  block         TEXT NOT NULL,                       -- 'regime' | 'export' | 'export_support' | 'import' | 'cost' | 'logistics' | 'documents'
  statement     JSONB NOT NULL,                      -- {"ru": "...", "en": "..."} generated from the same fact
  quote         TEXT NOT NULL CHECK (length(quote) > 0),
  quote_lang    TEXT NOT NULL,
  source_url_id BIGINT NOT NULL REFERENCES source_urls(id),
  snapshot_id   BIGINT NOT NULL REFERENCES snapshots(id),
  status        fact_status NOT NULL DEFAULT 'verified',
  verified_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  is_demo       BOOLEAN NOT NULL DEFAULT FALSE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ON facts (corridor_id, hs6, block);

-- Structured rates: the LLM never writes numbers; they come from here.
CREATE TABLE rates (
  id            BIGSERIAL PRIMARY KEY,
  country       CHAR(2) NOT NULL REFERENCES countries(code),
  hs_code       TEXT NOT NULL,                       -- national line (8–10 digits) or hs6
  kind          rate_kind NOT NULL,
  partner       CHAR(2),                             -- for preferential rates: origin country
  agreement_id  BIGINT,                              -- set below after agreements table
  value         NUMERIC,                             -- percent or amount
  unit          TEXT NOT NULL DEFAULT 'percent',     -- 'percent' | 'per_tonne' | 'per_unit' | 'cad' ...
  currency      TEXT,
  valid_from    DATE,
  valid_to      DATE,
  source_url_id BIGINT REFERENCES source_urls(id),
  snapshot_id   BIGINT REFERENCES snapshots(id),
  verified_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  is_demo       BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE INDEX ON rates (country, hs_code, kind);

CREATE TABLE agreements (
  id            BIGSERIAL PRIMARY KEY,
  name          JSONB NOT NULL,
  parties       CHAR(2)[] NOT NULL,
  in_force_from DATE,
  origin_rules  TEXT,                                -- short note: certificate form, issuer
  source_url_id BIGINT REFERENCES source_urls(id),
  verified_at   TIMESTAMPTZ
);
ALTER TABLE rates ADD CONSTRAINT rates_agreement_fk FOREIGN KEY (agreement_id) REFERENCES agreements(id);

-- Sanctions regimes as they apply to a target country and (optionally) goods scope.
CREATE TABLE sanctions (
  id             BIGSERIAL PRIMARY KEY,
  jurisdiction   TEXT NOT NULL,                      -- 'CA' | 'US' | 'EU' | 'UK' | target countries' own
  target_country CHAR(2) NOT NULL REFERENCES countries(code),
  program        TEXT NOT NULL,
  scope          sanction_scope NOT NULL,
  hs_scope       TEXT[],                             -- HS prefixes affected; NULL = all / not goods-specific
  exemptions     TEXT,                               -- e.g. food, medicine general licences
  source_url_id  BIGINT REFERENCES source_urls(id),
  snapshot_id    BIGINT REFERENCES snapshots(id),
  verified_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Government support: subsidies, insurance, transport compensation, VAT refund, zones.
CREATE TABLE programs (
  id            BIGSERIAL PRIMARY KEY,
  country       CHAR(2) NOT NULL REFERENCES countries(code),
  agency        TEXT NOT NULL,
  kind          TEXT NOT NULL,                       -- 'transport_compensation' | 'insurance' | 'vat_refund' | 'subsidy' | 'financing' | 'zone'
  title         JSONB NOT NULL,
  summary       JSONB,
  eligibility   TEXT,
  hs_scope      TEXT[],
  route_scope   TEXT,                                -- if tied to a route/mode (e.g. rail to Europe)
  deadline      DATE,
  quote         TEXT NOT NULL,
  source_url_id BIGINT NOT NULL REFERENCES source_urls(id),
  snapshot_id   BIGINT NOT NULL REFERENCES snapshots(id),
  status        fact_status NOT NULL DEFAULT 'verified',
  verified_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  is_demo       BOOLEAN NOT NULL DEFAULT FALSE
);

-- Demand signal (estimate only).
CREATE TABLE trade_stats (
  id          BIGSERIAL PRIMARY KEY,
  importer    CHAR(2) NOT NULL REFERENCES countries(code),
  exporter    CHAR(2),                                -- NULL = world
  hs6         CHAR(6) NOT NULL,
  period      TEXT NOT NULL,                          -- '2025' or '2025-06'
  value_usd   NUMERIC,
  quantity    NUMERIC,
  unit        TEXT,
  source      TEXT NOT NULL,                          -- 'statcan' | 'comtrade' | ...
  fetched_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ON trade_stats (importer, hs6, period);

-- Logistics signal (estimate only): indicative bands per region pair and mode.
CREATE TABLE freight_indicative (
  id          BIGSERIAL PRIMARY KEY,
  from_region TEXT NOT NULL,
  to_region   TEXT NOT NULL,
  mode        TEXT NOT NULL,                          -- 'sea_fcl' | 'air' | 'rail' | 'road'
  low         NUMERIC,
  high        NUMERIC,
  unit        TEXT NOT NULL,                          -- 'usd_per_feu' | 'usd_per_tonne' | ...
  days_low    INT,
  days_high   INT,
  index_name  TEXT,
  index_date  DATE,
  fetched_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Cheap index layer: five-part score for every (corridor, hs6, mode).
CREATE TABLE corridor_index (
  id              BIGSERIAL PRIMARY KEY,
  from_country    CHAR(2) NOT NULL REFERENCES countries(code),
  to_country      CHAR(2) NOT NULL REFERENCES countries(code),
  hs6             CHAR(6) NOT NULL,
  mode            shipment_mode NOT NULL DEFAULT 'b2b',
  score_tariff    SMALLINT CHECK (score_tariff BETWEEN 0 AND 5),
  score_barriers  SMALLINT CHECK (score_barriers BETWEEN 0 AND 5),
  score_support   SMALLINT CHECK (score_support BETWEEN 0 AND 5),
  score_demand    SMALLINT CHECK (score_demand BETWEEN 0 AND 5),
  score_logistics SMALLINT CHECK (score_logistics BETWEEN 0 AND 5),
  basis           JSONB NOT NULL,                     -- one-line basis per part, per language
  prohibited      BOOLEAN NOT NULL DEFAULT FALSE,     -- goods prohibited -> total forced to 0
  total           SMALLINT GENERATED ALWAYS AS (
                    CASE WHEN prohibited THEN 0
                         ELSE COALESCE(score_tariff,0)+COALESCE(score_barriers,0)+COALESCE(score_support,0)
                              +COALESCE(score_demand,0)+COALESCE(score_logistics,0) END) STORED,
  computed_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (from_country, to_country, hs6, mode)
);

-- Generated corridor pages (cached). Content is the assembled block structure; rendering is the web app's job.
CREATE TABLE pages (
  id            BIGSERIAL PRIMARY KEY,
  corridor_id   TEXT NOT NULL REFERENCES corridors(id),
  hs6           CHAR(6) NOT NULL REFERENCES product_groups(hs6),
  mode          shipment_mode NOT NULL DEFAULT 'b2b',
  lang          TEXT NOT NULL,
  content       JSONB NOT NULL,                     -- blocks with facts, stamps, scores
  sources_total INT NOT NULL DEFAULT 0,
  sources_missing INT NOT NULL DEFAULT 0,
  status        page_status NOT NULL DEFAULT 'generating',
  generated_at  TIMESTAMPTZ,
  UNIQUE (corridor_id, hs6, mode, lang)
);

CREATE TABLE subscriptions (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email         TEXT NOT NULL,
  corridor_id   TEXT NOT NULL REFERENCES corridors(id),
  hs6           CHAR(6) NOT NULL,
  topics        TEXT[] NOT NULL DEFAULT '{rates,sanctions,programs}',
  frequency     TEXT NOT NULL DEFAULT 'immediate',     -- 'immediate' | 'weekly'
  confirmed_at  TIMESTAMPTZ,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE error_reports (
  id          BIGSERIAL PRIMARY KEY,
  page_id     BIGINT REFERENCES pages(id),
  fact_id     BIGINT REFERENCES facts(id),
  message     TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  status      TEXT NOT NULL DEFAULT 'queued'            -- 'queued' | 'rechecked' | 'changed' | 'unchanged'
);

-- Freshness view: what the page shows next to each fact.
CREATE VIEW fact_freshness AS
SELECT f.id,
       CASE
         WHEN f.status IN ('not_found','unavailable','prohibited','estimate','confirm_with_broker') THEN f.status::text
         WHEN now() - f.verified_at > interval '180 days' THEN 'stale_warning'
         WHEN now() - f.verified_at > interval '90 days'  THEN 'stale'
         ELSE 'verified'
       END AS display_status,
       f.verified_at
FROM facts f;
