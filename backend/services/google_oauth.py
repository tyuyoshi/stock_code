from typing import Dict, Any, Optional
from authlib.integrations.starlette_client import OAuth
from authlib.integrations.base_client import OAuthError
import httpx

from core.config import settings


class GoogleOAuthClient:

    def __init__(self):
        if not settings.google_client_id or not settings.google_client_secret:
            raise ValueError(
                "Google OAuth credentials not configured. "
                "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in environment."
            )

        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret
        self.redirect_uri = settings.google_redirect_uri

        self.token_url = "https://oauth2.googleapis.com/token"
        self.userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        self.authorize_url = "https://accounts.google.com/o/oauth2/v2/auth"

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent",
        }

        if state:
            params["state"] = state

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.authorize_url}?{query_string}"

    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    "code": code,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": self.redirect_uri,
                    "grant_type": "authorization_code",
                },
            )

            if response.status_code != 200:
                raise OAuthError(
                    description=f"Failed to exchange code for token: {response.text}"
                )

            return response.json()

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.userinfo_url, headers={"Authorization": f"Bearer {access_token}"}
            )

            if response.status_code != 200:
                raise OAuthError(
                    description=f"Failed to get user info: {response.text}"
                )

            user_data = response.json()

            return {
                "google_id": user_data.get("id"),
                "email": user_data.get("email"),
                "name": user_data.get("name"),
                "profile_picture_url": user_data.get("picture"),
                "email_verified": user_data.get("verified_email", False),
            }

    async def authenticate(self, code: str) -> Dict[str, Any]:
        token_data = await self.exchange_code_for_token(code)
        access_token = token_data.get("access_token")

        if not access_token:
            raise OAuthError(description="No access token in response")

        user_info = await self.get_user_info(access_token)

        return {
            **user_info,
            "access_token": access_token,
            "refresh_token": token_data.get("refresh_token"),
        }


def get_google_oauth_client() -> GoogleOAuthClient:
    return GoogleOAuthClient()
