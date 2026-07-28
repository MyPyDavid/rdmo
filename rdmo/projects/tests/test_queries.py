import pytest

from django.urls import reverse

max_queries = [
    # method, urlname, max_queries, url_args
    ('get', 'project_answers', 38, [1]),
    ('get', 'project_answers_export', 31, [1, 'html']),
    ('get', 'v1-projects:project-navigation', 43, [1]),
    ('get', 'v1-projects:project-answers', 43, [1]),
    ('post', 'v1-projects:project-progress', 44, [1]),
    ('get', 'v1-projects:project-page-detail', 46, [1, 1]),
    ('get', 'v1-projects:project-page-detail', 50, [1, 42]),
    ('get', 'v1-projects:project-page-detail', 62, [1, 87]),
]


@pytest.mark.performance
@pytest.mark.parametrize('method,urlname,max_queries,url_args', max_queries)
def test_queries(db, client, django_assert_max_num_queries, method, urlname, max_queries, url_args):
    client.login(username='owner', password='owner')
    url = reverse(urlname, args=url_args)

    with django_assert_max_num_queries(max_queries):
        if method == 'get':
            response = client.get(url)
        elif method == 'post':
            response = client.post(url)

    assert response.status_code == 200


@pytest.mark.performance
def test_resolve_queries(db, client, django_assert_max_num_queries):
    client.login(username='admin', password='admin')
    url = reverse('v1-projects:project-resolve', args=[1])
    data = [
        {
            'set_prefix': '',
            'set_index': 0,
            'element_type': 'questions',
            'element_id': 104,
        },
        {
            'set_prefix': '',
            'set_index': 1,
            'element_type': 'questions',
            'element_id': 104,
        },
    ]

    # Request authentication and permissions plus the project, the
    # question-condition relation, the conditions, and the project values.
    with django_assert_max_num_queries(9):
        response = client.post(url, data, content_type='application/json')

    assert response.status_code == 200
    assert [
        {key: value for key, value in result.items() if key != 'result'}
        for result in response.json()
    ] == data
    assert all(isinstance(result['result'], bool) for result in response.json())
