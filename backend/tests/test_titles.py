def test_titles_endpoint(client):
    response = client.get("/api/titles")

    assert response.status_code == 200
    assert "titles" in response.json()
    assert isinstance(response.json()["titles"], list)
