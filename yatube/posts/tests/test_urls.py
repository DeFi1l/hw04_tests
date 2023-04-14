from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.guest_client = Client()

        cls.user = User.objects.create(username='HasNoName')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.user_not_author = User.objects.create(username='NotAuthor')
        cls.authorized_not_author_client = Client()
        cls.authorized_not_author_client.force_login(cls.user_not_author)

        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
        )

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='some-slug',
            description='Тестовое описание',
        )

    def setUp(self) -> None:
        cache.clear()

    def test_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_porfile_page(self):
        response = self.guest_client.get('/profile/HasNoName/')
        self.assertEqual(response.status_code, 200)

    def test_posts_detail_page(self):
        response = self.guest_client.get(f'/posts/{self.post.id}/')
        self.assertEqual(response.status_code, 200)

    def test_group_page(self):
        response = self.guest_client.get('/group/some-slug/')
        self.assertEqual(response.status_code, 200)

    def test_post_create_page(self):
        response_authorized = self.authorized_client.get('/create/')
        response_not_authorized = self.guest_client.get('/create/')

        self.assertEqual(response_authorized.status_code, 200)
        self.assertEqual(response_not_authorized.status_code, 302)

    def test_post_edit_page(self):
        response_authorized = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            )
        )
        response_not_authorized = self.guest_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            )
        )
        response_not_author = self.authorized_not_author_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            )
        )

        self.assertEqual(
            response_authorized.status_code, 200
        )
        self.assertEqual(
            response_not_authorized.status_code, 302
        )
        self.assertEqual(
            response_not_author.status_code, 302
        )

    def test_unexisting_page(self):
        response = self.guest_client.get('/unexisting_page/')

        self.assertEqual(response.status_code, 404)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            '/group/some-slug/': 'posts/group_list.html',
            '/profile/HasNoName/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/': 'posts/index.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
