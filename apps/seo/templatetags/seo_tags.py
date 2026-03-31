from django import template

register = template.Library()


@register.inclusion_tag("includes/breadcrumbs.html")
def render_breadcrumbs(*crumbs):
    breadcrumbs = []
    for i in range(0, len(crumbs), 2):
        title = crumbs[i]
        url = crumbs[i + 1] if i + 1 < len(crumbs) else None
        breadcrumbs.append({"title": title, "url": url})
    return {"breadcrumbs": breadcrumbs}
