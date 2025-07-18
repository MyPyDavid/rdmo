import pytest

from django.urls import reverse

users = (
    ('editor', 'editor'),
    ('reviewer', 'reviewer'),
    ('user', 'user'),
    ('site', 'site'),
    ('api', 'api'),
    ('anonymous', None)
)

status_map = {
    'list': {
        'editor': 200, 'reviewer': 200, 'user': 200, 'site': 200, 'api': 200, 'anonymous': 401
    }
}

urlnames = {
    'list': 'v1-management:meta-list',
}


@pytest.mark.parametrize('username,password', users)
def test_list(db, client, username, password):
    client.login(username=username, password=password)

    url = reverse(urlnames['list'])
    response = client.get(url)
    assert response.status_code == status_map['list'][username], response.json()
