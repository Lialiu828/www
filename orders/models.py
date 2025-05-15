from django.db import models
from django.utils import timezone
from tabletap.shops.models import CoffeeShop, Table
from tabletap.menus.models import Product, CustomizationOption, OptionChoice

class Order(models.Model):
    """订单"""
    STATUS_CHOICES = [
        ('new', 'New'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    shop = models.ForeignKey(CoffeeShop, on_delete=models.CASCADE, related_name='orders')
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    order_time = models.DateTimeField(auto_now_add=True)
    completed_time = models.DateTimeField(blank=True, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    special_instructions = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Order #{self.id} - {self.status}"
    
    def save(self, *args, **kwargs):
        # 如果状态改为completed，设置完成时间
        if self.status == 'completed' and not self.completed_time:
            self.completed_time = timezone.now()
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    """订单项目"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    item_price = models.DecimalField(max_digits=10, decimal_places=2)  # 保存下单时的价格
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

class OrderItemCustomization(models.Model):
    """订单项目定制"""
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='customizations')
    option = models.ForeignKey(CustomizationOption, on_delete=models.CASCADE)
    choice = models.ForeignKey(OptionChoice, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.order_item.product.name} - {self.option.name}: {self.choice.name}"