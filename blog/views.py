from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.edit import ModelFormMixin, FormMixin
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse_lazy
from django.core.signing import BadSignature, SignatureExpired, loads, dumps
from django.http import HttpResponse, Http404, HttpResponseBadRequest, JsonResponse, QueryDict
from django.views import generic
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import Count, Q
from .models import MyUser, Blog, Post, Tag, Category, Comment, AccessLog, AccessAnalytics
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.hashers import check_password
from django.contrib import messages
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordChangeDoneView
)
from .forms import (
    LoginForm,
    CreateUserForm,
    CommentForm,
    SearchForm,
    PostForm,
    TagForm,
    ChangePasswordForm,
    UpdateAccountForm,
    UpdateUsernameForm,
    UpdateEmailForm,
    UpdatePasswordForm,
    UpdateAccountValidateForm,
    BlogManagementForm,
    UpdateBlogTitleForm,
    UpdateBlogUrlForm,
    UpdateBlogInfoAllForm,
)

import logging
import json
import re
from django.core.mail import send_mail
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from functools import reduce
import operator
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

LOG_FILE_PATH = 'logs/access_log.csv'
BROWSER_LIST = ['Chrome', 'Firefox', 'Edge', 'Safari', 'Other']

# ListViewのための継承用クラス
# paginate_by, ordering, template_nameはページ毎に指定する。
class BaseListView(generic.ListView):

    # デフォルトでPostモデルを表示
    model = Post

    # 記事リストの変数名を定義
    context_object_name = 'posts_list'

    # 検索フォームはPostだから、その時のため
    # def post(self, request, *args, **kwargs):
    #
    #     form_value = self.request.POST.get('title', None)
    #     request.session['form_value'] = form_value
    #     return self.get(request, *args, **kwargs)

    # デフォルトとなるクエリー。公表フラグTrueのもののみ表示

    def base_queryset(self):

        queryset = Post.objects.filter(isPublic=True)
        return queryset

    # テンプレートに渡す変数を定義する。
    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context.update({
            # カテゴリーリスト
            'category_list': Category.objects.all().annotate(Count('post')).order_by('created_at'),

            # 検索フォーム
            'post_search_form': SearchForm,

        })

        # 検索フォームから検索されたら、そのワードを変数で持っておく。
        title = ''
        if 'form_value' in self.request.session:
            title = self.request.session['form_value']

        return context



# トップページ
# 現時点でIndexViewはマイページ兼用になっている。
# ログインされたらテンプレートで {% if user.is_authenticated %} で判定可能
class IndexView(BaseListView):

    template_name = 'blog/index.html'

    # 1ページの記事表示数
    paginate_by = 6

    def get_queryset(self, **kwargs):

        logger.info(self.request.COOKIES)

        queryset = self.base_queryset()

        # 検索フォームから検索されたら、そのワードを元に、クエリーを更新する。
        # BaseListViewで変数で持ってるから、変数定義はいらないかも。
        if 'form_value' in self.request.session:
            title = self.request.session['form_value']
            queryset = Post.objects.filter(title=title)
            del self.request.session['form_value']
            return queryset
        else:
            return queryset

    # Topページに渡したい変数を定義
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'popular_posts_list': Post.objects.filter(isPublic=True).order_by('-created_at')[0:6]
        })
        return context


