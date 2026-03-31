from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from apps.events.models import EventCity
from .models import Review


@require_POST
def add_review(request, event_city_id):
    ec = get_object_or_404(EventCity, pk=event_city_id, is_published=True)
    author = request.POST.get("author_name", "").strip()
    content = request.POST.get("content", "").strip()
    rating = request.POST.get("rating", 5)

    errors = {}
    if not author:
        errors["author_name"] = "Podaj imię"
    if not content:
        errors["content"] = "Napisz recenzję"

    if errors:
        return render(request, "reviews/partials/review_form.html", {
            "event_city": ec,
            "errors": errors,
        })

    Review.objects.create(
        event_city=ec,
        author_name=author[:200],
        content=content[:2000],
        rating=int(rating),
    )

    return render(request, "reviews/partials/review_success.html", {
        "event_city": ec,
    })
