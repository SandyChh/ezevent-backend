from django.urls import path
from .admin_views import user_list, user_suspend

urlpatterns = [
    path("users/", user_list, name="admin-user-list"),
    path("users/<int:pk>/suspend/", user_suspend, name="admin-user-suspend"),
]
