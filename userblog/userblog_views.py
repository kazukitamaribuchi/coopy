from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.edit import ModelFormMixin
from django.views import generic
from django.http import HttpResponseBadRequest, Http404
from django.urls import reverse_lazy
from blog.views import BaseListView
from blog.models import MyUser, Blog, Post, Tag, Category, Comment, AccessLog, AccessAnalytics
from blog.forms import CommentForm, SearchForm
from django.contrib.auth.mixins import LoginRequiredMixin
import logging, uuid, csv, datetime, re

logger = logging.getLogger(__name__)

LOG_FILE_PATH = 'logs/access_log.csv'
BROWSER_LIST = ['Chrome', 'Firefox', 'Edge', 'Safari', 'Other']

class UserBlogView(BaseListView):

    template_name = 'blog/myblog.html'
    context_object_name = 'posts_list'
    paginate_by = 10

    # def render_to_response(self, context, **responsekwargs):
    #     response = super(UserBlogView, self).render_to_response(context, **responsekwargs)
    #     return setCookie(response)

    def get(self, request, *args, **kwargs):
        insertAccessLog(request, *args, **kwargs)
        return super().get(request, *args, **kwargs)

    # 現時点では、ログインユーザーのemailと筆者のemailで紐づけて記事を表示。
    def get_queryset(self, **kwargs):
        user = self.request.user
        url = self.request.path.strip('/')
        # queryset = Post.objects.filter(isPublic=True, blog__user=user)
        queryset = Post.objects.filter(isPublic=True, blog__url=url)

        if 'form_value' in self.request.session:
            title = self.request.session['form_value']
            # queryset = Post.objects.filter(isPublic=True, title=title, blog__user=user)
            queryset = Post.objects.filter(isPublic=True, blog__url=url)
            del self.request.session['form_value']
            return queryset
        else:
            return queryset

    def get_context_data(self, **kwargs):
        url = self.request.path.strip('/')
        context = super().get_context_data(**kwargs)
        context.update({
            'blog' : Blog.objects.get(url=url)
        })
        return context


class PostDetailView(generic.DetailView, ModelFormMixin):

    model = Post
    form_class = CommentForm
    template_name = 'blog/detail.html'
    context_object_name = 'detail'

    # def render_to_response(self, context, **responsekwargs):
    #     response = super(PostDetailView, self).render_to_response(context, **responsekwargs)
    #     return setCookie(response)

    def get(self, request, *args, **kwargs):
        insertAccessLog(request, *args, **kwargs)
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        post_pk = self.kwargs['pk']
        comment = form.save(commit=False)
        comment.target = get_object_or_404(Post, pk=post_pk)
        comment.save()
        return redirect('blog:comment_post')

    def post(self, request, *args, **kwargs):
        self.object = None
        self.object_list = self.get_queryset()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            self.object = self.get_object()
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            # 検索フォーム
            'post_search_form': SearchForm
        })
        return context


def insertAccessLog(request, *args, **kwargs):

    host = request.get_host()
    ip_address = request.META.get('REMOTE_ADDR')
    page = host + request.get_full_path()

    access_page = request.get_full_path()[1:]
    access_blog_slug = access_page[:access_page.index('/')]

    try:
        TARGET_BLOG = Blog.objects.get(url=access_blog_slug)
    except Blog.DoesNotExist:
        raise Http404

    access_blog_id = TARGET_BLOG.pk
    access_blog_name = TARGET_BLOG.title
    access_blog_owner = TARGET_BLOG.user
    access_blog_url = TARGET_BLOG.url

    logger.info(request.META)

    if 'favicon.ico' not in page:
        user = request.user
        timezone = request.META['TZ']
        language = request.META['LANG']
        user_agent = request.META['HTTP_USER_AGENT']
        pattern = r'(?<=\().*;'
        device = re.search(pattern, user_agent).group(0)[:-1].split('; ')[0]
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        referer = request.META['HTTP_REFERER'] if 'HTTP_REFERER' in request.META else None

        pattern2 = r'(?<=\)\s)+(.*)'
        USER_AGENT = re.search(pattern2, user_agent).group(0).split(' ')
        browser = re.match(r'.*(?=[/\s])', USER_AGENT[-1]).group(0)

        if browser == 'Safari':
            browser = 'Chrome' if USER_AGENT[-2][0:6] == 'Chrome' else 'Safari'
        if browser not in BROWSER_LIST:
            browser = 'Other'

        if request.COOKIES.get('uuId') != None:
            logger.debug('uuIdが存在する')
            uuId = request.COOKIES.get('uuId')

            request.session['uuId'] = uuId
            # request.session.set_expiry(0)

            if request.COOKIES.get('uuId') == request.session.get('uuId'):
                logger.debug('セッションにUUIDが存在するため新規UUIDは発行しない。')

            AccessLog.objects.create(
                blog_pk=access_blog_id,
                blog_name=access_blog_name,
                blog_owner=access_blog_owner,
                blog_url=access_blog_url,
                uuId=uuId,
                ip=ip_address,
                page=page,
                user=user,
                timezone=timezone,
                language=language,
                device=device,
                now=now,
                referer=referer,
                browser=browser
            )

        else:
            logger.debug(request.COOKIES)
            logger.debug('uuIdはCOOKIEに存在しない。')

    else:
        logger.debug('faviconログはいらんから飛ばす')


# def setCookie(response):
#     response.set_cookie('test', 'test')
#     return response
