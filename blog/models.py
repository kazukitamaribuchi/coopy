from django.db import models
from django.core.mail import send_mail
from django.urls import reverse
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
import os, uuid, logging

# from markdownx.models import MarkdownxField
# from markdownx.utils import markdownify

logger = logging.getLogger(__name__)

class UserManager(BaseUserManager):

    use_in_migrations = True

    def _create_user(self, username, email, password, **extra_fields):

        """Create and save a user with the given username, email, and
        password."""
        if not username:
            raise ValueError('ユーザーネームは必須項目です。')

        email = self.normalize_email(email)
        username = self.model.normalize_username(username)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)


        blog_title = user.username + "'s blog"

        Blog.objects.create(
            title=blog_title,
            user=user,
            # temp_no='1',
            # temp_path='css/designTemplateCss/thema-1.css',
            url=user.username,
        )

        return user

    def create_user(self, username, email, password=None, **extra_fields):

        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):

        logger.info(username)
        logger.info(email)
        logger.info(password)

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(username, email, password, **extra_fields)


class MyUser(AbstractBaseUser, PermissionsMixin):
    """カスタムユーザーモデル."""

    username = models.CharField(_('Username'), max_length=30, unique=True)
    email = models.EmailField(_('Email'), unique=True)

    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_(
            'Designates whether the user can log into this admin site.'),
    )

    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )

    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.username

    def get_username(self):
        return self.username

    def email_user(self, subject, message, from_email=None, **kwargs):
        send_mail(subject, message, from_email, [self.email], **kwargs)


def _get_latest_post(request):
    return queryset.filter(is_public=True).order_by('created_at')[:5]


class Blog(models.Model):

    title = models.CharField(_('Blog Title'), max_length=50, blank=True, null=True)
    user = models.OneToOneField(MyUser, on_delete=models.CASCADE, primary_key=True)
    url = models.SlugField(_('Url'))
    icon = models.ImageField(_('Icon'), upload_to="upload/")
    temp_no = models.CharField(max_length=20, blank=True, null=True, default='1')
    temp_path = models.CharField(max_length=255, blank=True, null=True, default='css/designTemplateCss/thema-1.css')
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)

    def __str__(self):
        return "%s's blog" % self.user.username if self.title == None else self.title


class Category(models.Model):

    name = models.CharField(_('Category'), max_length=50, default='未分類')
    created_by = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    description = models.TextField(_('Description'), blank=True)
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    slug = models.SlugField(default=name)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = _('Categories')

    def get_latest_post(self):
        queryset = Post.objects.filter(category=self)
        return _get_latest_post(queryset)


class Tag(models.Model):

    name = models.CharField(_('Tag'), max_length=50)
    created_by = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    description = models.TextField(_('Description'), blank=True)
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    slug = models.SlugField(default=name)

    def __str__(self):
        return self.name

    def get_latest_post(self):
        queryset = Post.objects.filter(tag=self)
        return _get_latest_post(queryset)


def content_file_name(instance, filename):
    return 'upload/{0}/{1}/{2}'.format(instance.author, instance.title, filename)


class Post(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)
    # author = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE)
    title = models.CharField(_('Title'), max_length=255)
    content = models.TextField(_('Content'), blank=True, null=True)
    # content = MarkdownxField('Contents', help_text='markdown形式')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    # category = models.ManyToManyField(Category, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    # thumbnail = models.FileField('Thumbnail', upload_to=content_file_name, blank=True, null=True)
    thumbnail = models.ImageField(_('Thumbnail'), upload_to="upload/", blank=True, null=True)
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)
    isPublic = models.BooleanField(_('Publish or Not'), default=False)
    related_articles = models.ManyToManyField('self', blank=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog:index')

    def formatted_markdown(self):
        return markdownify(self.content)


class Comment(models.Model):

    name = models.CharField(max_length=255, blank=True, null=True)
    text = models.TextField(_('Text'))
    email = models.EmailField(_('Email'), max_length=255, blank=True)
    target = models.ForeignKey(Post, on_delete=models.CASCADE)
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    is_public = models.BooleanField(_('Publish or Not'), default=False)

    def __str__(self):
        return self.name


class AccessAnalytics(models.Model):

    blog_pk = models.PositiveIntegerField(_('Blog Pk'), null=True, blank=True)
    blog_name = models.CharField(_('Blog Name'), max_length=50, null=True, blank=True)
    blog_owner = models.CharField(_('Blog Owner'), max_length=30, null=True, blank=True)
    blog_url = models.URLField(_('Blog Url'), null=True, blank=True)
    total_pv = models.PositiveIntegerField(_('Total PV'), null=True, blank=True)
    month_pv = models.PositiveIntegerField(_('Monthly PV'), null=True, blank=True)
    week_pv = models.PositiveIntegerField(_('Weekly PV'), null=True, blank=True)
    day_pv = models.PositiveIntegerField(_('Daily PV'), null=True, blank=True)
    total_user = models.PositiveIntegerField(_('Total User'), null=True, blank=True)
    month_user = models.PositiveIntegerField(_('Monthly User'), null=True, blank=True)
    week_user = models.PositiveIntegerField(_('Weekly User'), null=True, blank=True)
    day_user = models.PositiveIntegerField(_('Daily User'), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.blog_name


class AccessLog(models.Model):

    blog_pk = models.PositiveIntegerField(_('Blog Pk'))
    blog_name = models.CharField(_('Blog Title'), max_length=50)
    blog_owner = models.CharField(_('Blog Owner'), max_length=30)
    blog_url = models.URLField(_('Blog Url'))
    uuId = models.UUIDField(_('Uuid'), editable=False)
    ip = models.GenericIPAddressField(_('IP Address'), unpack_ipv4=True)
    page = models.URLField(_('Page'), max_length=300)
    user = models.CharField(_('User'), max_length=30)
    timezone = models.CharField(_('Timezone'), max_length=30)
    language = models.CharField(_('Language'), max_length=30)
    device = models.CharField(_('Device'), max_length=50)
    now = models.CharField(_('Now'), max_length=30)
    referer = models.CharField(_('Referer'), max_length=300, null=True, blank=True)
    browser = models.CharField(_('Browser'), max_length=50)

    def __str__(self):
        return self.blog_name
