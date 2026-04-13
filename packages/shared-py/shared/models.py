from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True
    )
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), primary_key=True)


class Machine(Base):
    __tablename__ = "machines"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    hostname: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    ip_address: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    region: Mapped[str] = mapped_column(String(64), index=True)
    rack: Mapped[str] = mapped_column(String(64), index=True)
    environment: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Metric(Base):
    __tablename__ = "metrics"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    machine_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("machines.id"), index=True
    )
    recorded_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    cpu_usage: Mapped[float] = mapped_column(Float)
    memory_usage: Mapped[float] = mapped_column(Float)
    temperature_c: Mapped[float] = mapped_column(Float)
    network_in_mbps: Mapped[float] = mapped_column(Float)
    network_out_mbps: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(32), index=True)

    __table_args__ = (
        Index("ix_metrics_machine_recorded_desc", "machine_id", "recorded_at"),
    )


class Anomaly(Base):
    __tablename__ = "anomalies"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    machine_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("machines.id"), index=True
    )
    severity: Mapped[str] = mapped_column(String(32), index=True)
    anomaly_score: Mapped[float] = mapped_column(Float, index=True)
    summary: Mapped[str] = mapped_column(String(500))
    detected_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    context: Mapped[dict] = mapped_column(JSONB, default=dict)


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    machine_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("machines.id"), index=True
    )
    risk_score: Mapped[float] = mapped_column(Float, index=True)
    failure_type: Mapped[str] = mapped_column(String(128), index=True)
    time_to_failure_minutes: Mapped[int] = mapped_column(Integer, index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    features: Mapped[dict] = mapped_column(JSONB, default=dict)
    reasoning: Mapped[str] = mapped_column(Text)


class Action(Base):
    __tablename__ = "actions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    machine_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("machines.id"), index=True
    )
    action_type: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    approval_required: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    simulated: Mapped[bool] = mapped_column(Boolean, default=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reasoning: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    machine_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("machines.id"), index=True
    )
    agent_name: Mapped[str] = mapped_column(String(64), index=True)
    input_payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    output_payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    reasoning: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    actor_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(128), index=True)
    entity_type: Mapped[str] = mapped_column(String(64), index=True)
    entity_id: Mapped[str] = mapped_column(String(128), index=True)
    details: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
