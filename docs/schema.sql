CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;

CREATE TYPE machine_status AS ENUM (
  'healthy',
  'warning',
  'critical',
  'offline',
  'maintenance'
);

CREATE TYPE severity_level AS ENUM (
  'low',
  'medium',
  'high',
  'critical'
);

CREATE TYPE action_mode AS ENUM (
  'manual',
  'auto'
);

CREATE TYPE action_type AS ENUM (
  'load_balance',
  'cooling_adjustment',
  'alert',
  'restart_service',
  'traffic_drain',
  'throttle_workload'
);

CREATE TYPE action_status AS ENUM (
  'pending',
  'approved',
  'rejected',
  'executing',
  'executed',
  'failed',
  'simulated',
  'rolled_back'
);

CREATE TYPE agent_name AS ENUM (
  'monitoring',
  'prediction',
  'decision',
  'action'
);

CREATE TYPE user_role_name AS ENUM (
  'admin',
  'operator',
  'viewer',
  'service'
);

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email CITEXT NOT NULL UNIQUE,
  full_name VARCHAR(150) NOT NULL,
  hashed_password VARCHAR(255) NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  last_login_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT chk_users_email_length CHECK (char_length(email::text) >= 5)
);

CREATE TABLE roles (
  id SMALLSERIAL PRIMARY KEY,
  name user_role_name NOT NULL UNIQUE,
  description TEXT NOT NULL
);

CREATE TABLE user_roles (
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role_id SMALLINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
  assigned_by UUID REFERENCES users(id) ON DELETE SET NULL,
  assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (user_id, role_id)
);

CREATE TABLE machines (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  hostname VARCHAR(255) NOT NULL UNIQUE,
  ip_address INET NOT NULL UNIQUE,
  region VARCHAR(64) NOT NULL,
  availability_zone VARCHAR(64),
  data_center VARCHAR(64) NOT NULL,
  rack VARCHAR(64) NOT NULL,
  environment VARCHAR(32) NOT NULL,
  status machine_status NOT NULL DEFAULT 'healthy',
  action_mode action_mode NOT NULL DEFAULT 'manual',
  agent_version VARCHAR(64),
  os_name VARCHAR(64),
  os_version VARCHAR(64),
  last_seen_at TIMESTAMPTZ,
  tags JSONB NOT NULL DEFAULT '{}'::jsonb,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE machine_credentials (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  machine_id UUID NOT NULL REFERENCES machines(id) ON DELETE CASCADE,
  key_name VARCHAR(100) NOT NULL,
  key_hash VARCHAR(255) NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  last_used_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ,
  UNIQUE (machine_id, key_name)
);

CREATE TABLE metrics (
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  machine_id UUID NOT NULL REFERENCES machines(id) ON DELETE CASCADE,
  recorded_at TIMESTAMPTZ NOT NULL,
  ingest_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  cpu_usage DOUBLE PRECISION NOT NULL,
  memory_usage DOUBLE PRECISION NOT NULL,
  temperature_c DOUBLE PRECISION NOT NULL,
  network_in_mbps DOUBLE PRECISION NOT NULL,
  network_out_mbps DOUBLE PRECISION NOT NULL,
  disk_usage DOUBLE PRECISION,
  disk_read_iops DOUBLE PRECISION,
  disk_write_iops DOUBLE PRECISION,
  fan_speed_rpm DOUBLE PRECISION,
  power_draw_watts DOUBLE PRECISION,
  source VARCHAR(32) NOT NULL,
  source_ref VARCHAR(128),
  labels JSONB NOT NULL DEFAULT '{}'::jsonb,
  PRIMARY KEY (id, recorded_at),
  CONSTRAINT chk_metrics_cpu_usage CHECK (cpu_usage >= 0 AND cpu_usage <= 100),
  CONSTRAINT chk_metrics_memory_usage CHECK (memory_usage >= 0 AND memory_usage <= 100),
  CONSTRAINT chk_metrics_network_in CHECK (network_in_mbps >= 0),
  CONSTRAINT chk_metrics_network_out CHECK (network_out_mbps >= 0),
  CONSTRAINT chk_metrics_disk_usage CHECK (
    disk_usage IS NULL OR (disk_usage >= 0 AND disk_usage <= 100)
  )
);

SELECT create_hypertable(
  'metrics',
  'recorded_at',
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE
);

CREATE TABLE anomalies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  machine_id UUID NOT NULL REFERENCES machines(id) ON DELETE CASCADE,
  metric_id UUID,
  detected_at TIMESTAMPTZ NOT NULL,
  severity severity_level NOT NULL,
  anomaly_type VARCHAR(100) NOT NULL,
  anomaly_score DOUBLE PRECISION NOT NULL,
  summary VARCHAR(500) NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'open',
  model_name VARCHAR(100),
  feature_window_seconds INTEGER,
  context JSONB NOT NULL DEFAULT '{}'::jsonb,
  reasoning TEXT NOT NULL,
  CONSTRAINT chk_anomalies_score CHECK (anomaly_score >= 0)
);

