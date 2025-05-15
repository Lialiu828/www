// navigation.js

// 在页面加载时初始化导航栏
function initNavigation() {
    // 检查用户角色并显示相应导航
    const userRole = localStorage.getItem('userRole'); // 假设您在登录时存储了用户角色
    
    // 隐藏所有导航菜单
    document.getElementById('adminNav')?.classList.add('hidden');
    document.getElementById('userNav')?.classList.add('hidden');
    document.getElementById('platformAdminNav')?.classList.add('hidden');
    document.getElementById('guestNav')?.classList.add('hidden');
    
    // 显示相应的导航菜单
    if (userRole === 'admin') {
        document.getElementById('adminNav')?.classList.remove('hidden');
    } else if (userRole === 'platformAdmin') {
        document.getElementById('platformAdminNav')?.classList.remove('hidden');
    } else if (userRole === 'user') {
        document.getElementById('userNav')?.classList.remove('hidden');
    } else {
        // 默认显示访客导航
        document.getElementById('guestNav')?.classList.remove('hidden');
    }
    
    // 高亮当前页面的导航链接
    highlightCurrentPage();
    
    // 初始化移动菜单
    initMobileMenu();
}

// 高亮当前页面的导航链接
function highlightCurrentPage() {
    const currentPage = window.location.pathname.split('/').pop();
    const navLinks = document.querySelectorAll('nav a');
    
    navLinks.forEach(link => {
        const linkPage = link.getAttribute('href');
        if (linkPage === currentPage) {
            link.classList.add('text-coffee-light', 'font-bold');
        }
    });
}

// 初始化移动菜单
function initMobileMenu() {
    const menuToggle = document.getElementById('menuToggle');
    const closeMenu = document.getElementById('closeMenu');
    const mobileMenu = document.getElementById('mobileMenu');
    
    if (menuToggle && mobileMenu && closeMenu) {
        menuToggle.addEventListener('click', function() {
            mobileMenu.classList.remove('hidden');
            populateMobileMenu();
        });
        
        closeMenu.addEventListener('click', function() {
            mobileMenu.classList.add('hidden');
        });
    }
}

// 根据用户角色填充移动菜单
function populateMobileMenu() {
    const mobileMenu = document.getElementById('mobileMenu');
    const menuContent = mobileMenu?.querySelector('.flex.flex-col');
    
    if (!menuContent) return;
    
    menuContent.innerHTML = ''; // 清空现有内容
    
    const userRole = localStorage.getItem('userRole');
    let menuItems = [];
    
    if (userRole === 'admin') {
        menuItems = [
            {text: '仪表盘', href: 'dashborad.html'},
            {text: '菜单管理', href: 'menumanagement.html'},
            {text: '订单管理', href: 'ordermanage.html'},
            {text: '桌位管理', href: 'tablemangement.html'},
            {text: '店铺设置', href: 'storeset.html'},
            {text: '登出', onClick: 'logout()'}
        ];
    } else if (userRole === 'platformAdmin') {
        menuItems = [
            {text: '平台管理', href: 'SaaSPlatformAdmin.html'},
            {text: '仪表盘', href: 'dashborad.html'},
            {text: '登出', onClick: 'logout()'}
        ];
    } else if (userRole === 'user') {
        menuItems = [
            {text: '主页', href: 'index.html'},
            {text: '菜单', href: 'menu.html'},
            {text: '结账', href: 'checkout.html'},
            {text: '登出', onClick: 'logout()'}
        ];
    } else {
        menuItems = [
            {text: '登录', href: 'login.html'},
            {text: '注册', href: 'signup.html'}
        ];
    }
    
    menuItems.forEach(item => {
        if (item.onClick) {
            menuContent.innerHTML += `<button onclick="${item.onClick}" class="py-2">${item.text}</button>`;
        } else {
            menuContent.innerHTML += `<a href="${item.href}" class="py-2">${item.text}</a>`;
        }
    });
}

// 登出函数
function logout() {
    // 清除用户登录信息
    localStorage.removeItem('userRole');
    // 跳转到登录页面
    window.location.href = 'login.html';
}

// 页面加载时初始化导航
document.addEventListener('DOMContentLoaded', initNavigation);