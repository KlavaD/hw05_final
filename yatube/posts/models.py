from core.models import CreatedModel, User
from django.db import models


class Group(models.Model):
    title = models.CharField("Название группы", max_length=200)
    slug = models.SlugField("Путь", unique=True)
    description = models.TextField("Описание группы")

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

    def __str__(self) -> str:
        return self.title


class Post(CreatedModel):
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name="Группа",
        help_text='Группа, к которой будет относиться пост'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta(CreatedModel.Meta):
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'
        default_related_name = 'posts'


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Комментируемы пост",
        help_text='Введите комментарий'
    )

    class Meta(CreatedModel.Meta):
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        default_related_name = 'comments'


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name="Подписчик"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name="Автор постов"
    )

    class Meta:
        verbose_name = 'Подписчик'
        verbose_name_plural = 'Подписчики'

    def __str__(self) -> str:
        return str(f'{self.user} подписан на {self.author}')
