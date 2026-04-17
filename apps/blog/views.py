from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator

from apps.pages.utils import extract_media_from_html
from .models import Article


def article_list(request):
    articles = Article.objects.filter(is_published=True)
    paginator = Paginator(articles, 12)
    page_obj = paginator.get_page(request.GET.get("page", 1))
    return render(request, "blog/article_list.html", {
        "page_obj": page_obj,
        "breadcrumbs": [{"title": "Aktualności", "url": None}],
    })


def article_detail(request, slug):
    article = get_object_or_404(Article, slug=slug, is_published=True)
    images, videos, content_html = extract_media_from_html(article.content)
    breadcrumbs = [
        {"title": "Aktualności", "url": "/aktualnosci/"},
        {"title": article.title, "url": None},
    ]
    return render(request, "blog/article_detail.html", {
        "article": article,
        "images": images,
        "videos": videos,
        "content_html": content_html,
        "breadcrumbs": breadcrumbs,
    })
