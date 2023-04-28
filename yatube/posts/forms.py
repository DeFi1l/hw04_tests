from django.forms import ModelForm

from .models import Post


class PostForm(ModelForm):

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {'text': 'Текст', 'group': 'Группа'}

        help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относится пост', }
