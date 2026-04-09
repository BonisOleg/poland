from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import EventCity, Category, City, AgeGroup


def event_list(request):
    events = EventCity.objects.filter(
        is_published=True
    ).select_related("event", "city")

    cities = City.objects.all()
    categories = (
        Category.objects
        .filter(events__event_cities__is_published=True)
        .distinct()
        .order_by("sort_order", "name")
    )
    age_groups = (
        AgeGroup.objects
        .filter(events__event_cities__is_published=True)
        .distinct()
        .order_by("min_age")
    )

    events = _apply_filters(events, request)

    sort = request.GET.get("sort", "date")
    if sort == "date":
        events = events.order_by("event_date")
    elif sort == "popular":
        events = events.order_by("-event__sort_order")

    paginator = Paginator(events, 18)
    page = paginator.get_page(request.GET.get("page", 1))

    ctx = {
        "page_obj": page,
        "cities": cities,
        "categories": categories,
        "age_groups": age_groups,
        "current_filters": {
            "city": request.GET.get("city", ""),
            "category": request.GET.get("category", ""),
            "age": request.GET.get("age", ""),
            "date": request.GET.get("date", ""),
            "sort": sort,
        },
    }

    if request.htmx:
        return render(request, "events/partials/event_grid.html", ctx)
    return render(request, "events/event_list.html", ctx)


def event_filter(request):
    events = EventCity.objects.filter(
        is_published=True
    ).select_related("event", "city")
    events = _apply_filters(events, request)

    sort = request.GET.get("sort", "date")
    if sort == "date":
        events = events.order_by("event_date")
    elif sort == "popular":
        events = events.order_by("-event__sort_order")

    paginator = Paginator(events, 18)
    page = paginator.get_page(request.GET.get("page", 1))

    return render(request, "events/partials/event_grid.html", {
        "page_obj": page,
    })


def event_detail(request, slug):
    ec = get_object_or_404(
        EventCity.objects.select_related("event", "city", "venue"),
        slug=slug,
        is_published=True,
    )
    related = ec.get_related_events(6)
    reviews = ec.reviews.filter(is_approved=True)[:10]

    return render(request, "events/event_detail.html", {
        "event_city": ec,
        "event": ec.event,
        "related_events": related,
        "reviews": reviews,
    })


def _apply_filters(qs, request):
    city = request.GET.get("city")
    if city:
        qs = qs.filter(city__slug=city)

    category = request.GET.get("category")
    if category:
        qs = qs.filter(event__categories__slug=category)

    age = request.GET.get("age")
    if age:
        qs = qs.filter(event__age_group__slug=age)

    date_str = request.GET.get("date")
    if date_str:
        from django.utils.dateparse import parse_date
        d = parse_date(date_str)
        if d:
            qs = qs.filter(event_date__date=d)

    return qs
