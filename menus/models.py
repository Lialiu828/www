from django.db import models
from tabletap.shops.models import CoffeeShop

class Category(models.Model):
    """菜单分类"""
    shop = models.ForeignKey(CoffeeShop, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    display_order = models.IntegerField(default=0)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name

class Product(models.Model):
    """菜单产品"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    preparation_time = models.PositiveIntegerField(default=5, help_text="Preparation time in minutes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    @property
    def shop(self):
        """返回产品所属的咖啡店"""
        return self.category.shop

class CustomizationOption(models.Model):
    """产品定制选项类型，例如大小、牛奶类型等"""
    name = models.CharField(max_length=50)
    option_type = models.CharField(max_length=50)
    
    def __str__(self):
        return f"{self.option_type}: {self.name}"

class OptionChoice(models.Model):
    """定制选项的具体选择，例如'小杯'、'中杯'、'大杯'"""
    option = models.ForeignKey(CustomizationOption, on_delete=models.CASCADE, related_name='choices')
    name = models.CharField(max_length=50)
    additional_price = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    
    def __str__(self):
        return self.name

class ProductOption(models.Model):
    """产品与定制选项的关联"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='customization_options')
    option = models.ForeignKey(CustomizationOption, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.product.name} - {self.option.name}"