# サインアップページ
class SignupView(generic.CreateView):

    template_name = 'register/signup.html'
    form_class = CreateUserForm

    def __init__(self):
        self.error_dict = {}

    # フォームから正常にsubmitが来たら、ボタンを判定して確認画面or仮登録
    def form_valid(self, form):

        context = {'form': form}

        logger.info("------------------------------")

        # 最初のボタンはname=confirm_btnで確認画面を返す
        if self.request.POST.get('confirm_btn', '') == 'confirm':
            return render(self.request, 'register/signup_confirm.html', context)
        # 確認画面から戻るボタンname=back_btnを押したら、前に戻る
        elif self.request.POST.get('back_btn', '') == 'back':
            return render(self.request, 'register/signup.html', context)
        # 確認画面から作成ボタンname=create_btnを押したら、仮登録しメールを送る
        elif self.request.POST.get('create_btn', '') == 'create':

            user = form.save(commit=False)
            user.is_active = False
            user.save()

            current_site = get_current_site(self.request)
            domain = current_site.domain
            context = {
                'protocol': 'https' if self.request.is_secure() else 'http',
                'domain': domain,
                'token': dumps(user.pk),
                'user': user,
            }

            subject = '題名'
            message = render_to_string('register/mail_template/message.txt', context)
            user.email_user(subject, message)

            return redirect(reverse_lazy('blog:signup_done'))

        # それ以外はエラー扱い
        else:
            return HttpResponseBadRequest()

    def form_invalid(self, form):
        error_list = ['username', 'email', 'password1', 'password2']

        for error_name in error_list:
            if error_name in form.errors:
                self.error_dict[error_name + '_error_msg'] = form.errors[error_name][0]

        return super().get(self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for k, v in self.error_dict.items():
            context.update({
                k: v
            })
        return context


# 認証メール送信後のページ
class SignupDoneView(generic.TemplateView):

    template_name = 'register/signup_done.html'

# メール認証完了後のページ
class SignupCompleteView(generic.TemplateView):

    template_name = 'register/signup_complete.html'

    # 認証の制限時間を設定
    timeout_seconds = getattr(settings, 'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)

    # 認証ページに飛んで来たら、tokenが正しいか判定。
    # 正しくなければエラーページに飛ばし、正しければユーザーのステータスをactiveにする。
    def get(self, request, **kwargs):
        token = kwargs.get('token')
        try:
            user_pk = loads(token, max_age=self.timeout_seconds)

        except SignatureExpired:
            return HttpResponse("Expired error")

        except BadSignature:
            return HttpResponse("token error")

        else:
            try:
                user = MyUser.objects.get(pk=user_pk)

                blog_title = user.username + "'s blog"

                Blog.objects.create(
                    title=blog_title,
                    user=user,
                    url=user.username
                )

            except MyUser.DoesNotExist:
                return HttpResponseBadRequest()
            else:
                if not user.is_active:
                    user.is_active = True
                    user.save()
                    return super().get(request, **kwargs)

        return HttpResponseBadRequest()


# ログインページ
class LoginView(LoginView):

    form_class = LoginForm
    template_name = 'register/login.html'


# ログアウト後のページ
class LogoutView(LoginRequiredMixin, LogoutView):

    template_name = 'register/logout.html'


class CreatePostView(LoginRequiredMixin, generic.CreateView):

    model = Post
    template_name = 'blog/create_post.html'
    form_class = PostForm


    def get_form_kwargs(self):
        self.user = self.request.user
        kwargs = super(CreatePostView, self).get_form_kwargs()
        kwargs.update({
            'user': self.user
        })
        return kwargs

    def post(self, request, *args, **kwargs):

        logger.debug('-------記事作成--------')
        logger.debug(request.POST)
        title = request.POST.get('title')
        blog = Blog.objects.get(user=request.user)
        content = request.POST.get('content')
        tag_list = request.POST.getlist('tags')

        thumbnail = request.FILES['thumbnail'] if 'thumbnail' in request.FILES else None
        isPublic = True if request.POST.get('create_post_btn') == 'create_post' else False

        category = request.POST.get('category')
        if category == None:
            try:
                category_instance = Category.objects.get(name='未分類')
            except Category.DoesNotExist:
                category_instance = Category.objects.create(
                    name='未分類',
                    slug='other',
                    created_by=request.user
                )
        elif category.isdigit():
            logger.debug('categoryは数値 = ' + category)
            category_instance = Category.objects.get(pk=category)
        else:
            logger.debug('文字列だからAjaxから？ = ' + str(category))
            category_instance = Category.objects.get(name=category)

        post = Post.objects.create(
            title=title,
            blog=blog,
            category=category_instance,
            content=content,
            thumbnail=thumbnail,
            isPublic=isPublic
        )
        post.save()

        if len(tag_list) != 0:
            tag_instance_list = [Tag.objects.get(name=tag) for tag in tag_list]
            for tag in tag_instance_list:
                logger.debug('------追加タグ一覧-------')
                logger.debug(tag)
                post.tags.add(tag)

        return redirect(reverse_lazy('blog:index'))


class AddTagView(generic.View):

    def post(self, request, *args, **kwargs):

        param = request.POST.get('tag')

        if param != '':

            pattern = r'(^[0-9]+$)'
            result = re.match(pattern, param)
            if result:
                res = {
                    'status': 'error',
                    'message': '英数字を含んだタグにしてください。'
                }
                return JsonResponse(res, status=500)

            try:
                Tag.objects.get(name=param, created_by=request.user)
                res = {
                    'status': 'error',
                    'message': '既に同じタグが存在します'
                }
                return JsonResponse(res, status=500)
            except Tag.DoesNotExist:
                Tag.objects.create(
                    name = param,
                    created_by = request.user,
                    slug = param,
                )
                tag_name = Tag.objects.get(name=param).name

                msg = 'タグ追加成功しました'
                res = {
                    'param': param,
                    'tag_name': tag_name,
                    'message': msg
                }

                return JsonResponse(res)

        else:
            res = {
                'status': 'error',
                'message': '値が空です'
            }
            return JsonResponse(res, status=500)

class AddCategoryView(generic.View):

    def post(self, request, *args, **kwargs):
        param = request.POST.get('category')

        if param != '':

            pattern = r'(^[0-9]+$)'
            result = re.match(pattern, param)
            if result:
                res = {
                    'status': 'error',
                    'message': '英数字を含んだカテゴリにしてください。'
                }
                return JsonResponse(res, status=500)

            try:
                Category.objects.get(name=param, created_by=request.user)
                res = {
                    'status': 'error',
                    'message': '既に同じカテゴリが存在します'
                }
                return JsonResponse(res, status=500)
            except Category.DoesNotExist:
                Category.objects.create(
                    name = param,
                    created_by = request.user,
                    slug = param,
                )
                category_name = Category.objects.get(name=param).name
                msg = 'カテゴリ追加成功しました'
                res = {
                    'param': param,
                    'category_name': category_name,
                    'message': msg,
                }
                return JsonResponse(res)
        else:
            res = {
                'status': 'error',
                 'message': '値が空です'
            }
            return JsonResponse(res, status=500)


# # ユーザーのブログ
# class MyBlogView(LoginRequiredMixin, BaseListView):
#
#     template_name = 'blog/myblog.html'
#     context_object_name = 'posts_list'
#     paginate_by = 10
#
#     def get(self, request, *args, **kwargs):
#         logger.info(self.request)
#
#         return super().get(request, *args, **kwargs)
#
#
#     # 現時点では、ログインユーザーのemailと筆者のemailで紐づけて記事を表示。
#     def get_queryset(self, **kwargs):
#
#         user = self.request.user
#         queryset = Post.objects.filter(isPublic=True, blog__user=user)
#
#         if 'form_value' in self.request.session:
#             title = self.request.session['form_value']
#             queryset = Post.objects.filter(isPublic=True, title=title, blog__user=user)
#             del self.request.session['form_value']
#             return queryset
#         else:
#             return queryset
#
#     def get_context_data(self, **kwargs):
#
#         context = super().get_context_data(**kwargs)
#         context.update({
#             # テンプレートNo
#             # 'temp_no' : Blog.objects.get(user=self.request.user)
#         })
#         return context


class PostDetailView(generic.DetailView, ModelFormMixin):

    model = Post
    form_class = CommentForm
    template_name = 'blog/detail.html'
    context_object_name = 'detail'

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

class MyPageView(LoginRequiredMixin, generic.TemplateView):

    template_name = 'blog/mypage.html'

    # def get_context_data(self, *args, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context.update({
    #         'blog' : Blog.objects.get(user=self.request.user)
    #     })
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            'blog': Blog.objects.get(user=self.request.user)
        })
        return context

