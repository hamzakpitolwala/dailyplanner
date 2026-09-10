"""OOP Adapter/Strategy Pattern for Calendar Integrations.

Provides an abstract interface (BaseCalendarProvider) and concrete provider
adapters (e.g. GoogleCalendarAdapter) along with a Factory for instantiating them.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
import logging
import httpx

from backend.core.config import settings
from backend.db.models.integrations import UserOAuthToken

logger = logging.getLogger(__name__)


class BaseCalendarProvider(ABC):
    """Abstract Strategy interface for third-party calendar providers."""

    @abstractmethod
    async def fetch_events_for_day(
        self, token_record: UserOAuthToken, target_date: str, tz_offset_minutes: int = 0
    ) -> list[dict]:
        """Fetch all calendar events for a user on a given date (YYYY-MM-DD)."""
        pass

    @abstractmethod
    async def update_event(
        self,
        token_record: UserOAuthToken,
        calendar_id: str,
        external_id: str,
        summary: str,
        description: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict:
        """Update an existing event on the third-party calendar."""
        pass

    @abstractmethod
    async def create_event(
        self,
        token_record: UserOAuthToken,
        calendar_id: str,
        summary: str,
        description: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict:
        """Create a new event on the third-party calendar."""
        pass

    @abstractmethod
    async def cancel_event(
        self, token_record: UserOAuthToken, calendar_id: str, external_id: str
    ) -> bool:
        """Cancel or delete an event on the third-party calendar."""
        pass

    @abstractmethod
    async def refresh_token(self, token_record: UserOAuthToken) -> tuple[str, datetime]:
        """Refresh an expired OAuth access token."""
        pass


class GoogleCalendarAdapter(BaseCalendarProvider):
    """Concrete Adapter for Google Calendar API v3."""

    TOKEN_URL = "https://oauth2.googleapis.com/token"
    CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"

    async def _get_valid_access_token(self, token_record: UserOAuthToken) -> str:
        """Return access token, automatically refreshing if expired or expiring soon."""
        now = datetime.now(timezone.utc)
        if token_record.expires_at and token_record.expires_at.tzinfo is None:
            expires_at = token_record.expires_at.replace(tzinfo=timezone.utc)
        else:
            expires_at = token_record.expires_at

        if expires_at and (expires_at - now) < timedelta(seconds=60):
            logger.info("Google OAuth token expired/expiring. Refreshing token...")
            new_access_token, new_expires = await self.refresh_token(token_record)
            token_record.access_token = new_access_token
            token_record.expires_at = new_expires
            return new_access_token
        return token_record.access_token

    async def refresh_token(self, token_record: UserOAuthToken) -> tuple[str, datetime]:
        """Refresh token."""
        if not token_record.refresh_token:
            raise ValueError("No refresh token available for Google Calendar account")

        payload = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "refresh_token": token_record.refresh_token,
            "grant_type": "refresh_token",
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.TOKEN_URL, data=payload)
            if resp.status_code != 200:
                logger.error("Failed to refresh Google token: %s", resp.text)
                raise ValueError(f"Failed to refresh Google OAuth token: {resp.text}")

            data = resp.json()
            new_access_token = data["access_token"]
            expires_in = data.get("expires_in", 3600)
            new_expires = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            return new_access_token, new_expires

    async def fetch_events_for_day(
        self, token_record: UserOAuthToken, target_date: str, tz_offset_minutes: int = 0
    ) -> list[dict]:
        """Fetch events for day."""
        access_token = await self._get_valid_access_token(token_record)

        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        offset_delta = timedelta(minutes=tz_offset_minutes)
        start_dt = datetime(date_obj.year, date_obj.month, date_obj.day, 0, 0, 0, tzinfo=timezone.utc) + offset_delta
        end_dt = start_dt + timedelta(days=1) - timedelta(microseconds=1)

        time_min = start_dt.isoformat()
        time_max = end_dt.isoformat()

        url = f"{self.CALENDAR_API_BASE}/calendars/primary/events"
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {
            "timeMin": time_min,
            "timeMax": time_max,
            "singleEvents": "true",
            "orderBy": "startTime",
        }

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, params=params)
            if resp.status_code != 200:
                logger.error("Google Calendar list events error (%d): %s", resp.status_code, resp.text)
                return []

            data = resp.json()
            items = data.get("items", [])
            normalized_events = []

            for item in items:
                if item.get("status") == "cancelled":
                    continue

                start_info = item.get("start", {})
                end_info = item.get("end", {})

                start_str = start_info.get("dateTime") or start_info.get("date")
                end_str = end_info.get("dateTime") or end_info.get("date")

                start_time = datetime.fromisoformat(start_str) if start_str else None
                end_time = datetime.fromisoformat(end_str) if end_str else None

                normalized_events.append({
                    "external_id": item.get("id"),
                    "calendar_id": "primary",
                    "summary": item.get("summary", "Untitled Event"),
                    "description": item.get("description"),
                    "location": item.get("location"),
                    "status": item.get("status", "confirmed"),
                    "start_time": start_time,
                    "end_time": end_time,
                    "raw_payload": item,
                })

            return normalized_events

    async def update_event(
        self,
        token_record: UserOAuthToken,
        calendar_id: str,
        external_id: str,
        summary: str,
        description: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict:
        """Update event."""
        access_token = await self._get_valid_access_token(token_record)

        url = f"{self.CALENDAR_API_BASE}/calendars/{calendar_id}/events/{external_id}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        body: dict = {
            "summary": summary,
        }
        if description is not None:
            body["description"] = description

        if start_time:
            body["start"] = {"dateTime": start_time.isoformat()}
        if end_time:
            body["end"] = {"dateTime": end_time.isoformat()}

        async with httpx.AsyncClient() as client:
            resp = await client.patch(url, headers=headers, json=body)
            if resp.status_code not in (200, 201):
                logger.error("Google Calendar update event error (%d): %s", resp.status_code, resp.text)
                raise ValueError(f"Failed to update Google Calendar event: {resp.text}")
            return resp.json()

    async def create_event(
        self,
        token_record: UserOAuthToken,
        calendar_id: str,
        summary: str,
        description: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict:
        """Create event."""
        access_token = await self._get_valid_access_token(token_record)

        url = f"{self.CALENDAR_API_BASE}/calendars/{calendar_id}/events"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        body: dict = {
            "summary": summary,
        }
        if description is not None:
            body["description"] = description

        if start_time:
            body["start"] = {"dateTime": start_time.isoformat()}
        if end_time:
            body["end"] = {"dateTime": end_time.isoformat()}

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=body)
            if resp.status_code not in (200, 201):
                logger.error("Google Calendar create event error (%d): %s", resp.status_code, resp.text)
                raise ValueError(f"Failed to create Google Calendar event: {resp.text}")
            return resp.json()

    async def cancel_event(
        self, token_record: UserOAuthToken, calendar_id: str, external_id: str
    ) -> bool:
        """Cancel event."""
        access_token = await self._get_valid_access_token(token_record)

        url = f"{self.CALENDAR_API_BASE}/calendars/{calendar_id}/events/{external_id}"
        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient() as client:
            resp = await client.delete(url, headers=headers)
            if resp.status_code in (200, 204, 410):
                return True
            logger.error("Google Calendar delete event error (%d): %s", resp.status_code, resp.text)
            raise ValueError(f"Failed to delete Google Calendar event: {resp.text}")


class CalendarProviderFactory:
    """Factory Pattern to supply the appropriate Calendar Provider Adapter."""

    _providers: dict[str, BaseCalendarProvider] = {
        "google": GoogleCalendarAdapter(),
    }

    @classmethod
    def get_provider(cls, provider_name: str = "google") -> BaseCalendarProvider:
        """Get provider."""
        provider = cls._providers.get(provider_name.lower())
        if not provider:
            raise ValueError(f"Unsupported calendar provider: {provider_name}")
        return provider
