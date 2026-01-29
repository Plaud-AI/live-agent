"""OAuth provider integrations for Google and Apple Sign-In"""
import httpx
import jwt
import time
from typing import Optional
from datetime import datetime, timedelta

from config import settings
from schemas.auth import GoogleUserInfo, AppleUserInfo


class GoogleOAuthProvider:
    """Google OAuth 2.0 provider for Google Sign-In"""
    
    GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"
    GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"
    
    @staticmethod
    async def verify_id_token(id_token: str) -> Optional[GoogleUserInfo]:
        """
        Verify Google ID token and extract user info.
        
        Args:
            id_token: The ID token from Google Sign-In
            
        Returns:
            GoogleUserInfo if valid, None otherwise
        """
        try:
            # Verify token with Google
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{GoogleOAuthProvider.GOOGLE_TOKEN_INFO_URL}?id_token={id_token}"
                )
                
                if response.status_code != 200:
                    return None
                
                data = response.json()
                
                # Verify audience (client ID)
                if data.get('aud') != settings.GOOGLE_CLIENT_ID:
                    return None
                
                # Verify issuer
                if data.get('iss') not in ['accounts.google.com', 'https://accounts.google.com']:
                    return None
                
                # Check expiration
                exp = int(data.get('exp', 0))
                if exp < time.time():
                    return None
                
                return GoogleUserInfo(
                    sub=data['sub'],
                    email=data['email'],
                    email_verified=data.get('email_verified', 'false').lower() == 'true',
                    name=data.get('name'),
                    given_name=data.get('given_name'),
                    family_name=data.get('family_name'),
                    picture=data.get('picture')
                )
                
        except Exception as e:
            print(f"Error verifying Google ID token: {e}")
            return None


class AppleOAuthProvider:
    """Apple Sign In provider"""
    
    APPLE_KEYS_URL = "https://appleid.apple.com/auth/keys"
    APPLE_TOKEN_URL = "https://appleid.apple.com/auth/token"
    
    _apple_public_keys = None
    _keys_fetched_at = None
    
    @classmethod
    async def _get_apple_public_keys(cls) -> dict:
        """Fetch and cache Apple's public keys"""
        # Cache keys for 1 hour
        if cls._apple_public_keys and cls._keys_fetched_at:
            if datetime.now() - cls._keys_fetched_at < timedelta(hours=1):
                return cls._apple_public_keys
        
        async with httpx.AsyncClient() as client:
            response = await client.get(cls.APPLE_KEYS_URL)
            if response.status_code == 200:
                cls._apple_public_keys = response.json()
                cls._keys_fetched_at = datetime.now()
                return cls._apple_public_keys
        
        return {}
    
    @classmethod
    def _generate_client_secret(cls) -> str:
        """
        Generate Apple client secret JWT.
        Apple requires a JWT signed with your private key.
        """
        now = int(time.time())
        
        headers = {
            'alg': 'ES256',
            'kid': settings.APPLE_KEY_ID
        }
        
        payload = {
            'iss': settings.APPLE_TEAM_ID,
            'iat': now,
            'exp': now + 86400 * 180,  # 180 days
            'aud': 'https://appleid.apple.com',
            'sub': settings.APPLE_CLIENT_ID
        }
        
        # The private key should be in PEM format
        private_key = settings.APPLE_PRIVATE_KEY.replace('\\n', '\n')
        
        return jwt.encode(payload, private_key, algorithm='ES256', headers=headers)
    
    @classmethod
    async def verify_id_token(
        cls, 
        id_token: str,
        user_info: Optional[dict] = None
    ) -> Optional[AppleUserInfo]:
        """
        Verify Apple ID token and extract user info.
        
        Args:
            id_token: The ID token from Sign in with Apple
            user_info: Optional user info (only provided on first sign-in)
            
        Returns:
            AppleUserInfo if valid, None otherwise
        """
        try:
            # Get Apple's public keys
            keys_data = await cls._get_apple_public_keys()
            
            if not keys_data or 'keys' not in keys_data:
                return None
            
            # Get the key ID from the token header
            unverified_header = jwt.get_unverified_header(id_token)
            kid = unverified_header.get('kid')
            
            # Find the matching public key
            public_key = None
            for key in keys_data['keys']:
                if key['kid'] == kid:
                    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
                    break
            
            if not public_key:
                return None
            
            # Verify and decode the token
            payload = jwt.decode(
                id_token,
                public_key,
                algorithms=['RS256'],
                audience=settings.APPLE_CLIENT_ID,
                issuer='https://appleid.apple.com'
            )
            
            # Extract user info
            name = None
            if user_info:
                # First sign-in - user info is provided
                name_obj = user_info.get('name', {})
                if name_obj:
                    first_name = name_obj.get('firstName', '')
                    last_name = name_obj.get('lastName', '')
                    name = f"{first_name} {last_name}".strip() or None
            
            return AppleUserInfo(
                sub=payload['sub'],
                email=payload.get('email'),
                email_verified=payload.get('email_verified'),
                is_private_email=payload.get('is_private_email'),
                name=name
            )
            
        except jwt.ExpiredSignatureError:
            print("Apple ID token has expired")
            return None
        except jwt.InvalidTokenError as e:
            print(f"Invalid Apple ID token: {e}")
            return None
        except Exception as e:
            print(f"Error verifying Apple ID token: {e}")
            return None


# Singleton instances
google_oauth = GoogleOAuthProvider()
apple_oauth = AppleOAuthProvider()


