from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class CoffeeShop(models.Model):
    """咖啡店模型 - 用于多租户SaaS平台"""
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coffee_shops')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='shop_logos/', blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    working_hours = models.CharField(max_length=100, blank=True, null=True)
    theme_settings = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Subscription(models.Model):
    """订阅模型 - 跟踪SaaS订阅状态"""
    PLAN_CHOICES = [
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    shop = models.OneToOneField(CoffeeShop, on_delete=models.CASCADE, related_name='subscription')
    plan_type = models.CharField(max_length=20, choices=PLAN_CHOICES, default='basic')
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    payment_status = models.CharField(max_length=20, default='paid')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.shop.name} - {self.plan_type}"

class Table(models.Model):
    """咖啡店桌位"""
    shop = models.ForeignKey(CoffeeShop, on_delete=models.CASCADE, related_name='tables')
    table_number = models.CharField(max_length=10)
    seats = models.PositiveIntegerField(default=2)
    location = models.CharField(max_length=50, blank=True, null=True)
    qr_code_url = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Table {self.table_number} ({self.shop.name})"