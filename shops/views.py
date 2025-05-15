from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import timedelta
import json
import qrcode
from io import BytesIO

# 导入模型
from tabletap.shops.models import CoffeeShop, Table, Subscription
from tabletap.menus.models import Category, Product
from tabletap.orders.models import Order, OrderItem

# 基本页面视图
def index(request):
    """首页视图，显示主页"""
    return render(request, 'shops/index.html')

def welcome(request):
    """欢迎页面视图，展示平台介绍"""
    return render(request, 'shops/welcome.html')

# 用户认证视图
def login_view(request):
    """用户登录视图"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # 根据用户类型重定向到不同页面
            if user.is_staff:
                return redirect('dashboard')
            else:
                return redirect('index')
        else:
            # 登录失败
            context = {'error': '用户名或密码不正确'}
            return render(request, 'shops/login.html', context)
    
    return render(request, 'shops/login.html')

def signup_view(request):
    """用户注册视图"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # 表单验证
        if password1 != password2:
            return render(request, 'shops/signup.html', {'error': '两次密码不匹配'})
        
        if User.objects.filter(username=username).exists():
            return render(request, 'shops/signup.html', {'error': '用户名已存在'})
        
        if User.objects.filter(email=email).exists():
            return render(request, 'shops/signup.html', {'error': '电子邮件已被使用'})
        
        # 创建用户
        user = User.objects.create_user(username=username, email=email, password=password1)
        
        # 自动登录
        login(request, user)
        return redirect('dashboard')
    
    return render(request, 'shops/signup.html')

def logout_view(request):
    """用户注销处理"""
    logout(request)
    return redirect('index')

# 顾客功能视图
def menu(request):
    """菜单页面，显示商品列表"""
    # 获取URL参数中的桌号
    table_number = request.GET.get('table', None)
    
    # 在实际应用中，你需要确定当前访问的是哪家咖啡店
    # 这里简单假设使用第一家咖啡店
    shop = CoffeeShop.objects.first()
    
    if not shop:
        return render(request, 'shops/menu.html', {'menu_items': []})
    
    # 获取该咖啡店的所有商品
    categories = Category.objects.filter(shop=shop)
    menu_items = Product.objects.filter(category__shop=shop, is_available=True)
    
    context = {
        'table_number': table_number,
        'categories': categories,
        'menu_items': menu_items,
        'shop': shop
    }
    
    return render(request, 'shops/menu.html', context)

def checkout(request):
    """结账页面，处理订单提交"""
    # 获取URL参数中的桌号
    table_number = request.GET.get('table', None)
    
    # 如果提供了桌号，尝试获取对应的桌位
    table = None
    if table_number:
        table = Table.objects.filter(table_number=table_number).first()
    
    # 获取最近的几个订单作为示例显示
    recent_orders = []
    if table:
        shop = table.shop
        recent_orders = Order.objects.filter(shop=shop).order_by('-order_time')[:5]
    
    context = {
        'table_number': table_number,
        'table': table,
        'recent_orders': recent_orders
    }
    
    return render(request, 'shops/checkout.html', context)

