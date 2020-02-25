import re
import logging
from django import forms
from django.forms import inlineformset_factory
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
)
from django.contrib.auth.hashers import check_password
from django.contrib.auth import get_user_model, password_validation
from .models import MyUser, Blog, Post, Tag, Category, Comment
from typing import List

logger = logging.getLogger(__name__)

class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('name', 'text', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label


class SearchForm(forms.Form):

    q = forms.CharField(
        initial = '',
        required = False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label

    @staticmethod
    def parse_search_params(words: str) -> List[str]:
        search_words = words.replace('　',' ').split()

        return search_words

class LoginForm(AuthenticationForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label


class CreateUserForm(UserCreationForm):

    class Meta:
        model = MyUser
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label

    # def clean_email(self):
    #     email = self.cleaned_data['email']
    #     MyUser.objects.filter(email=email, is_active=False).delete()
    #     return email

    def clean_username(self):
        username = self.cleaned_data['username']
        pattern = r'^[a-zA-Z0-9]{2,30}$'
        result = re.match(pattern, username)

        try:
            MyUser.objects.get(username=username)
            raise forms.ValidationError('このユーザーネームは既に存在します。')
        except MyUser.DoesNotExist:
            if result:
                return username
            else:
                logger.info(username)
                raise forms.ValidationError('ユーザーネームは英数字2文字以上、30文字以下で入力してください。')

    def clean_email(self):
        email = self.cleaned_data['email']
        pattern = r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)'

        result = re.match(pattern, email)

        try:
            MyUser.objects.get(email=email)
            raise forms.ValidationError('既に登録済みのアドレスです。')
        except MyUser.DoesNotExist:
            if result:
                return email
            else:
                raise forms.ValidationError('正しいEmailを入力してください')

    def _post_clean(self):
        super()._post_clean()
        password = self.cleaned_data.get('password1')
        if password:
            try:
                password_validation.validate_password(password, self.instance)
            except forms.ValidationError as error:
                self.add_error('password1', error)


class PostForm(forms.ModelForm):


    class Meta:
        model = Post
        fields = (
            'title',
            'content',
            'category',
            'tags',
            'thumbnail',
            # 'isPublic'
            )


    title = forms.CharField(
        label = 'タイトル',
        required = True,
        widget = forms.TextInput(
            attrs={
                'placeholder':'タイトル',
                'form':'post_form'
            })
    )

    content = forms.CharField(
        label = '記事',
        required = True,
        widget = forms.Textarea(
            attrs={
                'form':'post_form'
            }
        )
    )

    category = forms.MultipleChoiceField(
        label = 'カテゴリ',
        required = True,
        # disabled = False,
        widget = forms. RadioSelect(attrs={
            'id': 'id_category',
            'form':'post_form'
        })
    )

    tags = forms.MultipleChoiceField(
        label = 'タグ',
        required = False,
        # disabled = False,
        widget = forms. CheckboxSelectMultiple(attrs={
            'id': 'id_tags',
            'form':'post_form'
        })
    )

    thumbnail = forms.ImageField(
        label = 'サムネイル',
        required = False,
        widget = forms.FileInput(attrs={
            'id': 'id_thumbnail',
            'form':'post_form',
        })
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.category_id = kwargs.pop('category_id', None)
        super(PostForm, self).__init__(*args, **kwargs)

        tag_all = Tag.objects.filter(created_by=self.user)
        tags_list = [(tag_all[i].name, tag_all[i].name) for i in range(0, len(tag_all))]
        self.fields['tags'].choices = tags_list

        categories = Category.objects.filter(created_by=self.user)
        categories_list = [(categories[i].id, categories[i].name) for i in range(0, len(categories))]
        self.fields['category'].choices = categories_list

        if self.category_id != None:
            self.fields['category'].initial = [Category.objects.get(pk=self.category_id).id]
        else:
            logger.debug('カテゴリIDない')

        if kwargs['instance'] != None:
            self.fields['thumbnail'].initial = kwargs['instance'].thumbnail
        else:
            logger.info('サムネイルが設定されていません')

        self.fields['title'].widget.attrs['class'] = 'form-control'
        self.fields['content'].widget.attrs['class'] = 'form-control'


class TagForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = Tag
        fields = ('name', )


class ChangePasswordForm(PasswordChangeForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class UpdateAccountForm(forms.Form):

    username = forms.CharField(
        label = 'ユーザー名',
        required = True
    )

    email = forms.CharField(
        label = 'メールアドレス',
        required = True
    )

    password = forms.CharField(
        label = '現在のパスワード',
        required = True
    )

    new_password = forms.CharField(
        label = '新しいパスワード',
        required = True
    )

    new_password_confirm = forms.CharField(
        label = 'パスワードの確認',
        required = True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'



class UpdateAccountValidateForm(forms.Form):

    username = forms.CharField(
        label = 'ユーザー名',
        required = True
    )

    email = forms.CharField(
        label = 'メールアドレス',
        required = True
    )

    password = forms.CharField(
        label = '現在のパスワード',
        required = True
    )

    new_password = forms.CharField(
        label = '新しいパスワード',
        required = True
    )

    new_password_confirm = forms.CharField(
        label = 'パスワードの確認',
        required = True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.login_user_password = args[0]['login_user_password']
        self.new_password = args[0]['new_password']

        logger.debug(args)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_username(self):
        username = self.cleaned_data['username']
        pattern = r'^[a-zA-Z0-9]{1,30}$'
        result = re.match(pattern, username)

        try:
            MyUser.objects.get(username=username)
            raise forms.ValidationError('このユーザーネームは既に存在します。')
        except MyUser.DoesNotExist:
            if result:
                return username
            else:
                raise forms.ValidationError('ユーザーネームは英数字1文字以上、30文字以下で入力してください。')

    def clean_email(self):
        email = self.cleaned_data['email']
        pattern = r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)'
        result = re.match(pattern, email)

        try:
            MyUser.objects.get(email=email)
            raise forms.ValidationError('既に登録済みのアドレスです。')
        except MyUser.DoesNotExist:
            if result:
                return email
            else:
                raise forms.ValidationError('正しいEmailを入力してください')

    def clean_password(self):

        password = self.cleaned_data['password']
        if check_password(password, self.login_user_password):
            return password
        else:
            raise forms.ValidationError('パスワードが違います。')

    def clean_new_password(self):

        new_password = self.cleaned_data['new_password']
        pattern = r'(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,50}$'
        result = re.match(pattern, new_password)

        if check_password(new_password, self.login_user_password):
            raise forms.ValidationError('現在のパスワードと被っています。')
        else:
            if result:
                return new_password
            else:
                raise forms.ValidationError('パスワードは英数字8文字以上かつ大文字,小文字,数字を含めてください。')

    def clean_new_password_confirm(self):

        new_password_confirm = self.cleaned_data['new_password_confirm']
        pattern = r'(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,50}$'
        result = re.match(pattern, new_password_confirm)

        if self.new_password != new_password_confirm:
            raise forms.ValidationError('パスワードが一致しません。')
        else:
            return new_password_confirm


class UpdateUsernameForm(forms.Form):

    username = forms.CharField(
        label = 'ユーザー名',
        required = True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_username(self):
        username = self.cleaned_data['username']
        pattern = r'^[a-zA-Z0-9]{2,30}$'
        result = re.match(pattern, username)

        try:
            MyUser.objects.get(username=username)
            raise forms.ValidationError('このユーザーネームは既に存在します。')
        except MyUser.DoesNotExist:
            if result:
                return username
            else:
                raise forms.ValidationError('ユーザーネームは英数字2文字以上、30文字以下で入力してください。')



class UpdateEmailForm(forms.Form):

    email = forms.CharField(
        label = 'メールアドレス',
        required = True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_email(self):
        email = self.cleaned_data['email']
        pattern = r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)'
        result = re.match(pattern, email)

        try:
            MyUser.objects.get(email=email)
            raise forms.ValidationError('既に登録済みのアドレスです。')
        except MyUser.DoesNotExist:
            if result:
                return email
            else:
                raise forms.ValidationError('正しいEmailを入力してください')

class UpdatePasswordForm(forms.Form):

    password = forms.CharField(
        label = '現在のパスワード',
        required = True
    )

    new_password = forms.CharField(
        label = '新しいパスワード',
        required = True
    )

    new_password_confirm = forms.CharField(
        label = 'パスワードの確認',
        required = True
    )


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.login_user_password = args[0]['login_user_password']
        self.new_password = args[0]['new_password']

        logger.debug(args)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_password(self):

        password = self.cleaned_data['password']
        if check_password(password, self.login_user_password):
            return password
        else:
            raise forms.ValidationError('パスワードが違います。')

    def clean_new_password(self):

        new_password = self.cleaned_data['new_password']
        pattern = r'(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,50}$'
        result = re.match(pattern, new_password)

        if check_password(new_password, self.login_user_password):
            raise forms.ValidationError('現在のパスワードと被っています。')
        else:
            if result:
                return new_password
            else:
                raise forms.ValidationError('パスワードは英数字8文字以上かつ大文字,小文字,数字を含めてください。')

    def clean_new_password_confirm(self):

        new_password_confirm = self.cleaned_data['new_password_confirm']
        pattern = r'(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,50}$'
        result = re.match(pattern, new_password_confirm)

        if self.new_password != new_password_confirm:
            raise forms.ValidationError('パスワードが一致しません。')
        else:
            if result:
                return new_password_confirm
            else:
                raise forms.ValidationError('パスワードは英数字8文字以上かつ大文字小文字を含めてください。')


class BlogManagementForm(forms.ModelForm):

    class Meta:
        model = Blog
        fields = ('title', 'url', )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label

class UpdateBlogTitleForm(forms.Form):

    title = forms.CharField(
        label = 'BlogTitle',
        required = True
    )

    def clean_title(self):
        title = self.cleaned_data['title']
        pattern = r'^[\d\D]{2,50}$'
        result = re.match(pattern, title)

        if len(Blog.objects.filter(title=title)) == 0:
            if result:
                return title
            else:
                raise forms.ValidationError('ブログ名は2文字以上、50文字以下で入力してください。')
        else:
            raise forms.ValidationError('このブログ名は既に存在します。')



class UpdateBlogUrlForm(forms.Form):

    url = forms.CharField(
        label = 'BlogUrl',
        required = True
    )

    def clean_url(self):
        url = self.cleaned_data['url']
        pattern = r'^[a-zA-Z0-9]{2,200}$'
        result = re.match(pattern, url)

        if len(Blog.objects.filter(url=url)) == 0:
            if result:
                logger.debug(len(Blog.objects.filter(url=url)))
                return url
            else:
                raise forms.ValidationError('URLは英数字2文字以上、200文字以下で入力してください。')
        else:
            raise forms.ValidationError('このURLは既に存在します。')



class UpdateBlogInfoAllForm(forms.Form):

    title = forms.CharField(
        label = 'BlogTitle',
        required = True
    )

    url = forms.CharField(
        label = 'BlogUrl',
        required = True
    )

    def clean_title(self):
        title = self.cleaned_data['title']
        pattern = r'^[\d\D]{2,50}$'
        result = re.match(pattern, title)

        if len(Blog.objects.filter(title=title)) == 0:
            if result:
                return title
            else:
                raise forms.ValidationError('ブログ名は2文字以上、50文字以下で入力してください。')
        else:
            raise forms.ValidationError('このブログ名は既に存在します。')

    def clean_url(self):
        url = self.cleaned_data['url']
        pattern = r'^[\d\D]{2,50}$'
        result = re.match(pattern, url)

        if len(Blog.objects.filter(url=url)) == 0:
            if result:
                return url
            else:
                raise forms.ValidationError('URLは2文字以上、50文字以下で入力してください。')
        else:
            raise forms.ValidationError('このURLは既に存在します。')
