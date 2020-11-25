from django.urls import path, register_converter
from . import views

app_name = 'blog'

urlpatterns = [

    path('', views.IndexView.as_view(), name='index'),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('signup_done/', views.SignupDoneView.as_view(), name='signup_done'),
    path('signup_complete/<token>/', views.SignupCompleteView.as_view(), name='signup_complete'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('mypage/', views.MyPageView.as_view(), name='mypage'),
    path('mypage/create_post/', views.CreatePostView.as_view(), name='create_post'),
    # path('mypage/create_post_test/', views.CreatePostTestView.as_view(), name='create_post_test'),
    path('mypage/account_detail/<int:pk>/', views.AccountDetailView.as_view(), name='account_detail'),
    path('mypage/update_account/<int:pk>/', views.UpdateAccountView.as_view(), name='update_account'),
    path('mypage/blog_management/<int:pk>/', views.BlogManagementView.as_view(), name='blog_management'),
    path('mypage/blog_management/<int:pk>/update_blog_title/', views.UpdateBlogTitleView.as_view(), name='update_blog_title'),
    path('mypage/blog_management/<int:pk>/update_blog_url/', views.UpdateBlogUrlView.as_view(), name='update_blog_url'),
    path('mypage/blog_management/<int:pk>/update_blog_info_all/', views.UpdateBlogInfoAllView.as_view(), name='update_blog_info_all'),
    path('comment_post/', views.CommentPostView.as_view(), name='comment_post'),
    path('search/', views.SearchResultView.as_view(), name='search_result'),
    path('mypage/create_post/add_tag/', views.AddTagView.as_view(), name='add_tag'),
    path('mypage/create_post/add_category/', views.AddCategoryView.as_view(), name='add_category'),
    path('mypage/account_detail/<int:pk>/update_account_all/', views.UpdateAccountAllView.as_view(), name='update_account_all'),
    path('mypage/account_detail/<int:pk>/update_username/', views.UpdateUsernameView.as_view(), name='update_username'),
    path('mypage/account_detail/<int:pk>/update_email/', views.UpdateEmailView.as_view(), name='update_email'),
    path('mypage/account_detail/<int:pk>/update_password/', views.UpdatePasswordView.as_view(), name='update_password'),
    path('mypage/edit_contents_list/', views.EditContentsListView.as_view(), name='edit_contents_list'),
    path('mypage/edit_content/<str:pk>/', views.EditContentView.as_view(),name='edit_content'),
    path('mypage/edit_content/<str:pk>/add_category/', views.AddCategoryView.as_view(),name='add_category'),
    path('mypage/edit_content/<str:pk>/add_tag/', views.AddTagView.as_view(),name='add_tag'),
    path('mypage/edit_contents_list/delete_content/', views.DeleteContentView.as_view(),name='delete_content'),
    path('mypage/comments_list/', views.CommentsListView.as_view(),name='comments_list'),
    path('mypage/comments_list/update_comments_list/', views.UpdateCommentsListView.as_view(),name='update_comments_list'),
    path('mypage/design_customize/', views.DesignCustomizeView.as_view(),name='design_customize'),
    path('mypage/access_analytics/', views.AccessAnalyticsView.as_view(), name='access_analytics'),
    # path('cotegory_list/(?P<category>\w+)/', views.CategoryListView.as_view(), name='category_list'),
    path('cotegory_list/<str>/', views.CategoryListView.as_view(), name='category_list'),
    path('tags_list/<str>/', views.TagsListView.as_view(), name='tags_list'),
]
