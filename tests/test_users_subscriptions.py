from rest_framework import status


def test_me_requires_auth(api_client):
    response = api_client.get('/api/users/me/')
    assert response.status_code in (
        status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN
    )


def test_subscribe_and_unsubscribe(auth_client, another_user):
    url = f'/api/users/{another_user.id}/subscribe/'

    add1 = auth_client.post(url)
    assert add1.status_code == status.HTTP_201_CREATED

    add2 = auth_client.post(url)
    assert add2.status_code == status.HTTP_400_BAD_REQUEST

    subscriptions = auth_client.get('/api/users/subscriptions/')
    assert subscriptions.status_code == status.HTTP_200_OK
    assert isinstance(subscriptions.json().get('results', []), list)

    delete = auth_client.delete(url)
    assert delete.status_code == status.HTTP_204_NO_CONTENT
