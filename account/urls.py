from django.urls import path
from account.views import UserRegistrationView, UserLoginView, UserProfileView, UserChangePasswordView, SendPasswordResetEmailView, UserPasswordResetView, FileUploadView, FileListView, FileView, FileDelete, FileUpdateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('upload/', FileUploadView.as_view(), name='file-upload'),
    path('files/', FileListView.as_view(), name='file-list'),
    path('files/<int:file_id>/', FileView.as_view(), name='file-view'),
    path('files/<int:file_id>/delete/', FileDelete.as_view(), name='file-delete'),
    path('files/update/<int:file_id>/', FileUpdateView.as_view(), name='file-update'),

    path('profile/', UserProfileView.as_view(), name='profile'),
    path('changepassword/', UserChangePasswordView.as_view(), name='changepassword'),
    path('send-reset-password-email/', SendPasswordResetEmailView.as_view(), name='send-reset-password-email'),
    path('reset-password/<uid>/<token>/', UserPasswordResetView.as_view(), name='reset-password'),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
