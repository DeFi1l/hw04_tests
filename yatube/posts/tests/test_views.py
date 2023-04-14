import math

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()


class PostPageTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовая группа в которой будет один пост',
        )
        cls.new_group = Group.objects.create(
            title='Новая тестовая группа',
            slug='new-group',
            description='Тестовая группа в которой не будет постов',
        )
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPageTests.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}): (
                'posts/group_list.html'
            ),
            reverse('posts:profile', kwargs={'username': 'auth'}): (
                'posts/profile.html'
            ),
            reverse('posts:post_detail', kwargs={'post_id': 1}): (
                'posts/post_detail.html'
            ),
            reverse('posts:post_edit', kwargs={'post_id': 1}): (
                'posts/create_post.html'
            ),
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_posts_pages_has_one_post(self):
        """Шаблоны страниц отображают правильное количество постов"""
        pages_reverse_name = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'auth'}),
        )
        for reverse_name in pages_reverse_name:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), 1)

    def test_new_group_posts_has_no_post(self):
        """Шаблон страницы новой группы не имеет постов"""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'new-group'})
        )
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_posts_pages_show_correct_context(self):
        """Шаблоны страниц с постами сформированы с правильным контекстом."""
        pages_reverse_name = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'auth'}),
            reverse('posts:post_detail', kwargs={'post_id': 1}),
        )
        for reverse_name in pages_reverse_name:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                if 'post' in response.context:
                    first_object = response.context['post']
                else:
                    first_object = response.context['page_obj'][0]
                post_text_0 = first_object.text
                self.assertEqual(post_text_0, 'Тестовый пост')

    def test_posts_forms_show_correct_context(self):
        """Шаблоны страниц с формами сформированы с правильным контекстом."""
        pages_reverse_name = (
            reverse('posts:post_edit', kwargs={'post_id': 1}),
            reverse('posts:post_create'),
        )
        for reverse_name in pages_reverse_name:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                form_fields = {
                    'text': forms.fields.CharField,
                    'group': forms.fields.ChoiceField,
                }
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get('form').fields.get(
                            value
                        )
                        self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.user = User.objects.create_user(username='auth')
        cls.TEST_POSTS_COUNT = 11
        cls.paginator_reverse_name = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'auth'}),
        )
        cls.objs = [
            Post.objects.create(
                author=cls.user,
                text='Тестовый пост',
                group=cls.group,
            )
            for _ in range(cls.TEST_POSTS_COUNT)
        ]
        Post.objects.bulk_create(objs=cls.objs, ignore_conflicts=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)

    def test_first_page_contains_correct_records(self):
        """Первая страница отображает корректное количество постов"""
        paginator_reverse_name = PaginatorViewsTest.paginator_reverse_name
        for reverse_name in paginator_reverse_name:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']),
                    settings.POSTS_PER_PAGE,
                )

    def test_last_page_contains_correct_records(self):
        """Последняя страница отображает корректное количество постов"""
        paginator_reverse_name = PaginatorViewsTest.paginator_reverse_name
        last_page_number = math.ceil(
            PaginatorViewsTest.TEST_POSTS_COUNT
            / settings.POSTS_PER_PAGE
        )
        last_page_posts_count = (
            PaginatorViewsTest.TEST_POSTS_COUNT
            % settings.POSTS_PER_PAGE
            or settings.POSTS_PER_PAGE
        )
        for reverse_name in paginator_reverse_name:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(
                    reverse_name + f'?page={last_page_number}'
                )
                self.assertEqual(
                    len(response.context['page_obj']), last_page_posts_count
                )
