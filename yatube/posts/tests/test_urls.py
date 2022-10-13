from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache

from posts.models import Post, Group, User


class PostURLTests(TestCase):
    REDIRECT_WAY = '/auth/login/?next='

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
            author=PostURLTests.author_post,
            group=PostURLTests.group
        )

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='TestUser')
        self.not_author = Client()
        self.not_author.force_login(self.user)
        self.author = Client()
        self.author.force_login(PostURLTests.author_post)
        self.reverse_names = (
            ('posts:index', None, '/'),
            (
                'posts:group_list',
                (self.group.slug,),
                f'/group/{self.group.slug}/'
            ),
            (
                'posts:profile',
                (self.post.author.username,),
                f'/profile/{self.post.author.username}/'
            ),
            (
                'posts:post_detail',
                (self.post.pk,),
                f'/posts/{self.post.pk}/'
            ),
            ('posts:post_create', None, '/create/'),
            (
                'posts:post_edit',
                (self.post.pk,),
                f'/posts/{self.post.pk}/edit/'
            ),
            (
                'posts:add_comment',
                (self.post.pk,),
                f'/posts/{self.post.pk}/comment/'
            ),
            (
                'posts:follow_index',
                None,
                '/follow/'
            ),
            (
                'posts:profile_follow',
                (self.post.author.username,),
                f'/profile/{self.post.author.username}/follow/'
            ),
            (
                'posts:profile_unfollow',
                (self.post.author.username,),
                f'/profile/{self.post.author.username}/unfollow/'
            ),
        )

    def test_reverse_name_url(self):
        """Тест реверсов."""
        for name, args, hardurl in self.reverse_names:
            with self.subTest(name=name):
                self.assertEqual(reverse(name, args=args), hardurl)

    def test_unexisting_urls(self):
        """Проверяем запрос к несуществующей странице 404 и шаблон"""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_urls_uses_correct_template_guest(self):
        """URL-адрес использует соответствующий шаблон. """
        cache.clear()
        url_names = (
            ('posts:index', None, 'posts/index.html'),
            ('posts:follow_index', None, 'posts/follow.html'),
            (
                'posts:group_list',
                (self.group.slug,),
                'posts/group_list.html'
            ),
            (
                'posts:profile',
                (self.post.author.username,),
                'posts/profile.html'
            ),
            (
                'posts:post_detail',
                (self.post.pk,),
                'posts/post_detail.html'
            ),
            ('posts:post_create', None, 'posts/post_create.html'),
            (
                'posts:post_edit',
                (self.post.pk,),
                'posts/post_create.html'
            ),
        )
        for name, args, template in url_names:
            with self.subTest(name=name):
                response = self.author.get(reverse(name, args=args))
                self.assertTemplateUsed(response, template)

    def test_urls_author(self):
        """Проверяем доступность страниц для автора"""
        for name, args, url in self.reverse_names:
            with self.subTest(name=name):
                response = self.author.get(reverse(name, args=args))
                if name == 'posts:add_comment':
                    self.assertRedirects(response, reverse(
                        'posts:post_detail', args=(self.post.pk,)
                    ))
                elif name == 'posts:profile_follow':
                    self.assertRedirects(response, reverse(
                        'posts:profile', args=(self.post.author.username,)
                    ))
                elif name == 'posts:profile_unfollow':
                    self.assertEqual(
                        response.status_code, HTTPStatus.NOT_FOUND
                    )
                else:
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_not_author(self):
        """Проверяем доступность страниц для неавтора"""
        for name, args, x in self.reverse_names:
            with self.subTest(name=name):
                response = self.not_author.get(reverse(name, args=args))
                if name in ('posts:post_edit', 'posts:add_comment'):
                    self.assertRedirects(response, reverse(
                        'posts:post_detail', args=(self.post.pk,)
                    ))
                elif name in (
                    'posts:profile_follow',
                    'posts:profile_unfollow'
                ):
                    self.assertRedirects(response, reverse(
                        'posts:profile', args=(self.post.author.username,)
                    ))
                else:
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_guest(self):
        """Проверяем доступность страниц для гостя"""
        for_redirect = (
            'posts:post_edit',
            'posts:post_create',
            'posts:add_comment',
            'posts:profile_follow',
            'posts:profile_unfollow',
            'posts:follow_index',
        )
        for name, args, url in self.reverse_names:
            with self.subTest(name=name):
                response = self.client.get(reverse(name, args=args))
                if name in for_redirect:
                    self.assertRedirects(
                        response,
                        self.REDIRECT_WAY + reverse(name, args=args)
                    )
                else:
                    self.assertEqual(response.status_code, HTTPStatus.OK)
