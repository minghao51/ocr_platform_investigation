import asyncio

from database import crud
from routers.job_serialization import serialize_job


def test_websocket_ticket_and_status_flow(client, auth_header, temp_db_env):
    _ = temp_db_env
    job_id = asyncio.run(
        crud.create_job(
            file_name="websocket-sample.pdf",
            file_type="pdf",
            provider="gemini",
            model="gemini-2.5-flash",
            schema_id=None,
            schema_name="Custom",
            processing_method="vision",
            user_id=1,
        )
    )
    asyncio.run(
        crud.update_job_status(
            job_id,
            "processing",
            processing_time=0.25,
        )
    )

    ticket_response = client.post("/api/ws/ticket", headers=auth_header)
    assert ticket_response.status_code == 200
    ticket_payload = ticket_response.json()
    assert ticket_payload["expires_in"] == 60
    ticket = ticket_payload["ticket"]

    from routers.websocket import broadcast_job_update, manager

    try:
        with client.websocket_connect(f"/api/ws/job/{job_id}?ticket={ticket}") as ws:
            initial = ws.receive_json()
            assert initial["type"] == "status"
            assert initial["data"]["job_id"] == job_id
            assert initial["data"]["status"] == "processing"

            updated_job = asyncio.run(
                crud.update_job_status(
                    job_id,
                    "success",
                    result={"ok": True},
                    processing_time=1.0,
                )
            )
            asyncio.run(broadcast_job_update(job_id, serialize_job(updated_job)))

            update = ws.receive_json()
            assert update["type"] == "status_update"
            assert update["data"]["job_id"] == job_id
            assert update["data"]["status"] == "success"
            assert update["data"]["result"] == {"ok": True}
    finally:
        manager.active_connections.clear()
        manager.connection_jobs.clear()
