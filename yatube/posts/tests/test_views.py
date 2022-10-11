import shutil
import tempfile

from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache


from posts.forms import PostForm
from ..models import Post, Group, User, Comment, Follow

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='Test_author')
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
        cls.group = Group.objects.create(
            title='тестовая группа',
            slug='test_group'
        )
        cls.post = Post.objects.create(
            text='Содержание поста',
            author=cls.author,
            group=cls.group,
            image=uploaded
        )
        cls.comment = Comment.objects.create(
            text='Комментарий',
            post=cls.post,
            author=cls.author
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.authorized_author = Client()
        self.authorized_author.force_login(PostPagesTests.author)
        self.user = User.objects.create_user(username='TestUser')
        self.not_author = Client()
        self.not_author.force_login(self.user)

    def correct_context(self, response, flag=False):
        if not flag:
            first_object = response.context['page_obj'][0]
        else:
            first_object = response.context['post']
        task_text_0 = first_object.text
        task_author_0 = first_object.author.username
        task_date_0 = first_object.pub_date
        task_group_0 = first_object.group.title
        task_image_0 = first_object.image
        self.assertEqual(task_text_0, self.post.text)
        self.assertEqual(task_author_0, self.post.author.username)
        self.assertEqual(task_date_0, self.post.pub_date)
        self.assertEqual(task_group_0, self.post.group.title)
        self.assertEqual(str(task_image_0), 'posts/small.gif')

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        posts_count = Post.objects.count()
        if posts_count == 1:
            response = self.authorized_author.get(reverse('posts:index'))
            self.correct_context(response)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        posts_count = Post.objects.count()
        if posts_count == 1:
            response = self.authorized_author.get(
                reverse('posts:group_list', args=(self.group.slug,))
            )
            self.correct_context(response)
            self.assertEqual(
                response.context['group'],
                self.post.group
            )

    def test_profile_show_correct_context(self):
        """Шаблон profile, сформирован с правильным контекстом."""
        posts_count = Post.objects.count()
        if posts_count == 1:
            response = self.authorized_author.get(
                reverse('posts:profile', args=(self.post.author,))
            )
            self.correct_context(response)
            self.assertEqual(
                response.context['author'],
                self.author
            )

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        posts_count = Post.objects.count()
        if posts_count == 1:
            response = self.authorized_author.get(
                reverse('posts:post_detail', args=(self.post.pk,))
            )
            self.correct_context(response, flag=True)

    def test_post_create_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        reverse_names = (
            reverse('posts:post_create'),
            reverse('posts:post_edit', args=(self.post.pk,))
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context.get('form'), PostForm)
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get(
                            'form'
                        ).fields.get(value)
                        self.assertIsInstance(form_field, expected)

    def test_post_create(self):
        """Проверка, что пост не попал в группу,
        в которой его не должно быть"""

        group = Group.objects.create(
            title='неправильная группа',
            slug='not_right_group'
        )
        response = self.authorized_author.get(
            reverse('posts:group_list', args=(group.slug,))
        )
        self.assertFalse(len(response.context['page_obj']))
        new_post = get_object_or_404(Post, id=self.post.pk)
        self.assertIsNotNone(new_post.group.pk)
        response = self.authorized_author.get(
            reverse('posts:group_list', args=(self.group.slug,))
        )
        self.assertTrue(len(response.context['page_obj']))

    def test_add_comment(self):
        """Проверка, что комментарий появляется на странице поста."""
        Comment.objects.all().delete()
        comment_form = {
            'text': 'Новый комментарий',
        }
        self.authorized_author.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data=comment_form
        )
        self.assertEqual(Comment.objects.count(), 1)
        response = self.authorized_author.get(
            reverse('posts:post_detail', args=(self.post.pk,))
        )
        comment = response.context['comments'][0]
        self.assertEqual(comment.text, comment_form['text'])

    def test_index_cache(self):
        """Тестируем кэш index."""
        response1 = self.authorized_author.get(reverse('posts:index'))
        Post.objects.create(
            text='Testing cache',
            author=self.author,
            group=self.group
        )
        response2 = self.authorized_author.get(reverse('posts:index'))
        self.assertEqual(response1.content, response2.content)
        cache.clear()
        response3 = self.authorized_author.get(reverse('posts:index'))
        self.assertNotEqual(response3.content, response2.content)

    def test_follower_can_subscribe(self):
        """ Проверка: авторизованный пользователь
        может подписаться на автора, и только один раз"""
        Follow.objects.all().delete()
        self.not_author.get(
            reverse('posts:profile_follow', args=(self.author,))
        )
        count_followers = Follow.objects.count()
        self.assertEqual(count_followers, 1)
        follower = get_object_or_404(Follow, author=self.author)
        self.assertEqual(follower.user, self.user)
        self.not_author.get(
            reverse('posts:profile_follow', args=(self.author,))
        )
        count_followers = Follow.objects.count()
        self.assertEqual(count_followers, 1)

    def test_follower_can_unsubscribe(self):
        """ Проверка: авторизованный пользователь может отписаться от автора"""
        Follow.objects.create(
            user=self.user,
            author=self.author
        )
        self.not_author.get(
            reverse('posts:profile_unfollow', args=(self.author,))
        )
        count_followers = Follow.objects.count()
        self.assertEqual(count_followers, 0)

    def test_new_post_follow_unfollow(self):
        """ Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех,
        кто не подписан."""
        Follow.objects.create(
            user=self.user,
            author=self.author
        )
        Post.objects.all().delete()
        new_post = Post.objects.create(
            text='new_post',
            group=self.group,
            author=self.author
        )
        self.new_user = User.objects.create_user(username='Not_follower')
        self.not_follower = Client()
        self.not_follower.force_login(self.new_user)
        response_follower = self.not_author.get(
            reverse('posts:follow_index')
        )
        response_unfollower = self.not_follower.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(new_post, response_follower.context['page_obj'][0])
        self.assertFalse(len(response_unfollower.context['page_obj']))


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.posts = []
        cls.author = User.objects.create(username='Test_author_for_paginator')
        cls.group = Group.objects.create(
            title='тестовая группа',
            slug='test_group'
        )
        cls.posts_counts = 15
        post = [
            Post(
                text=f'Test{count}',
                author=cls.author,
                group=cls.group
            )
            for count in range(cls.posts_counts)
        ]
        cls.posts = Post.objects.bulk_create(post)

    def test_first_page_contains_ten_records(self):
        """ Проверка: количество постов на каждой странице"""
        reverse_names = (
            ('posts:index', None),
            ('posts:group_list', (self.group.slug,)),
            ('posts:profile', (self.author,))
        )
        count_posts_on_pages = (
            ('?page=1', settings.COUNT_POSTS),
            ('?page=2', self.posts_counts - settings.COUNT_POSTS)
        )
        for name, args in reverse_names:
            with self.subTest(name=name):
                for page, count in count_posts_on_pages:
                    with self.subTest(count=count):
                        response = self.client.get(
                            reverse(name, args=args) + page
                        )
                        self.assertEqual(
                            len(response.context['page_obj']), count
                        )
