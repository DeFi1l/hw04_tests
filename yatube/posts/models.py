from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        verbose_name='Группа',
        help_text='Выберите группу для поста',
        max_length=200
    )
    slug = models.SlugField(
        verbose_name='Слаг группы',
        unique=True
    )
    description = models.TextField(
        verbose_name='Описание группы',
        help_text='Введите описание группы'
    )

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        verbose_name='Пост',
        help_text='Введите текст поста',
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата',
        auto_now_add=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Группа',
        help_text='Выберите группу',
    )

    class Meta:
        ordering = ('-pub_date',)

    def __str__(self):
        return self.text[:15]
