import re

from rest_framework import status


def test_get_short_link_public(api_client, make_recipe):
    recipe = make_recipe()
    url = f'/api/recipes/{recipe.id}/get-link/'
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert 'short-link' in data

    assert re.match(r'^https?://', data['short-link'])
    assert data['short-link'].endswith(f'/recipes/{recipe.id}/')


def test_favorite_add_delete(auth_client, make_recipe):
    recipe = make_recipe()
    url = f'/api/recipes/{recipe.id}/favorite/'
    add1 = auth_client.post(url)
    assert add1.status_code == status.HTTP_201_CREATED
    add2 = auth_client.post(url)
    assert add2.status_code == status.HTTP_400_BAD_REQUEST

    delete1 = auth_client.delete(url)
    assert delete1.status_code == status.HTTP_204_NO_CONTENT
    delete2 = auth_client.delete(url)
    assert delete2.status_code == status.HTTP_400_BAD_REQUEST


def test_shopping_cart_add_delete_download(auth_client, make_recipe):
    recipe = make_recipe()
    url = f'/api/recipes/{recipe.id}/shopping_cart/'
    add = auth_client.post(url)
    assert add.status_code == status.HTTP_201_CREATED

    download = auth_client.get('/api/recipes/download_shopping_cart/')
    assert download.status_code == status.HTTP_200_OK
    content_type = download.headers.get('Content-Type', '')
    assert 'text/plain' in content_type
    assert 'Яйцо (шт) — 2.' in download.content.decode('utf-8')

    delete = auth_client.delete(url)
    assert delete.status_code == status.HTTP_204_NO_CONTENT
