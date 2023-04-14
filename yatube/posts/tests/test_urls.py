from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from ..models import Group, Post
from django.urls import reverse
from http import HTTPStatus


User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_2 = User.objects.create_user(username='User2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст поста',
        )
        cls.index_url = reverse('posts:index')
        cls.create_url = reverse('posts:post_create')
        cls.profile_url = (reverse('posts:profile',
                                   kwargs={'username':
                                           PostURLTests.
                                           post.author}))
        cls.post_url = (reverse('posts:post_detail',
                                kwargs={'post_id':
                                        PostURLTests.
                                        post.id}))
        cls.post_edit_url = (reverse('posts:post_edit',
                                     kwargs={'post_id':
                                             PostURLTests.
                                             post.id}))
        cls.group_url = (reverse('posts:group_posts',
                                 kwargs={'slug':
                                         PostURLTests.
                                         group.slug}))

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(PostURLTests.user_2)

    def test_url_exists_at_desired_location(self):
        """Страницы доступны гостям и авторизованным пользователям."""
        url = [
            reverse('posts:index'),
            reverse('posts:group_posts',
                    kwargs={'slug':
                            PostURLTests.group.slug}),
            reverse('posts:profile',
                    kwargs={'username':
                            PostURLTests.user.username}),
            reverse('posts:post_detail',
                    kwargs={'post_id':
                            PostURLTests.post.id}),
        ]
        for url in url:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
        url = [
            reverse('posts:post_edit',
                    kwargs={'post_id':
                            PostURLTests.post.id}),
            reverse('posts:post_create'),
        ]
        for url in url:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_redirect_anonymous(self):
        """Страница /post_id/edit перенаправляет анонимного пользователя."""
        response = self.guest_client.get(reverse('posts:post_edit',
                                                 kwargs={'post_id':
                                                         PostURLTests.
                                                         post.id}))
        redirect_URL = '/auth/login/?next=' + reverse('posts:post_edit',
                                                      kwargs={'post_id':
                                                              PostURLTests.
                                                              post.id})
        self.assertRedirects(response, redirect_URL)

    def test_post_edit_url_redirect_non_author(self):
        """Страница /post_id/edit перенаправляет не автора."""
        response = self.authorized_client_2.get(reverse('posts:post_edit',
                                                        kwargs={'post_id':
                                                                PostURLTests.
                                                                post.id}))
        self.assertRedirects(response, PostURLTests.post_url)

    def test_post_create_url_redirect_anonymous(self):
        """Страница /posts/create/ перенаправляет анонимного пользователя. """
        response = self.guest_client.get(reverse('posts:post_create'),
                                         follow=True)
        redirect_URL = '/auth/login/?next=' + reverse('posts:post_create')
        self.assertRedirects(response, redirect_URL)

    def test_unexisting_page(self):
        """Запрос к странице unixisting_page вернет ошибку 404"""
        response = self.guest_client.get('/unixisting_page/')
        self.assertEqual(response.status_code, 404)

    def test_urls_uses_correct_template(self):
        """Проверяем, что URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            PostURLTests.index_url: 'posts/index.html',
            PostURLTests.group_url: 'posts/group_list.html',
            PostURLTests.post_url: 'posts/post_detail.html',
            PostURLTests.profile_url: 'posts/profile.html',
            PostURLTests.create_url: 'posts/create_post.html',
            PostURLTests.post_edit_url: 'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_url_redirect_authorized_non_author(self):
        """Проверяем переадресацию для авторизованного пользователя,
        не являющегося автором поста на post_detail"""
        response = self.authorized_client_2.get(
            PostURLTests.post_edit_url, follow=True
        )
        self.assertRedirects(response, PostURLTests.post_url)
