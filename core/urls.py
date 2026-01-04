from django.urls import path
from .views import (
    RegisterView,
    handle_api,
    handle_image,
    SignInView,
    profile_view,
    CustomTokenObtainPairView
    )
from rest_framework_simplejwt.views import (
    TokenRefreshView
)


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('signin/', SignInView.as_view(), name='signin'),
    path("profile_view/", profile_view, name="profile_view"),
    path("handle_api/", handle_api, name="handle_api"),
    path("image/", handle_image, name="handle_image"),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
]


