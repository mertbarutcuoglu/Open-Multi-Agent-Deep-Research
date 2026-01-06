"""Tracing bootstrap for Traceloop/OpenLLMetry."""

import logging
import os
from typing import Optional

from traceloop.sdk import Traceloop

SERVICE_NAME = "open-multi-agent-deep-research"
_INITIALIZED = False


def _merge_resource_attributes(environment: str) -> None:
    existing = os.getenv("OTEL_RESOURCE_ATTRIBUTES", "")
    env_attr = f"deployment.environment={environment}"
    current_attrs = [attr.strip() for attr in existing.split(",") if attr.strip()]
    if env_attr in current_attrs:
        return

    merged = ",".join(filter(None, [existing, env_attr]))
    os.environ["OTEL_RESOURCE_ATTRIBUTES"] = merged


def _apply_env_defaults(environment: str, otlp_endpoint: Optional[str]) -> None:
    os.environ.setdefault("OTEL_SERVICE_NAME", SERVICE_NAME)
    _merge_resource_attributes(environment)

    if otlp_endpoint:
        os.environ.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", otlp_endpoint)


def _configure_sampling(sampling_ratio: Optional[str]) -> None:
    if not sampling_ratio:
        return

    os.environ.setdefault("OTEL_TRACES_SAMPLER", "traceidratio")
    os.environ.setdefault("OTEL_TRACES_SAMPLER_ARG", sampling_ratio)


def init_tracing() -> None:
    """Initialize Traceloop/OpenLLMetry tracing if not already configured."""
    global _INITIALIZED

    if _INITIALIZED:
        return

    environment = (
        os.getenv("TRACELOOP_ENVIRONMENT")
        or os.getenv("ENVIRONMENT")
        or "development"
    )
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    sampling_ratio = os.getenv("OTEL_TRACES_SAMPLER_ARG") or os.getenv(
        "TRACELOOP_SAMPLING_RATIO"
    )
    api_key = os.getenv("TRACELOOP_API_KEY")

    _apply_env_defaults(environment, otlp_endpoint)
    _configure_sampling(sampling_ratio)

    if api_key:
        os.environ.setdefault("TRACELOOP_API_KEY", api_key)

    try:
        Traceloop.init(app_name=SERVICE_NAME)
    except Exception as exc:  # pragma: no cover - defensive logging
        logging.getLogger(__name__).warning("Tracing initialization skipped: %s", exc)
        return

    _INITIALIZED = True
