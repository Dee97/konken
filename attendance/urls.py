from django.urls import path

# from rest_framework.urlpatterns import format_suffix_patterns

from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token

from attendance import views

urlpatterns = [
    path('', views.IndexTemplateView.as_view(), name="index"),
    
    path('timeout', views.TimeoutPage.as_view(), name="timeout-page"),
    
    path('attendance/list/<int:id>/', views.AttendancePage.as_view(), name='attendance_list'),
    path('attendance/list/<int:id>/<str:token>/', views.AttendancePage.as_view(), name='attendance_list'),

    path('view/linked/<str:token>', views.AttendanceStudentList.as_view(), name='student-list'),
    path('register/user', views.UserRegister.as_view(), name='user-register'),

    path('user/import/', views.UserImport.as_view(), name='user-import'),
    path('users/', views.UserList.as_view(), name='user-list' ),
    path('user/', views.UserDetail.as_view(), name='user-detail'),
    path('user/<str:id>/', views.UserDetail.as_view(), name='user-detail'),
    
    path('api/token/', obtain_jwt_token),
    path('api/token/refresh-it/', refresh_jwt_token),
    
    path('card/',views.CardScan.as_view(), name='card'),
    path('card/<str:short_name>',views.CardScan.as_view(), name='card'),
    
    path('holiday/import/', views.HolidaysImport.as_view(), name='holidays-import'),
    path('holiday/', views.HolidaysApi.as_view(), name='holiday'),
    path('holiday/<int:id>/', views.HolidaysApi.as_view(), name='holiday'),
    path('holidays-page/', views.HolidaysPage.as_view(), name='holidays-list'),

    # path('schools-page/', views.SchoolsPage.as_view(), name='schools-list'),
    # path('school/', views.SchoolsApi.as_view(), name='school'),
    # path('school<str:id>/', views.SchoolsApi.as_view(), name='school'),

    # path('user/import/', views.UserImport.as_view(), name='user-import'),
    path('schools-page/', views.SchoolList.as_view(), name='schools-list' ),
    path('school/<str:code>/', views.SchoolDetail.as_view(), name='school-detail'),
    path('school/', views.SchoolDetail.as_view(), name='school'),
    
    path('attendance-export/', views.AttendanceExport.as_view(), name='attendance-export'),
    path('attendance-export/<int:id>/', views.AttendanceExport.as_view(), name='attendance-export'),
    
    path('change-password', views.PasswordChange.as_view(), name="change-password"),
   
    path('card-logs', views.CardLogsView.as_view(), name="card-logs")
]