from rest_framework import status


def test_tags_list_public(api_client):
    response = api_client.get('/api/tags/')
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


def test_ingredients_list_public_and_search(api_client):
    response1 = api_client.get('/api/ingredients/')
    assert response1.status_code == status.HTTP_200_OK
    assert isinstance(response1.json(), list)

    response2 = api_client.get('/api/ingredients/?name=я')
    assert response2.status_code == status.HTTP_200_OK
    assert isinstance(response2.json(), list)
