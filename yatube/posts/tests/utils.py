from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
import shutil
from django.conf import settings
import tempfile
from ..forms import PostForm
from ..models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class BaseTestPost(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.author_client = Client()
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
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            group=cls.group,
            image=uploaded
        )
        cls.form = PostForm()

    def check_id(self, post_info):
        id = post_info.id
        self.assertEqual(id, self.post.id)

    def check_text(self, post_info):
        text = post_info.text
        self.assertEqual(text, self.post.text)

    def check_group(self, post_info):
        group = post_info.group
        self.assertEqual(group, self.post.group)

    def check_title(self, post_info):
        title = post_info.group.title
        self.assertEqual(title, self.group.title)

    def check_author(self, post_info):
        author = post_info.author.username
        self.assertEqual(author, self.post.author.username)

    def check_edit_post(self, edit_text, post_info):
        self.assertEqual(edit_text, post_info.text)

    def check_image(self, post_info):
        img = post_info.image
        self.assertEqual(
            img if img.file else None,
            self.post.image
        )