@csrf_exempt
def submit_order(request):
    """API端点：提交订单"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        data = json.loads(request.body)
        table_number = data.get('table_number')
        customer_name = data.get('customer_name')
        special_instructions = data.get('special_instructions', '')
        items = data.get('items', [])
        
        # 验证数据
        if not items:
            return JsonResponse({'success': False, 'error': 'No items in order'})
        
        # 找到桌位和商店
        table = Table.objects.filter(table_number=table_number).first() if table_number else None
        
        # 如果没有找到桌位，使用第一家咖啡店作为默认值
        if table:
            shop = table.shop
        else:
            shop = CoffeeShop.objects.first()
        
        if not shop:
            return JsonResponse({'success': False, 'error': 'Shop not found'})
        
        # 创建订单
        order = Order.objects.create(
            shop=shop,
            table=table,
            customer_name=customer_name,
            status='new',
            special_instructions=special_instructions
        )
        
        # 计算总价格
        total_price = 0
        
        # 添加订单项目
        for item_data in items:
            product_id = item_data.get('product_id')
            quantity = item_data.get('quantity', 1)
            
            try:
                product = Product.objects.get(id=product_id)
                item_price = product.price * quantity
                total_price += item_price
                
                order_item = OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    item_price=item_price
                )
                
                # 处理定制选项（如果有）
                customizations = item_data.get('customizations', [])
                for custom in customizations:
                    pass  # 处理定制选项逻辑
            except Product.DoesNotExist:
                # 如果产品不存在，仍然继续处理其他产品
                continue
        
        # 更新订单总价
        order.total_price = total_price
        order.save()
        
        return JsonResponse({
            'success': True, 
            'order_id': order.id,
            'message': 'Order created successfully'
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# 管理员功能视图
@login_required
def dashboard(request):
    """管理员仪表板，显示概览数据"""
    # 获取当前用户的咖啡店
    shop = CoffeeShop.objects.filter(owner=request.user).first()
    
    if not shop:
        # 如果用户还没有咖啡店，创建一个示例店铺
        shop = CoffeeShop.objects.create(
            owner=request.user,
            name="My Coffee Shop",
            description="A sample coffee shop",
        )
    
    # 准备日期范围 - 最近7天
    today = timezone.now().date()
    start_date = today - timedelta(days=6)  # 7天前
    
    # 初始化数据
    total_orders = 0
    total_sales = 0
    active_tables = 0
    total_tables = 0
    active_tables_percentage = 0
    orders_change = 0
    sales_change = 0
    new_customers = 0
    customers_change = 0
    recent_orders = []
    
    # 获取统计数据
    total_orders = Order.objects.filter(shop=shop).count()
    completed_orders = Order.objects.filter(shop=shop, status='completed')
    total_sales = completed_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
    
    # 获取表格统计数据
    total_tables = Table.objects.filter(shop=shop).count()
    active_tables = Table.objects.filter(shop=shop, is_active=True).count()
    if total_tables > 0:
        active_tables_percentage = round((active_tables / total_tables) * 100)
    
    # 准备销售趋势数据
    daily_sales = []
    daily_labels = []
    
    for i in range(7):
        date = start_date + timedelta(days=i)
        daily_labels.append(date.strftime('%a'))  # 星期几缩写
        
        # 获取当天销售额
        day_orders = Order.objects.filter(
            shop=shop,
            status='completed',
            order_time__date=date
        )
        day_sales = day_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
        daily_sales.append(float(day_sales))
    
    # 订单类型分布
    order_distribution_labels = ['New', 'Preparing', 'Ready', 'Completed']
    order_distribution_data = []
    
    for status in ['new', 'preparing', 'ready', 'completed']:
        count = Order.objects.filter(shop=shop, status=status).count()
        order_distribution_data.append(count)
    
    # 获取最近的订单
    recent_orders = Order.objects.filter(shop=shop).order_by('-order_time')[:5]
    
    # 获取订阅信息
    subscription = Subscription.objects.filter(shop=shop).first()
    
    context = {
        'shop': shop,
        'total_orders': total_orders,
        'total_sales': total_sales,
        'active_tables': active_tables,
        'total_tables': total_tables,
        'active_tables_percentage': active_tables_percentage,
        'recent_orders': recent_orders,
        'new_customers': new_customers,
        'customers_change': customers_change,
        'orders_change': orders_change,
        'sales_change': sales_change,
        'subscription': subscription,
        
        # 图表数据
        'sales_labels': json.dumps(daily_labels),
        'sales_data': json.dumps(daily_sales),
        'order_distribution_labels': json.dumps(order_distribution_labels),
        'order_distribution_data': json.dumps(order_distribution_data),
    }
    
    return render(request, 'shops/dashboard.html', context)

@login_required
def menu_management(request):
    """菜单管理页面，处理菜单项CRUD"""
    # 获取当前用户的咖啡店
    shop = CoffeeShop.objects.filter(owner=request.user).first()
    
    if not shop:
        return redirect('welcome')
    
    # 获取分类和产品
    categories = Category.objects.filter(shop=shop)
    products = Product.objects.filter(category__shop=shop)
    
    context = {
        'shop': shop,
        'categories': categories,
        'products': products
    }
    
    return render(request, 'shops/menumanagement.html', context)

@login_required
def order_manage(request):
    """订单管理页面，处理订单状态更新"""
    # 获取当前用户的咖啡店
    shop = CoffeeShop.objects.filter(owner=request.user).first()
    
    if not shop:
        return redirect('welcome')
    
    # 获取订单，按状态分类
    new_orders = Order.objects.filter(shop=shop, status='new').order_by('-order_time')
    preparing_orders = Order.objects.filter(shop=shop, status='preparing').order_by('-order_time')
    ready_orders = Order.objects.filter(shop=shop, status='ready').order_by('-order_time')
    completed_orders = Order.objects.filter(shop=shop, status='completed').order_by('-order_time')[:10]
    
    context = {
        'shop': shop,
        'new_orders': new_orders,
        'preparing_orders': preparing_orders,
        'ready_orders': ready_orders,
        'completed_orders': completed_orders
    }
    
    return render(request, 'shops/ordermanage.html', context)

@login_required
def table_management(request):
    """桌位管理页面，处理桌位CRUD和QR码生成"""
    # 获取当前用户的咖啡店
    shop = CoffeeShop.objects.filter(owner=request.user).first()
    
    if not shop:
        return redirect('welcome')
    
    # 获取桌位
    tables = Table.objects.filter(shop=shop)
    
    context = {
        'shop': shop,
        'tables': tables
    }
    
    return render(request, 'shops/tablemanagement.html', context)

@login_required
def store_settings(request):
    """商店设置页面，处理商店信息更新"""
    # 获取当前用户的商店信息
    shop = CoffeeShop.objects.filter(owner=request.user).first()
    
    if not shop:
        return redirect('welcome')
    
    if request.method == 'POST':
        # 处理表单提交
        shop.name = request.POST.get('shop-name', shop.name)
        shop.description = request.POST.get('description', shop.description)
        shop.address = request.POST.get('address', shop.address)
        shop.phone = request.POST.get('phone', shop.phone)
        shop.working_hours = request.POST.get('working-hours', shop.working_hours)
        
        # 处理logo上传
        if 'logo' in request.FILES:
            shop.logo = request.FILES['logo']
        
        shop.save()
        return redirect('store_settings')
    
    # 获取订阅信息
    subscription = Subscription.objects.filter(shop=shop).first()
    
    context = {
        'shop': shop,
        'subscription': subscription
    }
    
    return render(request, 'shops/storeset.html', context)

@login_required
def saas_platform_admin(request):
    """SaaS平台管理页面，处理订阅管理"""
    # 检查用户是否是平台管理员
    if not request.user.is_staff:
        return redirect('dashboard')
    
    # 获取所有订阅
    shops = CoffeeShop.objects.all().select_related('owner')
    subscriptions = Subscription.objects.all().select_related('shop', 'user')
    
    context = {
        'shops': shops,
        'subscriptions': subscriptions
    }
    
    return render(request, 'shops/SaaSPlatformAdmin.html', context)

# API端点
@csrf_exempt
@login_required
def update_order_status(request, order_id):
    """更新订单状态的API端点"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            status = data.get('status')
            
            # 获取当前用户的咖啡店
            shop = CoffeeShop.objects.filter(owner=request.user).first()
            
            if not shop:
                return JsonResponse({'success': False, 'error': 'Shop not found'})
            
            # 获取订单并验证它属于当前商店
            order = Order.objects.get(id=order_id, shop=shop)
            
            # 更新状态
            order.status = status
            if status == 'completed':
                order.completed_time = timezone.now()
            order.save()
            
            return JsonResponse({'success': True})
        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Order not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
