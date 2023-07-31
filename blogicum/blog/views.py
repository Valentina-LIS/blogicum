import datetime

from django.shortcuts import get_object_or_404, render

from django.http import Http404

from django.views.generic import ListView, UpdateView, CreateView

from django.contrib.auth.mixins import LoginRequiredMixin

from django.contrib.auth.models import User

from django.core.paginator import Paginator

from django.urls import reverse, reverse_lazy

from .models import Category, Post
from .forms import PostForm


PAGINATOR_VALUE: int = 10
PAGE_NUMBER = "page"


def post_queryset(category_is_published: bool = True):
    return Post.objects.filter(
        is_published=True,
        pub_date__date__lt=datetime.datetime.now(),
        category__is_published=category_is_published
    )


def index(request):
    template = 'blog/index.html'
    post_list = post_queryset()
    paginator = Paginator(post_list, PAGINATOR_VALUE)
    page_number = request.GET.get(PAGE_NUMBER)
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(request, template, context)


def post_detail(request, id):
    template = 'blog/detail.html'
    post = get_object_or_404(
        post_queryset().select_related(
            'category'
        ).filter(id=id)
    )
    context = {'post': post}
    return render(request, template, context)


def category_posts(request, category_slug):
    template = 'blog/category.html'
    category = get_object_or_404(Category,
                                 slug=category_slug,
                                 is_published=True)
    category_list = post_queryset().filter(category__slug=category_slug)
    paginator = Paginator(category_list, PAGINATOR_VALUE)
    page_number = request.GET.get(PAGE_NUMBER)
    page_obj = paginator.get_page(page_number)
    context = {'category': category,
               'page_obj': page_obj}
    return render(request, template, context)


class ProfileListView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'blog/profile.html'
    ordering = 'id'
    paginate_by = 10

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        username = self.kwargs['username']
        try:
            profile = User.objects.get(username=username)
        except User.DoesNotExist:
            raise Http404
        return Post.objects.filter(author=profile
                                   ).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile"] = User.objects.get(username=self.kwargs['username'])
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'blog/user.html'
    fields = ['first_name', 'last_name', 'username', 'email']
    success_url = reverse_lazy('blog:profile')

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse('blog:profile', kwargs={
            'username': self.request.user.username})


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = "blog/create.html"

    def get_success_url(self):
        return reverse('blog:profile', kwargs={
            'username': self.request.user.username})

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
