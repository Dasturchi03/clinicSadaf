from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.core.api.router import BaseRouter
from apps.user.api import views

app_name = 'user'

router = BaseRouter(trailing_slash=False)
router.register("users", views.UserViewSet, basename="users")

urlpatterns = [
    path('users/doctors', views.DoctorsApiView.as_view(), name='doctors_list'),
    path('users/brief/list', views.UserBriefListView.as_view(), name='user_brief_list'),
    path('users/schedule/list', views.UserSchduleListView.as_view(), name='user_schedule_list'),
    path('users/login/', views.LoginView.as_view(), name='token_obtain_pair'),
    path('users/token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('users/image', views.UserUploadImageView.as_view(), name='upload_image'),

    path('users/<int:pk>/permissions', views.UserPermissionList.as_view(), name='users_perms_list'),
    path('users/<int:pk>/password', views.UserPasswordUpdateView.as_view(), name='password_change'),

    path('users/groups/', views.GroupListView.as_view(), name='group_list'),
    path('users/permissions', views.PermissionAllListView.as_view(), name='perms_all_list'),
    path('users/groups/<int:group_id>/permissions', views.PermissionGroupListView.as_view(), name='perms_all_list'),

    path("users/types", views.UserTypeViewSet.as_view({"get": "list", "post": "create"}), name="users_types"),
    path("users/types/<int:pk>/", views.UserTypeViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"}), name="users_types"),

    path("users/salary/<int:user_id>/list", views.UserSalaryViewSet.as_view({"get": "list"}), name="users_salary"),
    path("users/salary/<int:salary_id>/", views.UserSalaryViewSet.as_view({"get": "retrieve", "delete": "destroy", "patch": "partial_update", "put": "update"}), name="users_salary"),
    path('country_list', views.CountryListView, name='country_list'),

]

urlpatterns += router.urls
