from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from posts.models import Group, Post

User = get_user_model()


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.authorized_author_client = Client()
        cls.user = User.objects.create_user(username='PUTIn')
        cls.authorized_client = Client()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.author,
            group=cls.group,
        )

    def setUp(self):
        self.authorized_author_client.force_login(self.author)
        self.authorized_client.force_login(self.user)

    def test_post_edit_page_with_author(self):
        """Страница /posts/<post_id>/edit доступна только автору"""
        response = self.authorized_author_client.get(
            f'/posts/{self.post.pk}/edit/',
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий
                        шаблон для общедоступных страниц."""
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': f'/group/{self.group.slug}/',
            'posts/profile.html': f'/profile/{self.author.username}/',
            'posts/post_detail.html': f'/posts/{self.post.pk}/'
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_refers_to_correct_template_for_authorized(self):
        """URL-адрес использует соответсвующий
                шаблон для авторизованного пользователя"""
        templates_url_names = {
            '/create/': 'posts/post_create.html',
            f'/posts/{self.post.pk}/edit/': 'posts/post_create.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_author_client.get(address)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_redirect_guest(self):
        """Проверка редиректа гостя при
                        попытке зайти на приватную страницу"""
        templates_url_names = {
            '/create/': '/auth/login/?next=/create/',
            '/posts/1/edit/': f'/auth/login/?next=/posts/{self.post.pk}/edit/'
        }
        for url, url_redirect in templates_url_names.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, url_redirect)

    def test_url_redirect_authorized_edit(self):
        """Проверка редиректа при попытке редактировать чужой пост"""
        response = self.authorized_client.get(f'/posts/{self.post.pk}/edit/')
        self.assertRedirects(response, f'/posts/{self.post.pk}/')