class AccountDetailView(LoginRequiredMixin, generic.DetailView):

    model = MyUser
    template_name = 'blog/mypage.html'

    # def post(self, request, *args, **kwargs):

        # return HttpResponse(request.body)

        # if request.POST.get('update_account_detail_btn') == 'update_account_detail_confirm':
        #     context = {'form': UserInfoUpdateForm}
        #     return render(request, 'register/update_account_detail_confirm.html', context)
            # return HttpResponse('1')
        # elif request.POST.get('update_account_detail_btn') == 'update_account_detail':
        #     # user = MyUser.objects.filter(email=request.user.email)
        #     # username = request.POST.get('username')
        #     # email = request.POST.get('email')
        #     #
        #     # user.username = username
        #     # user.email = email
        #     # user.save()
        #
        #     # return redirect('blog:account_detail')
        #
        #     return HttpResponse('2')


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'blog': Blog.objects.get(user=self.request.user),
            'updateAcountForm': UpdateAccountForm
        })
        return context


class UpdateAccountView(LoginRequiredMixin, generic.UpdateView):

    model = MyUser
    template_name = 'register/update_account.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'blog': Blog.objects.get(user=self.request.user),
        })
        return context


class BlogManagementView(LoginRequiredMixin, generic.UpdateView):

    model = Blog
    template_name = 'blog/mypage.html'
    form_class = BlogManagementForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'blog': Blog.objects.get(user=self.request.user),
        })
        return context


