"""
Optional Sentry bridge.

If `SENTRY_DSN` is set in the environment and `sentry_sdk` is installed,
_error_logger calls capture_exception. Otherwise this module is a no-op —
the app continues to log to exports/error_log.txt via the rotating handler.
"""
from __future__ import annotations

import os

_SENTRY_ENABLED = False
_sentry_sdk = None

_dsn = os.environ.get("SENTRY_DSN", "").strip()
if _dsn:
    try:
        import sentry_sdk  # type: ignore

        sentry_sdk.init(
            dsn=_dsn,
            traces_sample_rate=float(os.environ.get("SENTRY_TRACES_RATE", "0.1")),
            send_default_pii=False,
            environment=os.environ.get("SENTRY_ENV", "production"),
        )
        _sentry_sdk = sentry_sdk
        _SENTRY_ENABLED = True
        print("  - Sentry: ✅ initialized")
    except ImportError:
        print("  - Sentry: ⚠️  SENTRY_DSN set but sentry-sdk not installed")
    except Exception as e:
        print(f"  - Sentry: ⚠️  init failed: {e}")
else:
    print("  - Sentry: ℹ️  disabled (no SENTRY_DSN)")


def capture_exception(err: Exception, **context) -> None:
    if not _SENTRY_ENABLED or _sentry_sdk is None:
        return
    try:
        with _sentry_sdk.push_scope() as scope:
            for k, v in context.items():
                scope.set_extra(k, v)
            _sentry_sdk.capture_exception(err)
    except Exception:
        pass


def capture_message(message: str, level: str = "info", **context) -> None:
    if not _SENTRY_ENABLED or _sentry_sdk is None:
        return
    try:
        with _sentry_sdk.push_scope() as scope:
            for k, v in context.items():
                scope.set_extra(k, v)
            _sentry_sdk.capture_message(message, level=level)
    except Exception:
        pass


def is_enabled() -> bool:
    return _SENTRY_ENABLED
