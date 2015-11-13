from content.models import SiteSettings

from .models import Organizer


def front_page_controller(request, page, num_blog_posts=5):
    current_site_settings = request.site.site_settings

    return dict(
        news_posts=current_site_settings.get_visible_blog_posts()[:num_blog_posts],
    )


def organizers_page_controller(request):
    organizers = Organizer.objects.all()

    return dict(
        organizers=organizers,
    )