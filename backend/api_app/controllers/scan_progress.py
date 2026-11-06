"""Inferred progress for a requested app scan.

The caller must authorize access to the request before calling this endpoint.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

from litestar import Controller, get
from litestar.datastructures import State
from litestar.exceptions import ValidationException
from litestar.params import FromQuery

from dbcon.queries import get_scan_progress

StageStatus = Literal[
    "pending", "success", "failure", "unknown", "estimated", "optional"
]


@dataclass
class ScanStage:
    """A stage inferred from an event or an explicitly identified estimate."""

    status: StageStatus
    at: datetime | None
    note: str


@dataclass
class ScanStages:
    """Stages in the requested scan lifecycle."""

    request: ScanStage
    download: ScanStage
    sdk_scan: ScanStage
    data_import: ScanStage
    waydroid: ScanStage


@dataclass
class ScanProgress:
    """Progress is inferred from activity, not linked to a specific request."""

    store_id: str
    requested_at: datetime
    version_code: str | None
    stages: ScanStages


def _event_stage(at: datetime | None, result: int | None, name: str) -> ScanStage:
    if at is None:
        return ScanStage(
            "optional" if name == "Waydroid" else "pending",
            None,
            f"No {name} event observed after the request; association is inferred.",
        )
    if result is None:
        status: StageStatus = "pending"
    else:
        status = "success" if result == 1 else "failure"
    return ScanStage(
        status, at, f"{name} event after the request; association is inferred."
    )


def build_scan_progress(
    store_id: str, requested_at: datetime, row: dict
) -> ScanProgress:
    """Build progress without claiming the events were caused by the request."""
    crawl_result = row["version_crawl_result"]
    if row["has_s3_key"]:
        download = ScanStage(
            "success",
            None,
            "An S3 key exists for the selected version; its creation time "
            "and association with the request are unknown.",
        )
    elif crawl_result in (2, 3, 4):
        download = ScanStage(
            "failure",
            row["version_updated_at"],
            "Selected version reports a download failure; "
            "association with the request is inferred.",
        )
    elif crawl_result is not None:
        download = ScanStage(
            "unknown",
            row["version_updated_at"],
            "No S3 key found; the selected version's result does not establish "
            "download completion. Association is inferred.",
        )
    else:
        download = ScanStage(
            "pending",
            None,
            "No completed download observed for the selected version; "
            "association is inferred.",
        )
    sdk = _event_stage(row["sdk_at"], row["sdk_result"], "SDK scan")
    waydroid = _event_stage(row["waydroid_at"], row["waydroid_result"], "Waydroid")
    if sdk.status == "success" and sdk.at is not None:
        data_import = ScanStage(
            "estimated",
            sdk.at + timedelta(hours=24),
            "Estimated 24 hours after the inferred successful SDK scan; "
            "import is not confirmed.",
        )
    else:
        data_import = ScanStage(
            "pending", None, "No successful SDK scan observed; import is not confirmed."
        )
    return ScanProgress(
        store_id,
        requested_at,
        row["version_code"],
        ScanStages(
            ScanStage(
                "success",
                requested_at,
                "Request timestamp supplied by caller; not independently verified.",
            ),
            download,
            sdk,
            data_import,
            waydroid,
        ),
    )


class ScanProgressController(Controller):
    """Internal analytics: inferred progress for one store ID and request time."""

    path = "/analytics"

    @get(path="/scan-progress", sync_to_thread=True)
    def scan_progress(
        self, state: State, store_id: FromQuery[str], requested_at: FromQuery[datetime]
    ) -> ScanProgress:
        """Return inferred progress; caller is responsible for request ownership."""
        if not store_id.strip():
            msg = "store_id must not be empty"
            raise ValidationException(msg)
        if requested_at.tzinfo is None or requested_at.utcoffset() is None:
            msg = "requested_at must include a timezone"
            raise ValidationException(msg)
        requested_at = requested_at.astimezone(UTC)
        if requested_at > datetime.now(UTC):
            msg = "requested_at must not be in the future"
            raise ValidationException(msg)
        row = get_scan_progress(state, store_id, requested_at)
        return build_scan_progress(store_id, requested_at, row)
