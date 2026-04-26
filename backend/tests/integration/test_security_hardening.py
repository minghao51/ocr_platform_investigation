import asyncio
from pathlib import Path

from PIL import Image

from auth import create_access_token
from database import crud


def _create_test_png(path: Path) -> None:
    image = Image.new("RGB", (64, 64), color="white")
    image.save(path, format="PNG")


def test_quality_check_enforces_file_ownership(client, temp_db_env, auth_header):
    uploads_dir = Path(temp_db_env) / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    file_path = uploads_dir / "owner-image.png"
    _create_test_png(file_path)

    file_id = "quality-owner-1"
    asyncio.run(
        crud.create_uploaded_file(
            file_id=file_id,
            original_filename="owner-image.png",
            file_extension=".png",
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            content_type="image/png",
            user_id=1,
            guest_token=None,
        )
    )

    owner_response = client.post(
        "/api/quality/check",
        json={"file_id": file_id},
        headers=auth_header,
    )
    assert owner_response.status_code == 200

    other_user_token = create_access_token(user_id=2, username="other", is_admin=False)
    forbidden_response = client.post(
        "/api/quality/check",
        json={"file_id": file_id},
        headers={"Authorization": f"Bearer {other_user_token}"},
    )
    assert forbidden_response.status_code == 403


def test_quality_check_requires_matching_guest_token(client, temp_db_env):
    uploads_dir = Path(temp_db_env) / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    file_path = uploads_dir / "guest-image.png"
    _create_test_png(file_path)

    file_id = "quality-guest-1"
    guest_token = "guest-token-abc"
    asyncio.run(
        crud.create_uploaded_file(
            file_id=file_id,
            original_filename="guest-image.png",
            file_extension=".png",
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            content_type="image/png",
            user_id=None,
            guest_token=guest_token,
        )
    )

    allowed = client.post(
        "/api/quality/check",
        json={"file_id": file_id},
        headers={"X-Guest-Token": guest_token},
    )
    assert allowed.status_code == 200

    denied = client.post(
        "/api/quality/check",
        json={"file_id": file_id},
    )
    assert denied.status_code == 403


def test_admin_only_analytics_and_benchmarks(client, auth_header, test_user_auth_header):
    # Admin succeeds
    admin_analytics = client.get("/api/analytics/usage", headers=auth_header)
    assert admin_analytics.status_code == 200

    admin_runs = client.get("/api/benchmarks/runs", headers=auth_header)
    assert admin_runs.status_code == 200

    # Non-admin blocked
    user_analytics = client.get("/api/analytics/usage", headers=test_user_auth_header)
    assert user_analytics.status_code == 403

    user_runs = client.get("/api/benchmarks/runs", headers=test_user_auth_header)
    assert user_runs.status_code == 403


def test_quality_check_upload_rejects_oversized_payload_and_cleans_temp_file(
    client, temp_db_env
):
    uploads_dir = Path(temp_db_env) / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    before_files = set(uploads_dir.iterdir())

    oversized = b"\xff" * (10 * 1024 * 1024 + 1)
    response = client.post(
        "/api/quality/check-upload",
        files={"file": ("oversized.png", oversized, "image/png")},
        data={"estimated_dpi": "200"},
    )

    assert response.status_code == 413
    after_files = set(uploads_dir.iterdir())
    assert before_files == after_files
