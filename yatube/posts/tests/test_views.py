from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, Follow, Comment
from .utils import BaseTestPost

User = get_user_model()


class PostPagesTest(BaseTestPost):

    def setUp(self):
        self.author_client.force_login(self.author)

    def test_pages_uses_correct_template_all_users(self):
        """URL-адрес использует соответствующий шаблон.(posts)."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:profile', kwargs={'username': self.author}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
            'posts/post_detail.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            'posts/group_list.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
            'posts/post_create.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.author_client.get(reverse('posts:index'))
        post = response.context['page_obj'].object_list[0]
        self.check_id(post)
        self.check_text(post)
        self.check_author(post)
        self.check_group(post)
        self.check_title(post)
        self.check_image(post)

    def test_homepage_uses_the_cache(self):
        """Тест, проверяющий работу кэша на странице index"""
        cache.clear()
        content_before_text = self.author_client.get(
            reverse("posts:index")
        ).content
        cache.clear()
        post = Post.objects.create(text="ылвалыватьдл",
                                        author=self.author,)
        content_after_text = self.author_client.get(
            reverse("posts:index")
        ).content
        post.delete()
        content_cash_text = self.author_client.get(
            reverse("posts:index")
        ).content
        cache.clear()
        content_delete_cash_text = self.author_client.get(
            reverse("posts:index")
        ).content
        self.assertEqual(content_before_text, content_delete_cash_text)
        self.assertEqual(content_after_text, content_cash_text)
        self.assertNotEqual(content_before_text, content_after_text)
        self.assertNotEqual(content_after_text, content_delete_cash_text)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = (self.author_client.get(reverse('posts:group_list',
                    kwargs={'slug': self.group.slug})))
        post = response.context['page_obj'].object_list[0]
        self.check_id(post)
        self.check_text(post)
        self.check_author(post)
        self.check_group(post)
        self.check_title(post)
        self.check_image(post)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = (self.author_client.get(reverse('posts:profile',
                    kwargs={'username': self.post.author})))
        post = response.context['page_obj'].object_list[0]
        self.check_id(post)
        self.check_text(post)
        self.check_author(post)
        self.check_group(post)
        self.check_title(post)
        self.check_image(post)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контестом."""
        post = Post.objects.first()
        self.check_id(post)
        self.check_text(post)
        self.check_author(post)
        self.check_group(post)
        self.check_title(post)
        self.check_image(post)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = (self.author_client.get(reverse('posts:post_create')))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_show_correct_context_in_edit(self):
        """Шаблон post_create сформирован с правильным контекстом
        при редактировании поста."""
        response = (self.author_client.get(reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id})))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertEqual(response.context.get('post_id'), self.post.id)

        self.assertTrue(response.context.get('is_edit'))

    def test_check_post_on_create(self):
        """Проверка, что пост правильно добавляется на страницы."""
        pages = {
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.author}),
        }
        for address in pages:
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertEquals(response.context.get('page_obj')[0],
                                  self.post)

    def test_group(self):
        """Проверка, что пост не попал в группу, для которой
        не был предназначен."""
        fake_group = Group.objects.create(
            title='Тестовый заголовок',
            slug='fake-slug',
            description='Тестовое описание',
        )
        response = self.author_client.get(reverse('posts:group_list',
                                          args=[fake_group.slug]))
        self.assertNotIn(self.post, response.context['page_obj'])


class PaginatorViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание',
        )

        for i in range(13):
            Post.objects.create(
                text=f'Тестовый текст {i}',
                author=cls.user_author,
                group=cls.group,
            )

    def setUp(self):
        self.client = Client()

    def test_first_page_contains_ten_record(self):
        posts_on_pages = {
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user_author})
        }
        for post in posts_on_pages:
            with self.subTest(post=post):
                response = self.client.get(post)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        posts_on_pages = {
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user_author})
        }
        for post in posts_on_pages:
            with self.subTest(post=post):
                response = self.client.get(post + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)


class FollowTests(TestCase):
    def setUp(self):
        self.client_auth_follower = Client()
        self.client_auth_following = Client()
        self.user_follower = User.objects.create_user(username='follower')
        self.user_following = User.objects.create_user(username='following')
        self.post = Post.objects.create(
            author=self.user_following,
            text='Тестовый текст'
        )
        self.client_auth_follower.force_login(self.user_follower)
        self.client_auth_following.force_login(self.user_following)

    def test_follow(self):
        self.client_auth_follower.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user_following.username})
        )
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_unfollow(self):
        self.client_auth_follower.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user_following.username})
        )
        self.client_auth_follower.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.user_following.username})
        )
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_subscription_feed(self):
        """Запись постится в ленте избранных"""
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)
        response = self.client_auth_follower.get('/follow/')
        post_text_0 = response.context['page_obj'][0].text
        self.assertEqual(post_text_0, self.post.text)
        response = self.client_auth_following.get('/follow/')
        self.assertNotContains(response, self.post.text)

    def test_authorized_can_write_comment(self):
        """Авторизованный пользователь может jcnfdbnm комментарий"""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'вОЛга',
        }
        response = self.client_auth_follower.post(
            reverse((
                'posts:add_comment'), kwargs={'post_id': f'{self.post.id}'}),
            data=form_data,
            follow=True
        )
        get_comment = response.context['comments'][0].text
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(get_comment, form_data['text'])