class CommentPostView(generic.TemplateView):

    template_name = 'blog/comment_post.html'

class SearchResultView(BaseListView):

    template_name = 'blog/search_result.html'

    # 1ページの記事表示数
    paginate_by = 6

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 検索ワード出力用
        context.update({
            'search_result':self.request.GET.get('q', ''),
            'query_string':self.request.GET.urlencode()
        })

        return context

    def get_queryset(self, **kwargs):

        queryset = self.base_queryset()

        if 'q' in self.request.GET:
            #クエリパラメータがあるので検索用の処理をする
            query_param = self.request.GET.get('q')

            q = SearchForm.parse_search_params(query_param)
            logger.info(q)

            if q:
                query = reduce(operator.or_,(
                    Q(title__icontains=w) | Q(content__icontains=w) for w in q
                ))
                logger.info(query)

                queryset = Post.objects.filter(query).order_by('-updated_at')
                logger.info(queryset)

        return queryset


class UpdateAccountAllView(LoginRequiredMixin, generic.View):

    def post(self, request, *args, **kwargs):

        post_data = request.POST.copy()
        login_user_password = request.user.password
        post_data.update({
            'login_user_password': login_user_password
        })

        form = UpdateAccountValidateForm(post_data)

        if form.is_valid():
            user = MyUser.objects.get(username=request.user.username)

            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            new_password = form.cleaned_data['new_password']

            user.username = username
            user.email = email
            user.set_password(new_password)
            user.save()
            res = {
                'status': 'success',
                'message': '一括更新が完了しました。',
                'username': username,
                'email': email,
                'password': password,
                'new_password': new_password,
            }
            return JsonResponse(res)

        else:
            logger.debug('一括更新失敗')
            res = {
                'status': 'error',
                'message': 'エラーが発生しました。'
            }
            if 'username' in form.errors:
                res['username_error_msg'] = form.errors['username'][0]

            if 'email' in form.errors:
                res['email_error_msg'] = form.errors['email'][0]

            if 'password' in form.errors:
                res['password_error_msg'] = form.errors['password'][0]

            if 'new_password' in form.errors:
                res['new_password_error_msg'] = form.errors['new_password'][0]

            if 'new_password_confirm' in form.errors:
                res['new_password_confirm_error_msg'] = form.errors['new_password_confirm'][0]

            logger.debug('-----res-----')
            logger.debug(res)
            return JsonResponse(res, status=500)


class UpdateUsernameView(LoginRequiredMixin, generic.View):

    def post(self, request, *args, **kwargs):

        form = UpdateUsernameForm(request.POST)
        # logger.info(form.errors)

        if form.is_valid():
            username = form.cleaned_data['username']
            user = MyUser.objects.get(email=request.user.email)
            user.username = username
            user.save()
            logger.info(request.user.username)
            res = {
                'status': 'success',
                'message': '更新が完了しました。',
                'username': username
            }
            return JsonResponse(res)

        else:
            res = {
                'status': 'error',
                'message': 'エラーが発生しました。',
            }

            if 'username' in form.errors:
                res['username_error_msg'] = form.errors['username'][0]

            return JsonResponse(res, status=500)



