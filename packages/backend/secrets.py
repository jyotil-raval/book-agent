"""
Centralized secret loader.

Order of precedence:
1. Environment variable (os.environ)
2. Local .env file (python-dotenv) — dev only, safe if .env is gitignored
3. AWS Secrets Manager (if boto3 available and AWS env configured)
4. Google Secret Manager (if google-cloud-secret-manager installed and GCP env configured)
5. Optional file path (if provided)

This module caches fetched secrets to avoid repeated network calls.

Usage:
    from secrets import get_secret
    key = get_secret("OPENAI_KEY", required=True)
"""

import os
from functools import lru_cache
from typing import Optional

# Optional imports — only import if available to avoid extra dependencies for simple setups
try:
    import boto3  # type: ignore
    from botocore.exceptions import BotoCoreError, ClientError  # type: ignore
    _HAS_BOTO3 = True
except Exception:
    _HAS_BOTO3 = False

try:
    from google.cloud import secretmanager  # type: ignore
    _HAS_GCP = True
except Exception:
    _HAS_GCP = False

# Optional dotenv support for local dev
try:
    from dotenv import load_dotenv
    from pathlib import Path
    # Explicitly attempt to load a .env located next to this file (packages/backend/.env)
    _THIS_DIR = Path(__file__).resolve().parent
    _DOTENV_PATH = _THIS_DIR / ".env"
    if _DOTENV_PATH.exists():
        load_dotenv(dotenv_path=str(_DOTENV_PATH))
    else:
        # fallback to default search behavior (cwd / parents)
        load_dotenv()
    _HAS_DOTENV = True
except Exception:
    _HAS_DOTENV = False


@lru_cache(maxsize=64)
def _get_from_env(name: str) -> Optional[str]:
    return os.getenv(name)


@lru_cache(maxsize=64)
def _get_from_aws(name: str) -> Optional[str]:
    """
    Attempt to read secret from AWS Secrets Manager.
    Expects AWS credentials to be provided via normal AWS means (env vars, role).
    Secret name can be the env var itself or a mapping you maintain.
    """
    if not _HAS_BOTO3:
        return None
    try:
        client = boto3.client("secretsmanager")
        # try to get secret by name
        resp = client.get_secret_value(SecretId=name)
        secret = resp.get("SecretString")
        if secret:
            return secret
        # could be binary
        if "SecretBinary" in resp:
            return resp["SecretBinary"].decode("utf-8")
    except (BotoCoreError, ClientError):
        return None
    return None


@lru_cache(maxsize=64)
def _get_from_gcp(name: str) -> Optional[str]:
    """
    Attempt to read secret from Google Secret Manager.
    Name is expected to be the secret id; project detection is via ADC or GOOGLE_CLOUD_PROJECT env var.
    Returns the latest version value.
    """
    if not _HAS_GCP:
        return None
    try:
        client = secretmanager.SecretManagerServiceClient()
        project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT")
        if not project:
            # If project not set, we can't build default path reliably
            return None
        name_path = f"projects/{project}/secrets/{name}/versions/latest"
        response = client.access_secret_version(request={"name": name_path})
        payload = response.payload.data.decode("UTF-8")
        return payload
    except Exception:
        return None


@lru_cache(maxsize=256)
def get_secret(name: str, required: bool = False, fallback_file: Optional[str] = None) -> Optional[str]:
    """
    Resolve secret by trying multiple backends.
    - name: env var name or secret id
    - required: if True, raises RuntimeError when secret not found
    - fallback_file: optional path to read the secret from (e.g. Docker secret file)
    """
    # 1) env var
    val = _get_from_env(name)
    if val:
        return val

    # 2) dotenv already loaded at module import; env will have been set

    # 3) AWS Secrets Manager
    val = _get_from_aws(name)
    if val:
        return val

    # 4) GCP Secret Manager
    val = _get_from_gcp(name)
    if val:
        return val

    # 5) fallback file
    if fallback_file and os.path.isfile(fallback_file):
        try:
            with open(fallback_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            pass

    if required:
        raise RuntimeError(f"Required secret '{name}' not found in env / secret managers / file.")
    return None