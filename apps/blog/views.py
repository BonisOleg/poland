from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Article


def article_list(request):
    articles = Article.objects.filter(is_published=True)
    paginator = Paginator(articles, 12)
    page = paginator.get_page(request.GET.get("page", 1))
    return render(request, "blog/article_list.html", {"page_obj": page})


def article_detail(request, slug):
    article = get_object_or_404(Article, slug=slug, is_published=True)
    return render(request, "blog/article_detail.html", {"article": article})
