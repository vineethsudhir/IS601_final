def test_request_index(client):
    """This makes the index page"""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Hello, World!" in response.data

def test_request_page_not_found(client):
    response = client.get("/page")
    assert response.status_code == 404