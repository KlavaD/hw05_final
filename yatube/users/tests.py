from django.test import TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Post, Group, User


class PostCreateFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='Test_author')
        cls.group = Group.objects.create(
            title='тестовая группа',
            slug='test_group'
        )
        cls.post = Post.objects.create(
            text='Содержание поста',
            author=PostCreateFormTest.author,
            group=PostCreateFormTest.group
        )
        cls.form = PostForm()

    def test_create_user(self):
        # Подсчитаем количество записей в User
        users_count = User.objects.count()
        form_data = {
            'first_name': 'user1',
            'last_name': 'last_user1',
            'username': 'test_user',
            'email': 'user@test.py',
            'password1': '123qwe321',
            'password2': '123qwe321',
        }
        self.client.post(
            reverse('users:signup'),
            data=form_data
        )
        # Проверяем, увеличилось ли число users
        self.assertEqual(User.objects.count(), users_count + 1)
