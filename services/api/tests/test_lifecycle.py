def test_lifecycle_export_requires_dedicated_secret(api_client):
    missing = api_client.post(
        "/internal/lifecycle/user-system-id",
        json={"action": "export", "email": "test@example.com"},
    )
    assert missing.status_code == 401

    response = api_client.post(
        "/internal/lifecycle/user-system-id",
        headers={"authorization": "Bearer test-lifecycle-secret"},
        json={"action": "export", "email": "test@example.com", "requestId": "job_1"},
    )
    assert response.status_code == 200
    assert response.json()["service"] == "extract"
    assert response.json()["requestId"] == "job_1"
    assert response.json()["data"]["user"]["email"] == "test@example.com"
    assert "password_hash" not in response.json()["data"]["user"]


def test_lifecycle_delete_removes_the_local_extract_account(api_client):
    headers = {"authorization": "Bearer test-lifecycle-secret"}
    deleted = api_client.post(
        "/internal/lifecycle/user-system-id",
        headers=headers,
        json={"action": "delete", "email": "test@example.com", "requestId": "job_2"},
    )
    assert deleted.status_code == 200, deleted.text
    assert deleted.json()["deleted"]["userDeleted"] is True

    exported = api_client.post(
        "/internal/lifecycle/user-system-id",
        headers=headers,
        json={"action": "export", "email": "test@example.com"},
    )
    assert exported.status_code == 200
    assert exported.json()["data"]["user"] is None