@login_required
def add_table(request):
    """添加桌位的API端点"""
    if request.method == 'POST':
        try:
            # 获取当前用户的咖啡店
            shop = CoffeeShop.objects.filter(owner=request.user).first()
            
            if not shop:
                return JsonResponse({'success': False, 'error': 'Shop not found'})
            
            # 处理表单数据
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                table_number = data.get('table_number')
                seats = data.get('seats', 2)
                location = data.get('location', '')
            else:
                table_number = request.POST.get('table_number')
                seats = request.POST.get('seats', 2)
                location = request.POST.get('location', '')
                
            # 创建新桌位
            table = Table.objects.create(
                shop=shop,
                table_number=table_number,
                seats=seats,
                location=location,
                is_active=True
            )
            
            # 生成QR码URL
            domain = request.build_absolute_uri('/').rstrip('/')
            table.qr_code_url = f"{domain}/menu/?table={table.table_number}"
            table.save()
            
            return JsonResponse({
                'success': True,
                'table_id': table.id,
                'qr_code_url': table.qr_code_url
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
@login_required
def delete_table(request, table_id):
    """删除桌位的API端点"""
    if request.method == 'POST':
        try:
            # 获取当前用户的咖啡店
            shop = CoffeeShop.objects.filter(owner=request.user).first()
            
            if not shop:
                return JsonResponse({'success': False, 'error': 'Shop not found'})
            
            # 获取桌位并验证它属于当前商店
            table = Table.objects.get(id=table_id, shop=shop)
            
            # 删除桌位
            table.delete()
            
            return JsonResponse({'success': True})
        except Table.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Table not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def generate_qr(request, table_id):
    """为桌位生成QR码的API端点"""
    try:
        # 获取当前用户的咖啡店
        shop = CoffeeShop.objects.filter(owner=request.user).first()
        
        if not shop:
            return HttpResponse("Shop not found", status=404)
        
        # 获取桌位
        table = Table.objects.get(id=table_id, shop=shop)
        
        # 生成QR码的URL
        domain = request.build_absolute_uri('/').rstrip('/')
        qr_data = f"{domain}/menu/?table={table.table_number}"
        
        # 生成QR码
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 返回QR码图像
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        return HttpResponse(buffer, content_type="image/png")
    except Table.DoesNotExist:
        return HttpResponse("Table not found", status=404)
    except Exception as e:
        return HttpResponse(str(e), status=500)

# 产品管理API端点
@csrf_exempt
@login_required
def add_product(request):
    """添加产品的API端点"""
    if request.method == 'POST':
        try:
            # 获取当前用户的咖啡店
            shop = CoffeeShop.objects.filter(owner=request.user).first()
            
            if not shop:
                return JsonResponse({'success': False, 'error': 'Shop not found'})
            
            # 处理表单数据
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                name = data.get('name')
                category_id = data.get('category_id')
                price = data.get('price')
                description = data.get('description', '')
                is_available = data.get('is_available', True)
                
                # 验证分类是否属于当前商店
                category = Category.objects.get(id=category_id, shop=shop)
                
                # 创建产品
                product = Product.objects.create(
                    category=category,
                    name=name,
                    price=price,
                    description=description,
                    is_available=is_available
                )
                
                return JsonResponse({
                    'success': True,
                    'product_id': product.id,
                    'message': 'Product added successfully'
                })
            else:
                # 处理multipart/form-data（包含图片上传）
                name = request.POST.get('name')
                category_id = request.POST.get('category_id')
                price = request.POST.get('price')
                description = request.POST.get('description', '')
                is_available = request.POST.get('is_available', 'true') == 'true'
                
                # 验证分类是否属于当前商店
                category = Category.objects.get(id=category_id, shop=shop)
                
                # 创建产品
                product = Product.objects.create(
                    category=category,
                    name=name,
                    price=price,
                    description=description,
                    is_available=is_available
                )
                
                # 处理图片上传
                if 'image' in request.FILES:
                    product.image = request.FILES['image']
                    product.save()
                
                return JsonResponse({
                    'success': True,
                    'product_id': product.id,
                    'message': 'Product added successfully'
                })
        
        except Category.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Category not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
@login_required
def edit_product(request, product_id):
    """编辑产品的API端点"""
    if request.method == 'POST':
        try:
            # 获取当前用户的咖啡店
            shop = CoffeeShop.objects.filter(owner=request.user).first()
            
            if not shop:
                return JsonResponse({'success': False, 'error': 'Shop not found'})
            
            # 获取产品并验证它属于当前商店
            product = Product.objects.get(id=product_id, category__shop=shop)
            
            # 处理表单数据
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                name = data.get('name', product.name)
                category_id = data.get('category_id')
                price = data.get('price', product.price)
                description = data.get('description', product.description)
                is_available = data.get('is_available', product.is_available)
                
                # 更新分类（如果提供了）
                if category_id:
                    category = Category.objects.get(id=category_id, shop=shop)
                    product.category = category
                
                # 更新产品信息
                product.name = name
                product.price = price
                product.description = description
                product.is_available = is_available
                product.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Product updated successfully'
                })
            else:
                # 处理multipart/form-data（包含图片上传）
                name = request.POST.get('name', product.name)
                category_id = request.POST.get('category_id')
                price = request.POST.get('price', product.price)
                description = request.POST.get('description', product.description)
                is_available = request.POST.get('is_available', 'true') == 'true'
                
                # 更新分类（如果提供了）
                if category_id:
                    category = Category.objects.get(id=category_id, shop=shop)
                    product.category = category
                
                # 更新产品信息
                product.name = name
                product.price = price
                product.description = description
                product.is_available = is_available
                
                # 处理图片上传
                if 'image' in request.FILES:
                    product.image = request.FILES['image']
                
                product.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Product updated successfully'
                })
        
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Product not found'})
        except Category.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Category not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
@login_required
def delete_product(request, product_id):
    """删除产品的API端点"""
    if request.method == 'POST':
        try:
            # 获取当前用户的咖啡店
            shop = CoffeeShop.objects.filter(owner=request.user).first()
            
            if not shop:
                return JsonResponse({'success': False, 'error': 'Shop not found'})
            
            # 获取产品并验证它属于当前商店
            product = Product.objects.get(id=product_id, category__shop=shop)
            
            # 删除产品
            product.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Product deleted successfully'
            })
        
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Product not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})