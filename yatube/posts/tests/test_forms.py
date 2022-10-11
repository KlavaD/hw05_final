from http import HTTPStatus
import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.forms import PostForm, CommentForm
from posts.models import Post, Group, User, Comment


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_post = User.objects.create(username='Test_author')
        cls.group = Group.objects.create(
            title='тестовая группа',
            slug='test_group'
        )
        cls.post = Post.objects.create(
            text='Содержание поста',
            author=cls.author_post,
            group=cls.group
        )
        cls.comment = Comment.objects.create(
            text='Комментарий',
            post=cls.post,
            author=cls.author_post
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.author = Client()
        self.author.force_login(self.author_post)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        # Удалим все записи в Post
        Post.objects.all().delete()
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
        form_data = {
            'text': 'Пост для проверки создания',
            'group': self.group.pk,
            'image': uploaded,
        }
        # Отправляем POST-запрос
        response = self.author.post(
            reverse('posts:post_create'),
            data=form_data,
        )
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), 1)
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse(
            'posts:profile', args=(self.post.author.username,)
        ))
        new_post = Post.objects.first()
        self.assertEqual(new_post.author, self.author_post)
        self.assertEqual(new_post.text, form_data['text'])
        self.assertEqual(new_post.group.pk, form_data['group'])
        self.assertEqual(new_post.image, 'posts/small.gif')

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        # Подсчитаем количество записей в Post
        self.assertEqual(Post.objects.count(), 1)
        old_author = self.post.author
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
        another_group = Group.objects.create(
            title='другая тестовая группа',
            slug='another_test_group'
        )
        form_data = {
            'text': 'Пост для проверки создания',
            'group': another_group.pk,
            'image': uploaded,
        }
        # Отправляем POST-запрос
        response = self.author.post(
            reverse('posts:post_edit', args=(self.post.id,)),
            data=form_data,
            follow=False
        )
        # Проверяем, не создался ли новый пост
        self.assertEqual(Post.objects.count(), 1)
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse(
            'posts:post_detail', args=(self.post.pk,)
        ))
        post = Post.objects.first()
        self.assertEqual(post.author, old_author)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        response = self.client.post(
            reverse('posts:group_list', args=(self.group.slug,))
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(len(response.context['page_obj']))

    def test_guest_create_post(self):
        # Проверяем, может ли гость создать пост
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Пост для проверки создания',
            'group': self.group.pk,
        }
        # Отправляем POST-запрос
        self.client.post(
            reverse('posts:post_create'),
            data=form_data
        )
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count)

    def test_create_comment(self):
        form_fields = {
            'text': forms.fields.CharField,
        }
        response = self.author.get(
            reverse('posts:post_detail', args=(self.post.pk,))
        )
        self.assertIsInstance(response.context.get('form'), CommentForm)
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get(
                    'form'
                ).fields.get(value)
                self.assertIsInstance(form_field, expected)
            comments_count = Comment.objects.count()
            if comments_count == 1:
                comment = response.context['comments'][0]
                self.assertEqual(comment, self.comment)
