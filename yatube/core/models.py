from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class CreatedModel(models.Model):
    """Абстрактная модель. Добавляет дату создания."""
    pub_date = models.DateTimeField(
        'Дата создания',
        auto_now_add=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор"
    )
    text = models.TextField(
        'Текст',
        max_length=400,
        help_text='Введите текст'
    )

    class Meta:
        # Это абстрактная модель:
        abstract = True
        ordering = ('-pub_date',)

    def __str__(self) -> str:
        return self.text[:15]
