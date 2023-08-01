import datetime

from django.contrib.auth.decorators import login_required

from django.shortcuts import get_object_or_404, render, redirect

from django.http import Http404

from django.views.generic import (
    ListView, UpdateView, CreateView, DeleteView
)

from django.contrib.auth.mixins import LoginRequiredMixin

from django.contrib.auth.models import User

from django.db.models import Count, Prefetch

from django.core.paginator import Paginator

from django.urls import reverse, reverse_lazy

from .models import Category, Post, Comment
from .forms import PostForm, CommentForm


PAGINATOR_VALUE: int = 10
PAGE_NUMBER = "page"


def post_queryset(category_is_published: bool = True):
    return Post.objects.filter(
        is_published=True,
        pub_date__date__lt=datetime.datetime.now(),
        category__is_published=category_is_published
    ).order_by('-pub_date')


@login_required
def index(request):
    template = 'blog/index.html'
    post_list = post_queryset().annotate(comment_count=Count("comments"))
    paginator = Paginator(post_list, PAGINATOR_VALUE)
    page_number = request.GET.get(PAGE_NUMBER)
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(request, template, context)


@login_required
def post_detail(request, id):
    template = 'blog/detail.html'
    post = get_object_or_404(
        post_queryset().select_related(
            'category'
        ).filter(id=id)
    )
    context = {'post': post,
               'form': CommentForm(),
               'comments': Comment.objects.filter(post_id=id)}
    return render(request, template, context)


@login_required
def category_posts(request, category_slug):
    template = 'blog/category.html'
    category = get_object_or_404(
        Category.objects.prefetch_related(
            Prefetch(
                'posts',
                post_queryset()
                .annotate(comment_count=Count('comments')),
            )
        ).filter(slug=category_slug),
        is_published=True,
    )
    category_list = category.posts.all().filter(category__slug=category_slug)
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
                                   ).order_by('-pub_date').annotate(
                                    comment_count=Count("comments"))

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


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    template_name = 'blog/create.html'
    form_class = PostForm
    success_url = reverse_lazy('blog:post_detail')

    def dispatch(self, request, *args, **kwargs):
        post = get_object_or_404(Post, pk=kwargs['pk'])
        if post.author != request.user:
            return redirect('blog:post_detail', pk=self.kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={
            'id': self.kwargs['pk']})

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')


class CommentCreateView(LoginRequiredMixin, CreateView):
    object = None
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    success_url = reverse_lazy('blog:post_detail')

    # Переопределяем dispatch()
    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(Post, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    # Переопределяем form_valid()
    def form_valid(self, form):
        form.instance.author = self.request.user
        post_id = self.kwargs['pk']
        post = get_object_or_404(Post, id=post_id)
        form.instance.post = post
        return super().form_valid(form)

    # Переопределяем get_success_url()
    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={
            'id': self.kwargs['pk']})


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    pk_url_kwarg = 'comment_id'
    template_name = 'blog/comment.html'
    success_url = reverse_lazy('blog:post_detail')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        comment = self.get_object()
        if comment.author != request.user:
            return redirect('blog:post_detail', pk=comment.post_id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={
            'id': self.kwargs['pk']})


class CommentDeletelView(LoginRequiredMixin, DeleteView):
    model = Comment
    pk_url_kwarg = 'comment_id'
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        comment = self.get_object()
        if comment.author != request.user:
            return redirect('blog:post_detail', pk=comment.post_id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={
            'id': self.kwargs['pk']})
