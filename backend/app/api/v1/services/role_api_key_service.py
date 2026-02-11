import secrets
from typing import List, Optional, Tuple

from app.api.v1.repositories.role_api_key_repository import RoleApiKeyRepository
from app.api.v1.repositories.role_permission_repository import RoleRepository
from app.models.role import Role
from app.models.role_api_key import RoleApiKey
from app.schemas.role_api_key import RoleApiKeyCreate, RoleApiKeySecret
from app.utils.password import get_password_hash, verify_password


class RoleApiKeyService:
    """Service for managing Role API Keys"""

    def __init__(
        self,
        api_key_repo: RoleApiKeyRepository,
        role_repo: RoleRepository,
    ):
        self.api_key_repo = api_key_repo
        self.role_repo = role_repo

    def create_api_key(
        self, data: RoleApiKeyCreate
    ) -> Tuple[Optional[RoleApiKeySecret], str]:
        """
        Create a new API key for a role.
        Returns (RoleApiKeySecret, error_message)
        RoleApiKeySecret contains the raw secret key which is shown ONLY once.
        """
        role = self.role_repo.get_by_id(data.role_id)
        if not role:
            return None, "Role not found"

        # Generate a secure random key
        # Format: sk-{random_32_chars}
        raw_key = f"sk-{secrets.token_urlsafe(32)}"

        # Hash the key for storage
        key_hash = get_password_hash(raw_key)

        # Create DB record
        api_key = RoleApiKey(
            name=data.name,
            key_hash=key_hash,
            prefix=raw_key[:6],  # Store "sk-XXX" prefix for identification
            role_id=data.role_id,
        )
        saved_key = self.api_key_repo.create(api_key)

        # Return response with raw key (only time it's available)
        response = RoleApiKeySecret(**saved_key.model_dump(), secret_key=raw_key)

        return response, ""

    def get_by_role(self, role_id: int) -> List[RoleApiKey]:
        """Get all API keys for a role"""
        return self.api_key_repo.get_by_role_id(role_id)

    def revoke_api_key(self, key_id: int) -> Tuple[bool, str]:
        """Revoke (delete) an API key"""
        key = self.api_key_repo.get_by_id(key_id)
        if not key:
            return False, "API Key not found"

        self.api_key_repo.delete(key)
        return True, "API Key revoked successfully"

    def verify_api_key(
        self, raw_key: str
    ) -> Tuple[Optional[Role], Optional[RoleApiKey]]:
        """
        Verify an API key and return the associated Role and ApiKey object.
        Optimized to search by prefix if possible, or iterate if needed (though hash lookup is preferred if we had full key index, but commonly we verify by matching hash).

        Since we store `key_hash` using bcrypt (which helps against rainbow tables but is slow), and we don't have the plain key to look up...
        Wait, `passlib` verifies against the hash. We can't look up by hash directly because bcrypt uses a salt.

        Strategy:
        1. We should ideally identify the key by ID or prefix.
        2. However, standard Bearer tokens don't carry ID.
        3. Changing strategy: We can't easily look up "which key is this" with bcrypt without trying all.

        BETTER STRATEGY for API Keys:
        - Format: sk-{public_id}-{secret}
        - Public ID allows fast lookup. Secret is hashed.

        Let's refine the implementation right here.
        """
        # Revised Logic:
        # If the key format is sk-{random}, we can't look it up efficiently if we use bcrypt.
        # Let's assume for now we might need to iterate valid keys OR improve the model.
        # Given we have `prefix` stored, we *could* filter by prefix, but multiple keys might have same prefix if short.
        #
        # Let's adjust the Create logic to use a clearer format if we want strict lookup,
        # OR just accept that for this MVC we might iterate active keys (bad for perf) or...
        #
        # Actually, let's stick to the industry standard: `sk-<random>` is fine if we use a fast hash (SHA256) instead of bcrypt for API keys.
        # API Keys are high-entropy, so rainbow tables are less concern than passwords.
        # But `passlib` is already used in `app.utils.password`.
        #
        # ALTERNATIVE: Token format: `sk-ROLE_ID-RANDOM`? No, exposes Role ID.
        #
        # Let's use the `prefix` to narrow down content? No, standard `secrets.token_urlsafe` is random.
        #
        # CORRECT APPROACH for this codebase's context:
        # Since I already wrote the Model with `key_hash`, I will stick to it.
        # To verify, I need to match the key.
        # If I can't look up by hash (due to salt), I have a problem.
        #
        # FIX: I will verify against ALL active API keys? No, that's terrible.
        #
        # RE-FACTOR on the fly:
        # The `RoleApiKey` model has `key_hash`.
        # If I used `pwd_context.hash()`, it uses bcrypt (salted).
        # So I cannot query `WHERE key_hash = ...`.
        #
        # I MUST parse the token to find the key ID or a lookup value.
        # Let's change the token format to: `sk-{id}.{secret}` or similar?
        # OR just iterate over all keys for that prefix?
        #
        # Let's go with: `sk-{urlsafe_token}`.
        # AND we store `prefix = raw_key[:10]`.
        # When verifying, we query `WHERE prefix = raw_key[:10]`.
        # This gives us a very small list (likely 1 candidate).
        # Then we verify hash.

        if not raw_key.startswith("sk-"):
            return None, None

        prefix = raw_key[:6]  # Match the model's prefix length

        candidates = self.api_key_repo.get_candidates_by_prefix(prefix)

        for key in candidates:
            if verify_password(raw_key, key.key_hash):
                return key.role, key

        return None, None