class UpdateEmailView(LoginRequiredMixin, generic.View):

    def post(self, request, *args, **kwargs):

        form = UpdateEmailForm(request.POST)
        logger.info(form.errors)

        if form.is_valid():
            email = form.cleaned_data['email']
            user = MyUser.objects.get(email=request.user.email)
            user.email = email
            user.save()
            res = {
                'status': 'success',
                'message': '更新が完了しました。',
                'email': email
            }
            return JsonResponse(res)

        else:
            res = {
                'status': 'error',
                'message': 'エラーが発生しました。',
            }

            if 'email' in form.errors:
                res['email_error_msg'] = form.errors['email'][0]

            return JsonResponse(res, status=500)


class UpdatePasswordView(LoginRequiredMixin, generic.View):


    def post(self, request, *args, **kwargs):

        post_data = request.POST.copy()
        login_user_password = request.user.password
        post_data.update({
            'login_user_password': login_user_password
        })

        form = UpdatePasswordForm(post_data)
        logger.info(form.errors)

        if form.is_valid():
            password = form.cleaned_data['password']
            new_password = form.cleaned_data['new_password']
            user = MyUser.objects.get(email=request.user.email)
            user.set_password(new_password)
            user.save()
            res = {
                'status': 'success',
                'message': '更新が完了しました。',
                'password': password,
                'new_password': new_password
            }
            return JsonResponse(res)

        else:
            res = {
                'status': 'error',
                'message': 'エラーが発生しました。',
            }

            if 'password' in form.errors:
                res['password_error_msg'] = form.errors['password'][0]

            if 'new_password' in form.errors:
                res['new_password_error_msg'] = form.errors['new_password'][0]

            if 'new_password_confirm' in form.errors:
                res['new_password_confirm_error_msg'] = form.errors['new_password_confirm'][0]

            return JsonResponse(res, status=500)


class EditContentsListView(LoginRequiredMixin, BaseListView):

    template_name = 'blog/mypage.html'
    # 1ページの記事表示数
    paginate_by = 10

    def get_queryset(self, **kwargs):
        queryset = Post.objects.filter(blog__user=self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'blog': Blog.objects.get(user=self.request.user),
        })
        return context




class EditContentView(LoginRequiredMixin,generic.UpdateView):

    template_name = 'blog/edit_content.html'
    model = Post
    form_class = PostForm

    def get_form_kwargs(self):
        self.user = self.request.user
        self.category_id = Post.objects.get(pk=self.kwargs['pk']).category.id
        kwargs = super(EditContentView, self).get_form_kwargs()
        kwargs.update({
            'user': self.user,
            'category_id': self.category_id
        })

        return kwargs

    def post(self, request, *args, **kwargs):
        logger.info('`記事更新`')
        logger.info(request.POST)
        title = request.POST.get('title')
        blog = Blog.objects.get(user=request.user)
        content = request.POST.get('content')
        tag_list = request.POST.getlist('tags')
        thumbnail = request.FILES['thumbnail'] if 'thumbnail' in request.FILES else None
        isPublic = True if request.POST.get('update_content_btn') == 'update_content' else False

        category = request.POST.get('category')
        if category == None:
            try:
                category_instance = Category.objects.get(name='未分類')
            except Category.DoesNotExist:
                category_instance = Category.objects.create(
                    name='未分類',
                    slug='other',
                    created_by=request.user
                )
        elif category.isdigit():
            logger.debug('categoryは数値 = ' + category)
            category_instance = Category.objects.get(pk=category)
        else:
            logger.debug('文字列だからAjaxから？ = ' + str(category))
            category_instance = Category.objects.get(name=category)

        try:
            post = Post.objects.get(id=self.kwargs['pk'])
            post.title = title
            post.content = content
            post.blog = blog
            post.category = category_instance
            post.thumbnail = thumbnail
            post.isPublic = isPublic
            post.tags.clear()
        except Post.DoesNotExist:
            logger.debug('記事取得失敗')

        if len(tag_list) != 0:
            tag_instance_list = [Tag.objects.get(name=tag) for tag in tag_list]

            for tag in tag_instance_list:
                post.tags.add(tag)

        post.save()

        return redirect(reverse_lazy('blog:edit_contents_list'))


    def form_valid(self, form):

        logger.debug('--form_valid--')
        if self.request.POST.get('update_content_btn') == 'update_content':
            form.instance.isPublic = True
        else:
            form.instance.isPublic = False

        result = super().form_valid(form)
        return result