CREATE TABLE predictions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  machine_id UUID NOT NULL REFERENCES machines(id) ON DELETE CASCADE,
  anomaly_id UUID REFERENCES anomalies(id) ON DELETE SET NULL,
  generated_at TIMESTAMPTZ NOT NULL,
  prediction_type VARCHAR(100) NOT NULL,
  failure_type VARCHAR(128) NOT NULL,
  risk_score DOUBLE PRECISION NOT NULL,
  confidence_score DOUBLE PRECISION,
  time_to_failure_minutes INTEGER NOT NULL,
  recommended_by_model VARCHAR(100),
  features JSONB NOT NULL DEFAULT '{}'::jsonb,
  reasoning TEXT NOT NULL,
  expires_at TIMESTAMPTZ,
  CONSTRAINT chk_predictions_risk CHECK (risk_score >= 0 AND risk_score <= 1),
  CONSTRAINT chk_predictions_confidence CHECK (
    confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)
  ),
  CONSTRAINT chk_predictions_ttf CHECK (time_to_failure_minutes >= 0)
);

CREATE TABLE actions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  machine_id UUID NOT NULL REFERENCES machines(id) ON DELETE CASCADE,
  prediction_id UUID REFERENCES predictions(id) ON DELETE SET NULL,
  requested_by UUID REFERENCES users(id) ON DELETE SET NULL,
  action_type action_type NOT NULL,
  status action_status NOT NULL DEFAULT 'pending',
  approval_required BOOLEAN NOT NULL DEFAULT FALSE,
  approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
  simulated BOOLEAN NOT NULL DEFAULT TRUE,
  request_source VARCHAR(50) NOT NULL DEFAULT 'agent',
  requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  approved_at TIMESTAMPTZ,
  executed_at TIMESTAMPTZ,
  rollback_at TIMESTAMPTZ,
  reasoning TEXT NOT NULL,
  execution_result JSONB NOT NULL DEFAULT '{}'::jsonb,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE action_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  action_id UUID NOT NULL REFERENCES actions(id) ON DELETE CASCADE,
  status action_status NOT NULL,
  message TEXT NOT NULL,
  details JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE agent_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  machine_id UUID NOT NULL REFERENCES machines(id) ON DELETE CASCADE,
  related_prediction_id UUID REFERENCES predictions(id) ON DELETE SET NULL,
  related_action_id UUID REFERENCES actions(id) ON DELETE SET NULL,
  correlation_id UUID NOT NULL,
  agent_name agent_name NOT NULL,
  input_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  output_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  reasoning TEXT NOT NULL,
  duration_ms INTEGER,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  actor_id UUID REFERENCES users(id) ON DELETE SET NULL,
  actor_type VARCHAR(32) NOT NULL DEFAULT 'user',
  action VARCHAR(128) NOT NULL,
  entity_type VARCHAR(64) NOT NULL,
  entity_id VARCHAR(128) NOT NULL,
  ip_address INET,
  user_agent TEXT,
  details JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO roles (name, description)
