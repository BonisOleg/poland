from django.shortcuts import render


def homepage(request):
    from apps.events.models import EventCity, Category
    from apps.blog.models import Article

    events = EventCity.objects.filter(
        is_published=True
    ).select_related("event", "city").order_by("-event__sort_order", "event_date")[:15]

    categories = Category.objects.order_by("sort_order")
    articles = Article.objects.filter(is_published=True).order_by("-published_at")[:4]

    return render(request, "homepage.html", {
        "events": events,
        "categories": categories,
        "articles": articles,
    })


def search(request):
    from apps.events.models import EventCity
    q = request.GET.get("q", "").strip()
    results = []
    if len(q) >= 2:
        results = EventCity.objects.filter(
            is_published=True,
        ).filter(
            models_q_search(q)
        ).select_related("event", "city")[:20]

    if request.htmx:
        return render(request, "components/search_results.html", {"results": results, "q": q})
    return render(request, "search.html", {"results": results, "q": q})


def models_q_search(q):
    from django.db.models import Q
    return (
        Q(event__title__icontains=q)
        | Q(city__name__icontains=q)
        | Q(slug__icontains=q)
        | Q(seo_title__icontains=q)
    )
