from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post


User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth1')
        cls.not_user = User.objects.create_user(username='auth2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )
        cls.urls_redirects = {
            '/create/': '/auth/login/?next=/create/',
            f'/posts/{cls.post.id}/edit/':
                f'/auth/login/?next=/posts/{cls.post.id}/edit/',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.not_author_client = Client()
        self.authorized_client.force_login(self.user)
        self.not_author_client.force_login(self.not_user)

    def test_for_everyone(self):
        """Страницы, доступные любому пользователю."""
        urls = (
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user}/',
            f'/posts/{self.post.pk}/'
        )
        for url in urls:
            with self.subTest():
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_page_404(self):
        """Страница /unexisting_page/ не существует."""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_create_for_authorized(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_for_author(self):
        """Страница /posts/1/edit/ доступна автору."""
        response = self.authorized_client.get(f'/posts/{self.post.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_user_not_author_edit_post(self):
        """Редирект на стр поста при редактировании поста неавтором."""
        response = self.not_author_client.get(
            f'/posts/{self.post.id}/edit/'
        )
        self.assertRedirects(
            response, f'/posts/{self.post.id}/'
        )

    def test_urls_redirect_anonymous_on_login(self):
        """Редирект на логин при создании/редактировании поста анонимом."""
        for url, redirect_url in self.urls_redirects.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, redirect_url)

    def test_url_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_urls = {
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            f'/posts/{self.post.pk}/edit/': 'posts/',
            '/create/': 'posts/post_create.html',
            '/lol/': 'core/404.html'
        }
        for url, template in templates_urls.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