class DeleteContentView(LoginRequiredMixin, generic.View):

    model = Post

    def post(self, request, *args, **kwargs):

        post_data = request.POST.copy()
        content_pk = post_data['content_pk']

        try:
            content = Post.objects.get(pk=content_pk)
            logger.debug(content)

            content.delete()
            res = {
                'status': 'success',
                'message': '記事が削除されました',
                'content_pk': content_pk,
            }

            return JsonResponse(res)

        except Post.DoesNotExist:
            logger.debug('エラーに進んでる')
            res = {
                'status': 'error',
                'message': 'エラーが発生しました。',
                'content_pk': content_pk,
            }

            return JsonResponse(res, status=500)


class CommentsListView(LoginRequiredMixin, generic.ListView):

    model = Comment
    context_object_name = 'comments_list'
    template_name = 'blog/mypage.html'
    paginate_by = 10

    def get_queryset(self):

        queryset = Comment.objects.filter(target__blog__user=self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'blog': Blog.objects.get(user=self.request.user),
        })
        return context


class UpdateCommentsListView(LoginRequiredMixin, generic.View):

    # modal = Comment

    def post(self, request, *args, **kwargs):

        post_data = request.POST.copy()
        comment_pk = post_data['comment_pk']
        select_value = post_data['select_value']

        try:
            comment = Comment.objects.get(pk=comment_pk)
            if select_value == '承認':
                comment.is_public = True
                comment.save()
                message = 'コメントが承認されました'
            elif select_value == '非承認':
                comment.is_public = False
                comment.save()
                message = 'コメントが非承認されました'
            else:
                comment.delete()
                message = 'コメントが削除されました'

            logger.debug(comment.is_public)

            res = {
                'status': 'success',
                'message': message,
                'comment_pk': comment_pk,
                'select_value': select_value,
            }

            return JsonResponse(res)

        except Post.DoesNotExist:
            logger.debug('エラーに進んでる')
            res = {
                'status': 'error',
                'message': 'エラーが発生しました。',
                'comment_pk': comment_pk,
                'select_value': select_value,
            }

            return JsonResponse(res, status=500)


class DesignCustomizeView(LoginRequiredMixin, generic.TemplateView):

    template_name = 'blog/mypage.html'
    model = Blog

    def post(self, request, *args, **kwargs):
        post_data = request.POST.copy();
        temp_no = post_data['temp_no']
        temp_path = post_data['temp_path']

        try:
            blog = Blog.objects.get(user=request.user)
            blog.temp_no = temp_no
            blog.temp_path = temp_path
            blog.save()

            res = {
                'status' : 'success',
                'message' : 'テンプレートの選択に成功しました',
                'temp_no' : temp_no,
                'temp_path' : temp_path,
            }

            return JsonResponse(res)

        except Blog.DoesNotExist:
            logger.debug('カスタマイズのエラーに進んでいる')
            res = {
                'status' : 'error',
                'message' : 'テンプレートの選択に失敗しました',
                'temp_no' : temp_no,
                'temp_path' : temp_path,
            }

            return JsonResponse(res, status=500)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'blog': Blog.objects.get(user=self.request.user),
            'posts_list' : Post.objects.filter(isPublic=True, blog__user=self.request.user)
        })
        return context


class UpdateBlogTitleView(LoginRequiredMixin, generic.View):

    def post(self, request, *args, **kwargs):

        form = UpdateBlogTitleForm(request.POST)

        if form.is_valid():
            title = form.cleaned_data['title']
            blog = Blog.objects.get(user=request.user)
            blog.title = title
            blog.save()
            res = {
                'status': 'success',
                'message': '更新が完了しました。',
                'title': title
            }
            return JsonResponse(res)

        else:
            logger.debug(form)
            res = {
                'status': 'error',
                'message': 'エラーが発生しました。',
            }

            if 'title' in form.errors:
                res['title_error_msg'] = form.errors['title'][0]

            return JsonResponse(res, status=500)


