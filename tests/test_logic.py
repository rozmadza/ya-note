from http import HTTPStatus

from pytils.translit import slugify

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import WARNING
from notes.models import Note


User = get_user_model()


class TestLogic(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.not_author = User.objects.create(username='Не автор')

        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.not_author_client = Client()
        cls.not_author_client.force_login(cls.not_author)

        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=cls.author,
        )

        cls.form_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': 'new-slug',
        }

    def test_auth_user_can_create_note(self):
        """Авторизованный пользователь может создать заметку."""
        response = self.author_client.post(
            reverse('notes:add'),
            data=self.form_data,
        )

        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 2)

        new_note = Note.objects.get(slug='new-slug')
        self.assertEqual(new_note.title, self.form_data['title'])
        self.assertEqual(new_note.text, self.form_data['text'])
        self.assertEqual(new_note.author, self.author)

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создать заметку."""
        url = reverse('notes:add')
        response = self.client.post(url, data=self.form_data)

        login_url = reverse('users:login')
        expected = f'{login_url}?next={url}'
        self.assertRedirects(response, expected)

        self.assertEqual(Note.objects.count(), 1)

    def test_unique_slug(self):
        """Нельзя создать две заметки с одинаковым slug."""
        data = self.form_data.copy()
        data['slug'] = self.note.slug

        response = self.author_client.post(
            reverse('notes:add'),
            data=data,
        )

        form = response.context['form']

        self.assertFormError(
            form,
            'slug',
            self.note.slug + WARNING,
        )
        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug(self):
        """Slug формируется автоматически."""
        data = self.form_data.copy()
        data.pop('slug')

        response = self.author_client.post(
            reverse('notes:add'),
            data=data,
        )

        self.assertRedirects(response, reverse('notes:success'))

        created_note = Note.objects.get(title=data['title'])
        self.assertEqual(
            created_note.slug,
            slugify(data['title']),
        )

    def test_author_can_edit_note(self):
        """Автор может редактировать свою заметку."""
        response = self.author_client.post(
            reverse('notes:edit', args=(self.note.slug,)),
            data=self.form_data,
        )

        self.assertRedirects(response, reverse('notes:success'))

        self.note.refresh_from_db()

        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.slug, self.form_data['slug'])

    def test_other_user_cant_edit_note(self):
        """Другой пользователь не может изменить заметку."""
        response = self.not_author_client.post(
            reverse('notes:edit', args=(self.note.slug,)),
            data=self.form_data,
        )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        note = Note.objects.get(pk=self.note.pk)

        self.assertEqual(note.title, self.note.title)
        self.assertEqual(note.text, self.note.text)
        self.assertEqual(note.slug, self.note.slug)

    def test_author_can_delete_note(self):
        """Автор может удалить свою заметку."""
        response = self.author_client.post(
            reverse('notes:delete', args=(self.note.slug,)),
        )

        self.assertRedirects(response, reverse('notes:success'))
        self.assertFalse(Note.objects.filter(pk=self.note.pk).exists())

    def test_other_user_cant_delete_note(self):
        """Другой пользователь не может удалить заметку."""
        response = self.not_author_client.post(
            reverse('notes:delete', args=(self.note.slug,)),
        )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTrue(Note.objects.filter(pk=self.note.pk).exists())
