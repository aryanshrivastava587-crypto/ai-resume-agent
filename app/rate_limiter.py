"""
In-memory rate limiter — tracks usage per IP address.
Resets daily at midnight UTC. Suitable for portfolio/demo projects.
For production, use Redis or a database-backed solution.
"""
import time
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

# ── Configuration ──
MAX_USES_PER_DAY = 5
SECONDS_IN_DAY = 86400


class RateLimiter:
    def __init__(self):
        self._usage = defaultdict(lambda: {"count": 0, "reset_at": 0})

    def _get_day_reset(self):
        """Get the UTC timestamp for the end of the current day."""
        now = time.time()
        return now - (now % SECONDS_IN_DAY) + SECONDS_IN_DAY

    def check(self, ip: str) -> dict:
        """
        Check and consume one use for the given IP.
        Returns: {"allowed": bool, "remaining": int, "limit": int, "reset_in_seconds": int}
        """
        now = time.time()
        entry = self._usage[ip]

        # Reset if new day
        if now >= entry["reset_at"]:
            entry["count"] = 0
            entry["reset_at"] = self._get_day_reset()

        remaining = MAX_USES_PER_DAY - entry["count"]
        reset_in = max(0, int(entry["reset_at"] - now))

        if entry["count"] >= MAX_USES_PER_DAY:
            logger.info(f"Rate limit exceeded for IP {ip}")
            return {
                "allowed": False,
                "remaining": 0,
                "limit": MAX_USES_PER_DAY,
                "reset_in_seconds": reset_in,
            }

        entry["count"] += 1
        remaining = MAX_USES_PER_DAY - entry["count"]
        logger.info(f"IP {ip}: usage {entry['count']}/{MAX_USES_PER_DAY}")

        return {
            "allowed": True,
            "remaining": remaining,
            "limit": MAX_USES_PER_DAY,
            "reset_in_seconds": reset_in,
        }

    def get_status(self, ip: str) -> dict:
        """Get current usage status without consuming a use."""
        now = time.time()
        entry = self._usage[ip]

        if now >= entry["reset_at"]:
            return {
                "remaining": MAX_USES_PER_DAY,
                "limit": MAX_USES_PER_DAY,
                "reset_in_seconds": int(self._get_day_reset() - now),
            }

        return {
            "remaining": MAX_USES_PER_DAY - entry["count"],
            "limit": MAX_USES_PER_DAY,
            "reset_in_seconds": max(0, int(entry["reset_at"] - now)),
        }


# Singleton instance
rate_limiter = RateLimiter()
