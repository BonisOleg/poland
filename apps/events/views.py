from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.translation import gettext as _

from .content_parser import build_detail_sections
from .models import EventCity, Category, City, AgeGroup


def _filter_year_range():
    y = timezone.now().date().year
    return list(range(y - 1, y + 3))


def _month_choices():
    return [
        (1, _("January")),
        (2, _("February")),
        (3, _("March")),
        (4, _("April")),
        (5, _("May")),
        (6, _("June")),
        (7, _("July")),
        (8, _("August")),
        (9, _("September")),
        (10, _("October")),
        (11, _("November")),
        (12, _("December")),
    ]


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
            "year": request.GET.get("year", ""),
            "month": request.GET.get("month", ""),
            "date": request.GET.get("date", ""),
            "sort": sort,
        },
        "filter_years": _filter_year_range(),
        "month_choices": _month_choices(),
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
    parsed = build_detail_sections(ec)

    return render(request, "events/event_detail.html", {
        "event_city": ec,
        "event": ec.event,
        "related_events": related,
        "reviews": reviews,
        "intro_html": parsed.intro_html,
        "photos": parsed.photos,
        "videos": parsed.videos,
        "blocks": parsed.blocks,
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

    year_str = (request.GET.get("year") or "").strip()
    if year_str:
        try:
            year = int(year_str)
        except ValueError:
            year = None
        if year is not None:
            qs = qs.filter(event_date__isnull=False, event_date__year=year)
            month_str = (request.GET.get("month") or "").strip()
            if month_str:
                try:
                    month = int(month_str)
                except ValueError:
                    month = None
                if month is not None and 1 <= month <= 12:
                    qs = qs.filter(event_date__month=month)
    else:
        date_str = request.GET.get("date")
        if date_str:
            d = parse_date(date_str)
            if d:
                qs = qs.filter(event_date__date=d)

    return qs
