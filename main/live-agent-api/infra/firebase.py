"""Firebase Admin SDK integration for ID token verification"""
import json
from typing import Optional
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials, auth
from config import settings
from config.logger import logger


class FirebaseUserInfo(BaseModel):
    """User info extracted from Firebase ID token"""
    uid: str  # Firebase UID
    email: Optional[str] = None
    email_verified: bool = False
    name: Optional[str] = None
    picture: Optional[str] = None
    provider: str = "firebase"  # The sign-in provider (password, google.com, apple.com)


class FirebaseAuth:
    """Firebase Authentication service for verifying ID tokens"""
    
    _initialized: bool = False
    
    def __init__(self):
        self._initialize()
    
    def _initialize(self):
        """Initialize Firebase Admin SDK"""
        if self._initialized or firebase_admin._apps:
            self._initialized = True
            return
        
        try:
            # Try to initialize from credentials file first
            if settings.FIREBASE_CREDENTIALS_PATH:
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized from credentials file")
                self._initialized = True
                return
            
            # Try to initialize from inline credentials
            if settings.FIREBASE_PROJECT_ID and settings.FIREBASE_PRIVATE_KEY:
                # Build credentials dict from environment variables
                cred_dict = {
                    "type": "service_account",
                    "project_id": settings.FIREBASE_PROJECT_ID,
                    "private_key_id": settings.FIREBASE_PRIVATE_KEY_ID,
                    "private_key": settings.FIREBASE_PRIVATE_KEY.replace("\\n", "\n"),
                    "client_email": settings.FIREBASE_CLIENT_EMAIL,
                    "client_id": settings.FIREBASE_CLIENT_ID,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{settings.FIREBASE_CLIENT_EMAIL.replace('@', '%40')}"
                }
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized from environment variables")
                self._initialized = True
                return
            
            logger.warning("Firebase credentials not configured - Firebase auth will not work")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
    
    async def verify_id_token(self, id_token: str) -> Optional[FirebaseUserInfo]:
        """
        Verify Firebase ID token and extract user info.
        
        Args:
            id_token: The Firebase ID token from the client
            
        Returns:
            FirebaseUserInfo if token is valid, None otherwise
        """
        if not self._initialized:
            logger.error("Firebase Admin SDK not initialized")
            return None
        
        try:
            # Verify the ID token
            decoded_token = auth.verify_id_token(id_token)
            
            # Extract user info
            uid = decoded_token.get("uid")
            email = decoded_token.get("email")
            email_verified = decoded_token.get("email_verified", False)
            name = decoded_token.get("name")
            picture = decoded_token.get("picture")
            
            # Get the sign-in provider
            # Firebase stores this in the 'firebase' claim
            firebase_claim = decoded_token.get("firebase", {})
            sign_in_provider = firebase_claim.get("sign_in_provider", "unknown")
            
            # Normalize provider names
            provider = self._normalize_provider(sign_in_provider)
            
            logger.info(f"Firebase token verified: uid={uid}, email={email}, provider={provider}")
            
            return FirebaseUserInfo(
                uid=uid,
                email=email,
                email_verified=email_verified,
                name=name,
                picture=picture,
                provider=provider
            )
            
        except auth.ExpiredIdTokenError:
            logger.warning("Firebase ID token has expired")
            return None
        except auth.InvalidIdTokenError as e:
            logger.warning(f"Invalid Firebase ID token: {e}")
            return None
        except auth.RevokedIdTokenError:
            logger.warning("Firebase ID token has been revoked")
            return None
        except Exception as e:
            logger.error(f"Error verifying Firebase ID token: {e}")
            return None
    
    def _normalize_provider(self, sign_in_provider: str) -> str:
        """Normalize Firebase sign-in provider to our internal format"""
        provider_map = {
            "password": "email",
            "google.com": "google",
            "apple.com": "apple",
            "anonymous": "anonymous",
        }
        return provider_map.get(sign_in_provider, sign_in_provider)
    
    async def get_user(self, uid: str) -> Optional[dict]:
        """
        Get Firebase user by UID.
        
        Args:
            uid: Firebase user UID
            
        Returns:
            User record as dict if found, None otherwise
        """
        if not self._initialized:
            return None
        
        try:
            user = auth.get_user(uid)
            return {
                "uid": user.uid,
                "email": user.email,
                "email_verified": user.email_verified,
                "display_name": user.display_name,
                "photo_url": user.photo_url,
                "disabled": user.disabled,
                "provider_data": [
                    {
                        "provider_id": p.provider_id,
                        "uid": p.uid,
                        "email": p.email,
                        "display_name": p.display_name,
                    }
                    for p in user.provider_data
                ] if user.provider_data else []
            }
        except auth.UserNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error getting Firebase user: {e}")
            return None


# Singleton instance
firebase_auth = FirebaseAuth()


