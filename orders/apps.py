from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tabletap.orders'
    verbose_name = 'Order Management'
    
    def ready(self):
        """
        应用初始化时运行的方法
        可以在这里注册信号处理器等
        """
        # 导入信号处理器（如果有）
        # import tabletap.orders.signals
        pass