VALUES
  ('admin', 'Full platform administration access'),
  ('operator', 'Can view, approve, and trigger operational actions'),
  ('viewer', 'Read-only dashboard and logs access'),
  ('service', 'Internal machine-to-machine access')
ON CONFLICT (name) DO NOTHING;

CREATE INDEX ix_user_roles_role_id_user_id
  ON user_roles (role_id, user_id);

CREATE INDEX ix_machines_region_status
  ON machines (region, status);

CREATE INDEX ix_machines_environment_status
  ON machines (environment, status);

CREATE INDEX ix_machines_last_seen_at
  ON machines (last_seen_at DESC);

CREATE INDEX ix_machine_credentials_machine_active
  ON machine_credentials (machine_id, is_active)
  WHERE is_active = TRUE;

CREATE INDEX ix_metrics_machine_recorded_desc
  ON metrics (machine_id, recorded_at DESC);

CREATE INDEX ix_metrics_recorded_desc
  ON metrics (recorded_at DESC);

CREATE INDEX ix_metrics_source_recorded
  ON metrics (source, recorded_at DESC);

CREATE INDEX ix_metrics_labels_gin
  ON metrics USING GIN (labels);

CREATE INDEX ix_anomalies_machine_detected_desc
  ON anomalies (machine_id, detected_at DESC);

CREATE INDEX ix_anomalies_status_detected_desc
  ON anomalies (status, detected_at DESC);

CREATE INDEX ix_anomalies_severity_detected_desc
  ON anomalies (severity, detected_at DESC);

CREATE INDEX ix_anomalies_context_gin
  ON anomalies USING GIN (context);

CREATE INDEX ix_predictions_machine_generated_desc
  ON predictions (machine_id, generated_at DESC);

CREATE INDEX ix_predictions_risk_generated_desc
  ON predictions (risk_score DESC, generated_at DESC);

CREATE INDEX ix_predictions_failure_type_generated_desc
  ON predictions (failure_type, generated_at DESC);

CREATE INDEX ix_predictions_features_gin
  ON predictions USING GIN (features);

CREATE INDEX ix_actions_machine_requested_desc
  ON actions (machine_id, requested_at DESC);

CREATE INDEX ix_actions_status_requested_desc
  ON actions (status, requested_at DESC);

CREATE INDEX ix_actions_pending_approvals
  ON actions (approval_required, status, requested_at DESC)
  WHERE approval_required = TRUE;

CREATE INDEX ix_action_logs_action_created_desc
  ON action_logs (action_id, created_at DESC);

CREATE INDEX ix_agent_logs_machine_created_desc
  ON agent_logs (machine_id, created_at DESC);

CREATE INDEX ix_agent_logs_correlation_created_desc
  ON agent_logs (correlation_id, created_at DESC);

CREATE INDEX ix_agent_logs_agent_created_desc
  ON agent_logs (agent_name, created_at DESC);

CREATE INDEX ix_audit_logs_entity_created_desc
  ON audit_logs (entity_type, entity_id, created_at DESC);

CREATE INDEX ix_audit_logs_actor_created_desc
  ON audit_logs (actor_id, created_at DESC);

CREATE INDEX ix_audit_logs_created_desc
  ON audit_logs (created_at DESC);

ALTER TABLE metrics SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'machine_id,source',
  timescaledb.compress_orderby = 'recorded_at DESC'
);

SELECT add_compression_policy('metrics', INTERVAL '7 days', if_not_exists => TRUE);
SELECT add_retention_policy('metrics', INTERVAL '90 days', if_not_exists => TRUE);
