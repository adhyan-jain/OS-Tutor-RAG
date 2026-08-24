"""Tests for src/indexing/s3_sync.py using moto's mocked S3 (no real cloud calls).

Run with: PYTHONPATH=. .venv/bin/python -m pytest tests/test_s3_sync.py -v
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import boto3
import pytest
from moto import mock_aws

from src.indexing.s3_sync import download_index, upload_index

REAL_INDEX_DIR = Path("data/index")


@pytest.fixture(autouse=True)
def s3_env(monkeypatch):
    monkeypatch.setenv("S3_BUCKET", "test-os-tutor-bucket")
    monkeypatch.setenv("S3_PREFIX", "os-tutor-rag/index")
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    monkeypatch.delenv("S3_ENDPOINT_URL", raising=False)
    # boto3 still wants *some* credentials/region present even against moto.
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


@pytest.fixture
def scratch_index_dir(tmp_path):
    """A scratch copy of the real (committed) data/index/, never mutated."""
    scratch = tmp_path / "index_src"
    shutil.copytree(REAL_INDEX_DIR, scratch)
    return scratch


def test_upload_index_puts_expected_keys(scratch_index_dir):
    with mock_aws():
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket="test-os-tutor-bucket")

        upload_index(scratch_index_dir)

        keys = {obj["Key"] for obj in client.list_objects_v2(Bucket="test-os-tutor-bucket")["Contents"]}
        expected = {
            "os-tutor-rag/index/dense.faiss",
            "os-tutor-rag/index/dense_chunks.pkl",
            "os-tutor-rag/index/manifest.json",
        }
        # bm25.pkl is present in the real committed index, so it should upload too.
        if (scratch_index_dir / "bm25.pkl").exists():
            expected.add("os-tutor-rag/index/bm25.pkl")
        assert expected.issubset(keys)


def test_download_index_round_trips_and_is_loadable(scratch_index_dir, tmp_path):
    download_dir = tmp_path / "index_downloaded"

    with mock_aws():
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket="test-os-tutor-bucket")

        upload_index(scratch_index_dir)
        found = download_index(download_dir)

        assert found is True
        for filename in ["dense.faiss", "dense_chunks.pkl", "manifest.json"]:
            src = scratch_index_dir / filename
            dst = download_dir / filename
            assert dst.exists()
            assert src.read_bytes() == dst.read_bytes(), f"{filename} not byte-identical after round trip"

    # Confirm the downloaded FAISS index + manifest are actually usable, not
    # just byte-copied.
    import json
    import pickle

    import faiss

    index = faiss.read_index(str(download_dir / "dense.faiss"))
    with open(download_dir / "dense_chunks.pkl", "rb") as f:
        chunks = pickle.load(f)
    assert index.ntotal == len(chunks) > 0

    with open(download_dir / "manifest.json") as f:
        manifest = json.load(f)
    assert "files" in manifest and len(manifest["files"]) > 0


def test_download_index_returns_false_for_empty_bucket(tmp_path):
    download_dir = tmp_path / "index_empty"

    with mock_aws():
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket="test-os-tutor-bucket")  # bucket exists but has nothing uploaded

        found = download_index(download_dir)
        assert found is False


def test_download_index_returns_false_for_nonexistent_bucket(tmp_path):
    download_dir = tmp_path / "index_no_bucket"

    with mock_aws():
        # No create_bucket call at all -- the bucket itself doesn't exist.
        found = download_index(download_dir)
        assert found is False


def test_upload_index_requires_s3_bucket_env(scratch_index_dir, monkeypatch):
    monkeypatch.delenv("S3_BUCKET", raising=False)
    with pytest.raises(RuntimeError, match="S3_BUCKET"):
        upload_index(scratch_index_dir)
