from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note


User = get_user_model()


class TestContent(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.not_author = User.objects.create(username='Не автор')

        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=cls.author,
        )

        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.not_author_client = Client()
        cls.not_author_client.force_login(cls.not_author)

    def test_note_in_object_list_for_author(self):
        """Автор видит свою заметку в списке."""
        response = self.author_client.get(reverse('notes:list'))
        object_list = response.context['object_list']

        self.assertIn(self.note, object_list)

    def test_note_not_in_object_list_for_other_user(self):
        """Чужие заметки не отображаются."""
        response = self.not_author_client.get(reverse('notes:list'))
        object_list = response.context['object_list']

        self.assertNotIn(self.note, object_list)

    def test_create_and_edit_pages_contains_form(self):
        """На страницах создания и редактирования присутствует форма."""
        urls = (
            reverse('notes:add'),
            reverse('notes:edit', args=(self.note.slug,)),
        )

        for url in urls:
            with self.subTest(url=url):
                response = self.author_client.get(url)

                self.assertIn('form', response.context)
                self.assertIsInstance(
                    response.context['form'],
                    NoteForm,
                )
