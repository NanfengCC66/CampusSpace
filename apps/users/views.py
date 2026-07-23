from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView, TemplateView
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm, CustomAuthenticationForm


class HomeView(TemplateView):
    """首页视图"""
    template_name = 'home.html'


class RegisterView(CreateView):
    """用户注册视图"""
    form_class = CustomUserCreationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('users:login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, '注册成功！请登录。')
        return response


def login_view(request):
    """用户登录视图"""
    if request.user.is_authenticated:
        return redirect('users:home')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'欢迎回来，{user.first_name or user.username}！')
            
            # 获取next参数，登录后跳转
            next_url = request.GET.get('next', 'users:home')
            return redirect(next_url)
        else:
            messages.error(request, '用户名或密码错误！')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'users/login.html', {'form': form})


@login_required
def logout_view(request):
    """用户登出视图"""
    logout(request)
    messages.info(request, '您已成功退出登录！')
    return redirect('users:home')