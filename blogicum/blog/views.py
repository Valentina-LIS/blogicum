import datetime

from django.shortcuts import get_object_or_404, render

from .models import Category, Post

NUM_SORT: int = 5


def post_queryset(category_is_published: bool = True):
    return Post.objects.filter(
        is_published=True,
        pub_date__date__lt=datetime.datetime.now(),
        category__is_published=category_is_published
    )


def index(request):
    template = 'blog/index.html'
    post_list = post_queryset()[:NUM_SORT]
    context = {'post_list': post_list}
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
    context = {'category': category,
               'post_list': category_list}
    return render(request, template, context)
