from django.urls import path
from . import views

urlpatterns = [
    # 基本页面
    path('', views.index, name='index'),
    path('welcome/', views.welcome, name='welcome'),
    
    # 用户认证
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    
    # 顾客功能
    path('menu/', views.menu, name='menu'),
    path('checkout/', views.checkout, name='checkout'),
    
    # 管理功能
    path('dashboard/', views.dashboard, name='dashboard'),
    path('menumanagement/', views.menu_management, name='menu_management'),
    path('ordermanage/', views.order_manage, name='order_manage'),
    path('tablemanagement/', views.table_management, name='table_management'),
    path('storesettings/', views.store_settings, name='store_settings'),
    
    # 平台管理
    path('saasplatformadmin/', views.saas_platform_admin, name='saas_platform_admin'),
    
    # API端点
    path('api/update-order/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('api/add-table/', views.add_table, name='add_table'),
    path('api/delete-table/<int:table_id>/', views.delete_table, name='delete_table'),
    path('api/generate-qr/<int:table_id>/', views.generate_qr, name='generate_qr'),
    path('api/add-product/', views.add_product, name='add_product'),
    path('api/edit-product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('api/delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
]