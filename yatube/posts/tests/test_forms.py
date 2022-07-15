from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from ..models import Comment, Post
from .utils import BaseTestPost

User = get_user_model()


class PostFormTests(BaseTestPost):

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_Auth_user_can_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
            'image': b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile',
                    kwargs={'username': f'{self.author.username}'})
        )
        post = Post.objects.first()
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.check_text(post)
        self.check_title(post)
        self.check_author(post)

    def test_cant_create_post_without_text(self):
        """Нельзя создать пост с пустым текстом"""
        posts_count = Post.objects.count()
        form_data = {
            'text': ''
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_dont_create_new_post(self):
        """Валидная форма редактирует запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый отредактированный текст',
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse(('posts:post_edit'),
                    kwargs={'post_id': f'{self.post.id}'}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(('posts:post_detail'),
                              kwargs={'post_id': f'{self.post.id}'})
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.check_edit_post(form_data.get('text'), Post.objects.first())
        self.check_title(Post.objects.first())
        self.check_author(Post.objects.first())

    def test_cant_edit_post_without_text(self):
        """Нельзя отредактировать пост, оставив пустой текст"""
        posts_count = Post.objects.count()
        form_data = {
            'text': ''
        }
        response = self.authorized_client.post(
            reverse(('posts:post_edit'),
                    kwargs={'post_id': f'{self.post.id}'}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_text_label(self):
        title_label = self.form.fields['text'].label
        self.assertEquals(title_label, 'Текст поста')

    def test_group_label(self):
        title_label = self.form.fields['group'].label
        self.assertEquals(title_label, 'Группа')

    def test_comment_show_up(self):
        """После успешной отправки, комментарий появляется на странице поста"""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Новый комментарий для поста',
        }
        response = self.authorized_client.post(
            reverse((
                'posts:add_comment'), kwargs={'post_id': f'{self.post.id}'}),
            data=form_data,
            follow=True
        )
        response_guest = self.client.post(
            reverse((
                'posts:add_comment'), kwargs={'post_id': f'{self.post.id}'}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse((
            'posts:post_detail'), kwargs={'post_id': f'{self.post.id}'}))
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertRedirects(response_guest,
                             '/auth/login/?next=/posts/1/comment/')
