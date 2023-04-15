from django import forms
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User

NUMBER_OF_POSTS = 13
NUMBER_OF_POSTS_ON_FIRST_PAGE = 10
NUMBER_OF_POSTS_ON_SECOND_PAGE = 3


class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='StasBasov')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
        )
        cls.new_group = Group.objects.create(
            title='Новая граппа',
            slug='new_slug',
            description='Новое описание',
        )

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_posts',
                    kwargs={'slug': 'test-slug'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': 'StasBasov'}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id':
                            self.post.id}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit',
                    kwargs={'post_id':
                            self.post.id}): 'posts/create_post.html'}

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""

        response = self.authorized_client.get(reverse('posts:index'))
        page_obj = response.context['page_obj'][0]

        self.assertEqual(page_obj, self.post)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""

        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': 'test-slug'}))
        group = response.context['group']
        page_obj = response.context['page_obj'][0]

        self.assertEqual(page_obj, self.post)
        self.assertEqual(group, self.group)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""

        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'StasBasov'}))
        author = response.context['author']
        page_obj = response.context['page_obj'][0]

        self.assertEqual(page_obj, self.post)
        self.assertEqual(author, self.post.author)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""

        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        post = response.context['post']

        self.assertEqual(post, self.post)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""

        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField, }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

        self.assertIn('is_edit', response.context)
        self.assertFalse(response.context['is_edit'])

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""

        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField, }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

        self.assertIn('is_edit', response.context)
        self.assertTrue(response.context['is_edit'])

    def test_new_post(self):
        """Новый пост появляется на трёх страницах."""

        pages = (
            reverse('posts:index'),
            reverse('posts:profile', kwargs={'username': self.user.username}),
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}),)

        for page in pages:
            response = self.authorized_client.get(page)
            page_obj = response.context['page_obj']

            self.assertIn(self.post, page_obj)

    def test_new_post_not_on_other_group_page(self):
        """Новый пост не попал на страницу другой группы."""

        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': self.new_group.slug}))

        page_obj = response.context['page_obj']

        self.assertNotIn(self.post, page_obj)


class PaginatorViewsTest(TestCase):
    """Паджинатор работает на всех страницах."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='StasBasov')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
        )

        posts = []
        for _ in range(1, NUMBER_OF_POSTS):
            posts.append(Post(
                text='Один из множества постов',
                author=cls.user,
                group=cls.group,
            ))

        Post.objects.bulk_create(posts)

    def test_paginator_on_three_pages(self):
        group_page = '/group/test-slug/'
        profile_page = '/profile/StasBasov/'
        main_page = '/'
        second_page = '?page=2'

        page_expected_posts = {
            group_page: NUMBER_OF_POSTS_ON_FIRST_PAGE,
            profile_page: NUMBER_OF_POSTS_ON_FIRST_PAGE,
            main_page: NUMBER_OF_POSTS_ON_FIRST_PAGE,
            group_page + second_page: NUMBER_OF_POSTS_ON_SECOND_PAGE,
            profile_page + second_page: NUMBER_OF_POSTS_ON_SECOND_PAGE,
            main_page + second_page: NUMBER_OF_POSTS_ON_SECOND_PAGE,
        }

        for address, expected_number_of_posts in page_expected_posts.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                total_posts_on_page = len(response.context['page_obj'])

                self.assertEqual(
                    total_posts_on_page,
                    expected_number_of_posts
                )