class UpdateBlogUrlView(LoginRequiredMixin, generic.View):

    def post(self, request, *args, **kwargs):

        form = UpdateBlogUrlForm(request.POST)

        if form.is_valid():
            url = form.cleaned_data['url']
            blog = Blog.objects.get(user=request.user)
            blog.url = url
            blog.save()
            res = {
                'status': 'success',
                'message': '更新が完了しました。',
                'url': url
            }
            return JsonResponse(res)

        else:
            res = {
                'status': 'error',
                'message': 'エラーが発生しました。',
            }

            if 'url' in form.errors:
                res['url_error_msg'] = form.errors['url'][0]

            return JsonResponse(res, status=500)

class UpdateBlogInfoAllView(LoginRequiredMixin, generic.View):

    def post(self, request, *args, **kwargs):

        form = UpdateBlogInfoAllForm(request.POST)

        if form.is_valid():

            title = form.cleaned_data['title']
            url = form.cleaned_data['url']

            blog = Blog.objects.get(user=request.user)
            blog.title = title
            blog.url = url
            blog.save()

            res = {
                'status': 'success',
                'message': '更新が完了しました。',
                'title': title,
                'url': url
            }
            return JsonResponse(res)

        else:
            logger.debug('一括更新失敗')
            res = {
                'status': 'error',
                'message': 'エラーが発生しました。'
            }
            if 'title' in form.errors:
                res['title_error_msg'] = form.errors['title'][0]

            if 'url' in form.errors:
                res['url_error_msg'] = form.errors['url'][0]


            logger.debug('-----res-----')
            logger.debug(res)
            return JsonResponse(res, status=500)




class AccessAnalyticsView(LoginRequiredMixin, generic.TemplateView):

    template_name = 'blog/mypage.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        FILE_PATH = 'accessAnalytics/images/'
        blog_name = Blog.objects.get(user=self.request.user).title

        now = datetime.now()

        pv_img_week = FILE_PATH + 'no_access_week.png'
        pv_img_week_bar = FILE_PATH + blog_name + '_pv_week_bar.png'
        user_img_week_bar = FILE_PATH + blog_name + '_user_week_bar.png'

        blog_name_q = Q(blog_name=blog_name)
        created_at_day_q = Q(created_at__date=now)
        created_while_week_q = Q(created_at__range=(now - timedelta(days=7), now))

        isAccess = True if len(AccessAnalytics.objects.filter(blog_name_q & created_while_week_q)) != 0 else False

        day_pv = 0
        day_user = 0
        day_device = 0
        week_pv = 0
        week_user = 0
        week_device = 0

        if isAccess:
            if len(AccessAnalytics.objects.filter(blog_name_q)) != 0:
                AnalyticsInstance = AccessAnalytics.objects.filter(blog_name_q).order_by('-created_at').first()
                day_pv = AnalyticsInstance.day_pv
                day_user = AnalyticsInstance.day_user
                week_pv = AnalyticsInstance.week_pv
                week_user = AnalyticsInstance.week_user

                pv_img_week = FILE_PATH + blog_name + '_pv_week.png'

                # 解析してないからとりあえず固定
                day_device = '39.8%'
                week_device = '39.8%'


        context.update({
            'blog': Blog.objects.get(user=self.request.user),
            'pv_img_week': pv_img_week,
            'pv_img_week_bar': pv_img_week_bar,
            'user_img_week_bar': user_img_week_bar,
            'isAccess': isAccess,
            'day_pv': day_pv,
            'day_user': day_user,
            'day_device': day_device,
            'week_pv': week_pv,
            'week_user': week_user,
        })
        return context

class CategoryListView(BaseListView):
    template_name = 'blog/category_list.html'
    model = Post
    paginate_by = 6

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            'category_name' : self.kwargs['str'],
        })

        return context

    def get_queryset(self, **kwargs):

        queryset = self.base_queryset()
        queryset = Post.objects.filter(category__name=self.kwargs['str'])

        return queryset

class TagsListView(BaseListView):
    template_name = 'blog/tags_list.html'
    model = Post
    paginate_by = 6

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            'tag_name' : self.kwargs['str'],
        })

        return context

    def get_queryset(self, **kwargs):

        queryset = self.base_queryset()
        queryset = Post.objects.filter(tags__name=self.kwargs['str'])

        return queryset
