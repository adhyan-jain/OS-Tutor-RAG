"""Push/pull the on-disk retrieval index to/from S3 (or an S3-compatible
store, e.g. Cloudflare R2 via S3_ENDPOINT_URL).

This lets a fresh deploy (no local data/index/) start from whatever index a
previous run already built and uploaded, instead of always rebuilding the
whole corpus locally. Configuration is read straight from environment
variables (no new config framework):

- S3_BUCKET: required for either function to do anything.
- S3_PREFIX: key prefix under the bucket (e.g. "os-tutor-rag/index").
- AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY: credentials. If unset, boto3
  falls back to its normal credential chain (env, shared config, instance
  role, etc).
- S3_ENDPOINT_URL: optional. Omitted entirely (not passed as None) unless
  set, so boto3 uses AWS's real default endpoint. Set this to an R2 account
  endpoint to point at Cloudflare R2 instead of AWS S3 -- that's the whole
  R2-compatibility story here, since R2 speaks the S3 API.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger("src.indexing.s3_sync")

# Every file an index directory may contain. bm25.pkl is optional (e.g. a
# dense-only setup never writes it), so its absence is not an error on either
# upload or download.
_INDEX_FILES = ["dense.faiss", "dense_chunks.pkl", "bm25.pkl", "manifest.json"]


def _get_client():
    """Construct a boto3 S3 client from env vars.

    Returns:
        A boto3 S3 client.
    """
    import boto3

    kwargs: dict[str, str] = {}
    access_key = os.environ.get("AWS_ACCESS_KEY_ID")
    secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
    if access_key:
        kwargs["aws_access_key_id"] = access_key
    if secret_key:
        kwargs["aws_secret_access_key"] = secret_key

    endpoint_url = os.environ.get("S3_ENDPOINT_URL")
    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url

    return boto3.client("s3", **kwargs)


def _require_bucket() -> str:
    bucket = os.environ.get("S3_BUCKET")
    if not bucket:
        raise RuntimeError(
            "S3_BUCKET is not set -- required to upload/download the index. "
            "Set it (and optionally S3_PREFIX, S3_ENDPOINT_URL, and AWS "
            "credentials) or don't call upload_index()/download_index()."
        )
    return bucket


def _prefix() -> str:
    prefix = os.environ.get("S3_PREFIX", "")
    return prefix.rstrip("/")


def _key_for(filename: str) -> str:
    prefix = _prefix()
    return f"{prefix}/{filename}" if prefix else filename


def upload_index(index_dir: Path) -> None:
    """Upload the index files present in `index_dir` to S3.

    Uploads whichever of dense.faiss, dense_chunks.pkl, bm25.pkl and
    manifest.json actually exist in `index_dir` -- missing files (e.g.
    bm25.pkl for a dense-only setup) are skipped, not an error.

    Args:
        index_dir: Local directory holding the index files to upload.

    Raises:
        RuntimeError: If S3_BUCKET is unset.
    """
    bucket = _require_bucket()
    client = _get_client()

    uploaded = []
    for filename in _INDEX_FILES:
        local_path = index_dir / filename
        if not local_path.exists():
            continue
        key = _key_for(filename)
        client.upload_file(str(local_path), bucket, key)
        uploaded.append(key)

    if uploaded:
        logger.info("Uploaded %d index file(s) to s3://%s/: %s", len(uploaded), bucket, uploaded)
    else:
        logger.warning("upload_index: no index files found in %s -- nothing uploaded", index_dir)


def download_index(index_dir: Path) -> bool:
    """Download the index files found under the configured S3 prefix into `index_dir`.

    Args:
        index_dir: Local directory to download the index files into.

    Returns:
        True if a usable index was found and downloaded (at minimum
        dense.faiss + dense_chunks.pkl), False if the bucket/prefix has
        nothing there (so callers can fall back to a local rebuild).

    Raises:
        RuntimeError: If S3_BUCKET is unset.
    """
    import botocore.exceptions

    bucket = _require_bucket()
    client = _get_client()

    index_dir.mkdir(parents=True, exist_ok=True)

    downloaded = []
    for filename in _INDEX_FILES:
        key = _key_for(filename)
        local_path = index_dir / filename
        try:
            client.download_file(bucket, key, str(local_path))
            downloaded.append(key)
        except botocore.exceptions.ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ("404", "NoSuchKey", "NoSuchBucket"):
                # Nothing at this key/bucket yet -- clean up any partial file
                # download_file may have created before failing.
                local_path.unlink(missing_ok=True)
                continue
            raise

    # A usable index needs at least the dense FAISS index and its chunk list;
    # bm25.pkl/manifest.json are recovered opportunistically if present.
    required = {_key_for("dense.faiss"), _key_for("dense_chunks.pkl")}
    if required.issubset(set(downloaded)):
        logger.info("Downloaded %d index file(s) from s3://%s/: %s", len(downloaded), bucket, downloaded)
        return True

    logger.info("download_index: no usable index found under s3://%s/%s -- nothing downloaded", bucket, _prefix())
    return False
