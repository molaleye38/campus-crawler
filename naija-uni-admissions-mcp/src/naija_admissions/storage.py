"""Supabase Storage (S3-compatible) helpers for CKAP.

Uploads HTML, PDF, Markdown, screenshots to Supabase Storage buckets.
Organizes by institution slug and academic session.
"""

from __future__ import annotations

import hashlib
import mimetypes
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from .utils import safe_log, slugify

# Bucket names
CRAWL_ASSETS_BUCKET = "crawl-assets"          # private: HTML, PDF, screenshots, markdown
INSTITUTION_ASSETS_BUCKET = "institution-assets"  # public: logos, public documents

# S3 endpoint from environment
S3_ENDPOINT = os.getenv("SUPABASE_S3_ENDPOINT", "https://fhqylwughhlxumgpsvho.storage.supabase.co/storage/v1/s3")
S3_REGION = os.getenv("SUPABASE_S3_REGION", "eu-west-1")
S3_ACCESS_KEY = os.getenv("SUPABASE_S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("SUPABASE_S3_SECRET_KEY")

_s3_client = None


def get_s3_client():
    """Get or create boto3 S3 client configured for Supabase Storage."""
    global _s3_client
    if _s3_client is None:
        if not S3_ACCESS_KEY or not S3_SECRET_KEY:
            raise RuntimeError(
                "Supabase S3 credentials not configured. "
                "Set SUPABASE_S3_ACCESS_KEY and SUPABASE_S3_SECRET_KEY in .env"
            )
        _s3_client = boto3.client(
            "s3",
            endpoint_url=S3_ENDPOINT,
            region_name=S3_REGION,
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY,
            config=Config(
                s3={"addressing_style": "virtual"},
                retries={"max_attempts": 3, "mode": "adaptive"},
            ),
        )
    return _s3_client


def ensure_buckets_exist() -> None:
    """Create buckets if they don't exist (idempotent)."""
    client = get_s3_client()
    for bucket in (CRAWL_ASSETS_BUCKET, INSTITUTION_ASSETS_BUCKET):
        try:
            client.head_bucket(Bucket=bucket)
        except ClientError as e:
            if e.response["Error"]["Code"] in ("404", "NoSuchBucket"):
                client.create_bucket(Bucket=bucket)
                safe_log("storage_bucket_created", bucket=bucket)
            else:
                raise


def _compute_hash(data: bytes) -> str:
    """Compute SHA256 hash of content."""
    return hashlib.sha256(data).hexdigest()


def _guess_mime_type(path: str | None, content: bytes | None = None) -> str:
    """Guess MIME type from file extension or content."""
    if path:
        mime, _ = mimetypes.guess_type(path)
        if mime:
            return mime
    if content:
        if content.startswith(b"%PDF"):
            return "application/pdf"
        if content.startswith(b"<") or content.startswith(b"<!DOCTYPE"):
            return "text/html"
        if content.startswith(b"# ") or b"\n# " in content[:200]:
            return "text/markdown"
    return "application/octet-stream"


def _storage_path(
    institution_slug: str,
    academic_session: str,
    asset_type: str,
    filename: str,
    is_public: bool = False,
) -> str:
    """Generate storage object key."""
    # Format: institutions/{slug}/{session}/{asset_type}/{filename}
    return f"institutions/{institution_slug}/{academic_session}/{asset_type}/{filename}"


def upload_bytes(
    institution_name: str,
    academic_session: str,
    asset_type: str,  # 'html', 'pdf', 'markdown', 'screenshot', 'json'
    filename: str,
    content: bytes,
    is_public: bool = False,
    metadata: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Upload raw bytes to Supabase Storage."""
    client = get_s3_client()
    institution_slug = slugify(institution_name)
    bucket = INSTITUTION_ASSETS_BUCKET if is_public else CRAWL_ASSETS_BUCKET
    key = _storage_path(institution_slug, academic_session, asset_type, filename, is_public)
    
    content_hash = _compute_hash(content)
    mime_type = _guess_mime_type(filename, content)
    
    extra_args = {
        "ContentType": mime_type,
        "Metadata": {
            "institution": institution_name,
            "academic_session": academic_session,
            "asset_type": asset_type,
            "content_hash": content_hash,
            **(metadata or {}),
        },
    }
    
    client.put_object(Bucket=bucket, Key=key, Body=content, **extra_args)
    
    # Construct public URL if public bucket
    public_url = None
    if is_public:
        public_url = f"{S3_ENDPOINT.replace('/s3', '')}/object/public/{bucket}/{key}"
    
    safe_log("storage_uploaded", bucket=bucket, key=key, size=len(content), hash=content_hash[:16])
    
    return {
        "bucket": bucket,
        "key": key,
        "size": len(content),
        "content_hash": content_hash,
        "mime_type": mime_type,
        "public_url": public_url,
        "storage_path": f"s3://{bucket}/{key}",
    }


def upload_file(
    institution_name: str,
    academic_session: str,
    asset_type: str,
    file_path: str | Path,
    is_public: bool = False,
    metadata: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Upload a file from disk."""
    path = Path(file_path)
    content = path.read_bytes()
    filename = path.name
    return upload_bytes(institution_name, academic_session, asset_type, filename, content, is_public, metadata)


def download_bytes(bucket: str, key: str) -> bytes | None:
    """Download object content as bytes."""
    client = get_s3_client()
    try:
        response = client.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            return None
        raise


def delete_object(bucket: str, key: str) -> bool:
    """Delete an object from storage."""
    client = get_s3_client()
    try:
        client.delete_object(Bucket=bucket, Key=key)
        safe_log("storage_deleted", bucket=bucket, key=key)
        return True
    except ClientError as e:
        safe_log("storage_delete_failed", bucket=bucket, key=key, error=str(e))
        return False


def object_exists(bucket: str, key: str) -> bool:
    """Check if object exists."""
    client = get_s3_client()
    try:
        client.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        raise


def generate_presigned_url(
    bucket: str,
    key: str,
    expiration: int = 3600,
    method: str = "get_object",
) -> str:
    """Generate a presigned URL for temporary access."""
    client = get_s3_client()
    return client.generate_presigned_url(
        method,
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expiration,
    )


def list_institution_assets(
    institution_name: str,
    academic_session: str | None = None,
    asset_type: str | None = None,
    bucket: str = CRAWL_ASSETS_BUCKET,
) -> list[dict[str, Any]]:
    """List all assets for an institution."""
    client = get_s3_client()
    institution_slug = slugify(institution_name)
    prefix = f"institutions/{institution_slug}/"
    if academic_session:
        prefix += f"{academic_session}/"
    if asset_type:
        prefix += f"{asset_type}/"
    
    paginator = client.get_paginator("list_objects_v2")
    results = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            results.append({
                "key": obj["Key"],
                "size": obj["Size"],
                "last_modified": obj["LastModified"],
                "etag": obj["ETag"].strip('"'),
            })
    return results


def get_content_hash_from_storage(bucket: str, key: str) -> str | None:
    """Retrieve content_hash from object metadata."""
    client = get_s3_client()
    try:
        response = client.head_object(Bucket=bucket, Key=key)
        return response.get("Metadata", {}).get("content_hash")
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return None
        raise


# ============================================================================
# High-level asset upload for crawl pipeline
# ============================================================================

def store_crawl_artifacts(
    institution_name: str,
    academic_session: str,
    source_url: str,
    html_content: str | None = None,
    markdown_content: str | None = None,
    pdf_content: bytes | None = None,
    screenshot_png: bytes | None = None,
    extracted_json: dict | None = None,
) -> dict[str, dict[str, Any]]:
    """Store all crawl artifacts for an institution URL in one call.
    
    Returns dict mapping asset_type -> upload result.
    """
    results = {}
    url_slug = slugify(source_url)[:100]
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    if html_content:
        results["html"] = upload_bytes(
            institution_name, academic_session, "html",
            f"{url_slug}_{timestamp}.html",
            html_content.encode("utf-8"),
            metadata={"source_url": source_url},
        )
    
    if markdown_content:
        results["markdown"] = upload_bytes(
            institution_name, academic_session, "markdown",
            f"{url_slug}_{timestamp}.md",
            markdown_content.encode("utf-8"),
            metadata={"source_url": source_url},
        )
    
    if pdf_content:
        results["pdf"] = upload_bytes(
            institution_name, academic_session, "pdf",
            f"{url_slug}_{timestamp}.pdf",
            pdf_content,
            metadata={"source_url": source_url},
        )
    
    if screenshot_png:
        results["screenshot"] = upload_bytes(
            institution_name, academic_session, "screenshot",
            f"{url_slug}_{timestamp}.png",
            screenshot_png,
            metadata={"source_url": source_url},
        )
    
    if extracted_json:
        import json
        results["json"] = upload_bytes(
            institution_name, academic_session, "json",
            f"{url_slug}_{timestamp}.json",
            json.dumps(extracted_json, ensure_ascii=False, indent=2).encode("utf-8"),
            metadata={"source_url": source_url},
        )
    
    return results