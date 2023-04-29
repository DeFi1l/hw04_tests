import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, Comment, Follow, User


User = get_user_model()

POST_N: int = 13
POST_1: int = 10
POST_2: int = 3

settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=settings.MEDIA_ROOT)
class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='auth1')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=Group.objects.get(slug='test_slug'),
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_url_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_urls = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}):
            'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}):
            'posts/post_create.html',
        }
        for reverse_name, template in templates_urls.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_detail_correct_context(self):
        """post_detail с правильным контекстом."""
        postid = self.post.pk
        response = self.client.get(reverse('posts:post_detail', args=[postid]))
        post = response.context['post']
        post_image_0 = Post.objects.first().image
        self.assertEqual(post.pk, postid)
        self.assertEqual(post_image_0, 'posts/small.gif')

    def test_create_post_edit_correct_context(self):
        """create_post(edit) с правильным контекстом."""
        post_id = self.post.pk
        response = self.authorized_client.get(reverse('posts:post_edit',
                                              args=[post_id]))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_create_post_correct_context(self):
        """create_post с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_correct_context(self):
        """index, group_list, profile с правильным контекстом."""
        urls = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user}),
        ]
        for template in urls:
            with self.subTest(template=template):
                response = self.client.get(template)
                first_object = response.context['page_obj'][0]
                task_author_0 = first_object.author.username
                task_group_0 = first_object.group.title
                task_text_0 = first_object.text
                post_image_0 = Post.objects.first().image
                self.assertEqual(task_author_0, self.user.username)
                self.assertEqual(task_group_0, self.group.title)
                self.assertEqual(task_text_0, self.post.text)
                self.assertEqual(post_image_0, 'posts/small.gif')

    def test_post_another_group(self):
        """Пост не попал в группу, для которой не был предназначен."""
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        self.assertTrue(post_text_0, self.post.text)

    def test_post_in_index_group_profile(self):
        """Пост на главной, в группе, в профиле."""
        reverse_url_post = {
            reverse('posts:index'): self.group.slug,
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            self.group.slug,
            reverse('posts:profile', kwargs={'username': self.user}):
            self.group.slug
        }
        for value, expected in reverse_url_post.items():
            response = self.authorized_client.get(value)
            for object in response.context['page_obj']:
                post_group = object.group.slug
                with self.subTest(value=value):
                    self.assertEqual(post_group, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth2',
                                            email='auth2@yandex.ru',
                                            password='11111',)
        cls.group = Group.objects.create(
            title=('Тестовая группа'),
            slug='test_slug',
            description='Тестовое описание')
        cls.posts_list = [
            Post(
                author=cls.user,
                text=f'Текст {i}',
                group=cls.group
            )
            for i in range(POST_N)
        ]
        Post.objects.bulk_create(cls.posts_list)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_first_page_has_ten_posts(self):
        """Количество постов на первой странице равно 10."""
        urls = {
            reverse('posts:index'): 'index',
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): 'group',
            reverse('posts:profile',
                    kwargs={'username': self.user}): 'profile',
        }
        for url in urls.keys():
            response = self.client.get(url)
            self.assertEqual(len(
                response.context.get('page_obj').object_list),
                POST_1)

    def test_second_page_has_three_posts(self):
        """На второй странице должно быть три поста."""
        urls = {
            reverse('posts:index') + '?page=2': 'index',
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}) + '?page=2':
            'group',
            reverse('posts:profile',
                    kwargs={'username': self.user}) + '?page=2':
            'profile',
        }
        for url in urls.keys():
            response = self.client.get(url)
            self.assertEqual(len(
                response.context.get('page_obj').object_list),
                POST_2)


class CommentTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth3')
        cls.post = Post.objects.create(
            text='текст',
            author=cls.user,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='коммент',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_comment_yes(self):
        """После отправки коммент появляется."""
        names_pages = [
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}),
        ]
        for address in names_pages:
            response = self.authorized_client.get(address)
            form_obj = response.context.get('comments')[0]
            self.assertEqual(form_obj.text, self.comment.text)

    def test_authorized_can_comment(self):
        """Авторизованный пользователь может комментировать посты."""
        form_data = {
            'text': 'коммент',
            'author': self.user,
            'post': self.post,
        }
        current_comments_count = Comment.objects.count()
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={
                'post_id': self.post.id
            }),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            )
        )
        self.assertEqual(
            Comment.objects.count(),
            current_comments_count + 1
        )
        self.assertTrue(
            Comment.objects.filter(
                text=form_data['text'],
                author=self.post.author,
                post=self.post,
            ).exists()
        )

    def test_post_cannot_comments_anonymous(self):
        """Неавторизованный пользователь не может комментировать посты."""
        form_data = {
            'text': 'коммент2',
            'author': self.user,
            'post': self.post,
        }
        current_comments_count = Comment.objects.count()
        self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}
            ),
            data=form_data,
            follow=True
        )
        self.assertNotEqual(
            Comment.objects.count(),
            current_comments_count + 1
        )
        self.assertFalse(
            Comment.objects.filter(
                text=form_data['text'],
                author=self.user,
                post=self.post,
            ).exists()
        )


class CacheTest(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='auth4')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_main_page(self):
        """Проверка работы кеша."""
        post = Post.objects.create(
            author=self.user,
            text='Тест',
        )
        response = self.guest_client.get(reverse('posts:index'))
        content_1 = response.content
        post.delete()
        response = self.guest_client.get(reverse('posts:index'))
        content_2 = response.content
        self.assertEqual(content_1, content_2)
        cache.clear()
        response = self.guest_client.get(reverse('posts:index'))
        content_3 = response.content
        self.assertNotEqual(content_1, content_3)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Author')
        cls.follower = User.objects.create_user(username='Follower')
        cls.not_follower = User.objects.create_user(username='Not_Follower')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
        )
        cls.post = Post.objects.create(
            text='Тестовый текст2',
            author=cls.author,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.follower_client = Client()
        self.not_follower_client = Client()
        self.authorized_client.force_login(self.author)
        self.follower_client.force_login(self.follower)
        self.not_follower_client.force_login(self.not_follower)

    def test_authorized_can_follow_unfollow(self):
        """Можно подписываться на других и удалять их из подписок."""
        self.follower_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.post.author}
            )
        )
        self.assertTrue(
            Follow.objects.filter(
                author=self.post.author,
                user=self.follower
            ).exists()
        )
        self.follower_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.post.author}
            )
        )
        self.assertFalse(
            Follow.objects.filter(
                author=self.post.author,
                user=self.follower
            ).exists()
        )

    def test_only_follower_sees_new_post(self):
        """Новая запись у тех, кто подписан, и нет у тех, кто не подписан."""
        self.follower_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.post.author}
            )
        )
        response_1 = self.follower_client.get(reverse('posts:follow_index'))
        response_2 = self.not_follower_client.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(response_1.context['page_obj']
                         .paginator.page(1)
                         .object_list.count(), 2)
        self.assertEqual(response_2.context['page_obj']
                         .paginator.page(1)
                         .object_list.count(), 0)
