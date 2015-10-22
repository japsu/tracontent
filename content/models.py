# encoding: utf-8

from collections import namedtuple

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.core.validators import RegexValidator
from django.db import models
from django.shortcuts import render
from django.utils.timezone import now
from django.template.loader import get_template

import bleach

from .utils import slugify, pick_attrs, format_emails, get_code


validate_slug = RegexValidator(
    regex=r'[a-z0-9-]+',
    message=u'Tekninen nimi saa sisältää vain pieniä kirjaimia, numeroita sekä väliviivoja.'
)

validate_path = RegexValidator(
    regex=r'[a-z0-9-/]+',
    message=u'Polku saa sisältää vain pieniä kirjaimia, numeroita, väliviivoja sekä kauttaviivoja.'
)


class CommonFields:
    path = dict(
        max_length=1023,
        validators=[validate_path],
        verbose_name=u'Polku',
        help_text=u'Polku määritetään automaattisesti teknisen nimen perusteella.',
    )

    slug = dict(
        blank=True, # actually not, but autogenerated anyway
        max_length=63,
        validators=[validate_slug],
        verbose_name=u'Tekninen nimi',
        help_text=u'Tekninen nimi eli "slug" näkyy URL-osoitteissa. Sallittuja '
            u'merkkejä ovat pienet kirjaimet, numerot ja väliviiva. Jos jätät teknisen nimen tyhjäksi, '
            u'se generoidaan automaattisesti otsikosta. Jos muutat teknistä nimeä julkaisun jälkeen, '
            u'muista luoda tarvittavat uudelleenojaukset.',
    )

    title = dict(
        max_length=1023,
        verbose_name=u'Otsikko',
        help_text=u'Otsikko näytetään automaattisesti sivun ylälaidassa sekä valikossa. Älä lisää erillistä pääotsikkoa sivun tekstiin.',
    )

    body = dict(
        blank=True,
        verbose_name=u'Leipäteksti',
    )

    page_template = dict(
        max_length=127,
        verbose_name=u'Sivupohja',
        help_text=u'Sivut näytetään käyttäen tätä sivupohjaa. Tämännimisen sivupohjan tulee löytyä lähdekoodista.',
    )

    site = dict(
        verbose_name=u'Sivusto',
        help_text=u'Sivusto, jolle tämä sivu kuuluu. HUOM! Kun haluat luoda saman sivun toiselle sivustolle, älä siirrä vanhaa sivua vaan käytä sivunkopiointitoimintoa.',
    )

    public_from = dict(
        null=True,
        blank=True,
        verbose_name=u'Julkaisuaika',
        help_text=u'Sivu on tästä hetkestä alkaen myös sisäänkirjautumattomien käyttäjien luettavissa, jos nämä tietävät osoitteen. Jätä tyhjäksi, jos haluat jättää sivun luonnokseksi.',
    )

    visible_from = dict(
        null=True,
        blank=True,
        verbose_name=u'Näkyvissä alkaen',
        help_text=u'Sivu on tästä hetkestä alkaen näkyvissä valikossa tai listauksessa. Jätä tyhjäksi, jos haluat jättää sivun piilotetuksi.',
    )

    created_at = dict(
        auto_now_add=True,
        verbose_name=u'Luotu',
    )

    updated_at = dict(
        auto_now=True,
        verbose_name=u'Päivitetty',
    )


class SiteSettings(models.Model):
    site = models.OneToOneField(Site,
        verbose_name=u'Sivusto',
        related_name='site_settings',
    )

    description = models.TextField(
        verbose_name=u'Sivuston kuvaus',
        help_text=u'Näkyy mm. hakukoneille sekä RSS-asiakasohjelmille.',
        blank=True,
        default='',
    )

    keywords = models.TextField(
        verbose_name=u'Sivuston avainsanat',
        help_text=u'Pilkuilla erotettu avainsanalista. Näkyy mm. hakukoneille.',
        blank=True,
        default='',
    )

    base_template = models.CharField(
        max_length=127,
        verbose_name=u'Asettelupohja',
        help_text=u'Asettelupohja määrittelee sivuston perusasettelun. Tämännimisen asettelupohjan tulee löytyä lähdekoodista.',
    )

    page_template = models.CharField(**CommonFields.page_template)

    blog_index_template = models.CharField(
        max_length=127,
        verbose_name=u'Blogilistauspohja',
        help_text=u'Blogilistaus näytetään käyttäen tätä sivupohjaa. Tämännimisen sivupohjan tulee löytyä lähdekoodista.',
    )

    blog_post_template = models.CharField(
        max_length=127,
        verbose_name=u'Blogipostauspohja',
        help_text=u'Blogipostaukset näytetään käyttäen tätä sivupohjaa. Tämännimisen sivupohjan tulee löytyä lähdekoodista.',
    )

    google_analytics_token = models.CharField(
        max_length=63,
        blank=True,
        verbose_name=u'Google Analytics -avain',
        help_text=u'Jos täytät tähän Google Analytics -sivustoavaimen, ei-kirjautuneiden käyttäjien visiitit raportoidaan Google Analyticsiin.',
    )

    context_processor_code = models.CharField(
        max_length=255,
        blank=True,
        default=u'',
        verbose_name=u'Sivustokontrolleri',
        help_text=u'Polku funktioon, joka suoritetaan joka sivulatauksella ja joka voi määritellä lisää muuttujia sivuston nimiavaruuteen.',
    )

    @classmethod
    def get_or_create_dummy(cls):
        site, unused = Site.objects.get_or_create(domain='example.com')

        return cls.objects.get_or_create(
            site=site,
            defaults=dict(
                title='Test site',
                base_template='example_base.jade',
                page_template='example_page.jade',
                blog_index_template='example_blog_index.jade',
                blog_post_template='example_blog_post.jade',
            )
        )

    @property
    def title(self):
        return self.site.name if self.site else None

    def get_menu(self, t=None, current_url=None, parent=None):
        if t is None:
            t = now()

        return [
            page.get_menu_entry(t=t, current_url=current_url)
            for page in Page.objects.filter(site=self.site, parent=parent, visible_from__lte=t).prefetch_related('child_page_set').all()
        ]

    def get_absolute_url(self):
        return '//{domain}'.format(domain=self.site.domain)

    def get_protocol_relative_uri(self, view_name, *args, **kwargs):
        return '//{domain}{path}'.format(
            domain=self.site.domain,
            path=reverse(view_name, args=args, kwargs=kwargs),
        )

    def get_visible_blog_posts(self):
        t = now()

        return self.site.blog_post_set.filter(visible_from__lte=t)

    def __unicode__(self):
        return self.site.domain if self.site else None

    class Meta:
        verbose_name = u'sivuston asetukset'
        verbose_name_plural = u'sivustojen asetukset'


BaseMenuEntry = namedtuple('MenuEntry', 'active href text children')
class MenuEntry(BaseMenuEntry):
    @property
    def active_css(self):
        return 'active' if self.active else ''


class RenderPageMixin(object):
    def render(self, request, **extra_vars):
        vars = dict(extra_vars,
            page=self,
        )

        return render(request, self.template, vars)


class PageAdminMixin(object):
    def admin_is_published(self):
        return self.public_from is not None
    admin_is_published.short_description = u'Julkinen'
    admin_is_published.boolean = True
    admin_is_published.admin_order_field = 'public_from'

    def admin_is_visible(self):
        return self.visible_from is not None
    admin_is_visible.short_description = u'Näkyvissä'
    admin_is_visible.boolean = True
    admin_is_visible.admin_order_field = 'visible_from'


class Page(models.Model, RenderPageMixin, PageAdminMixin):
    site = models.ForeignKey(Site, **CommonFields.site)
    path = models.CharField(**CommonFields.path)
    parent = models.ForeignKey('Page',
        null=True,
        blank=True,
        verbose_name=u'Yläsivu',
        help_text=u'Jos valitset tähän sivun, tämä sivu luodaan valitun sivun alaisuuteen. Jos jätät tämän tyhjäksi, sivu luodaan päätasolle.',
        related_name='child_page_set',
    )

    slug = models.CharField(**CommonFields.slug)

    created_at = models.DateTimeField(**CommonFields.created_at)
    updated_at = models.DateTimeField(**CommonFields.updated_at)
    public_from = models.DateTimeField(**CommonFields.public_from)
    visible_from = models.DateTimeField(**CommonFields.visible_from)

    title = models.CharField(**CommonFields.title)
    override_menu_text = models.CharField(
        max_length=1023,
        blank=True,
        verbose_name=u'Valikkoteksti',
        help_text=u'Sivu näkyy tällä nimellä valikossa. Jos jätät tämän tyhjäksi, käytetään otsikkoa.',
    )
    override_page_template = models.CharField(blank=True, default=u'', **CommonFields.page_template)
    page_controller_code = models.CharField(
        max_length=255,
        blank=True,
        default=u'',
        verbose_name=u'Sivukontrolleri',
        help_text=u'Polku funktioon, joka suoritetaan joka sivulatauksella ja joka voi määritellä lisää muuttujia sivupohjan nimiavaruuteen.',
    )
    order = models.IntegerField(
        default=0,
        verbose_name=u'Järjestys',
        help_text=u'Saman yläsivun alaiset sivut järjestetään valikossa tämän luvun mukaan nousevaan '
            u'järjestykseen (pienin ensin).'
    )
    body = models.TextField(**CommonFields.body)

    @property
    def edit_link(self):
        return reverse('admin:content_page_change', args=(self.id,))

    @property
    def menu_text(self):
        if self.override_menu_text:
            return self.override_menu_text
        else:
            return self.title

    @property
    def template(self):
        if self.override_page_template:
            return self.override_page_template
        else:
            return self.site.site_settings.page_template

    @property
    def is_front_page(self):
        return self.parent is None and self.slug == 'front-page'

    def get_absolute_url(self):
        return u'//{domain}/{path}'.format(
            domain=self.site.domain,
            path=u'' if self.is_front_page else self.path,

        )

    def get_local_url(self):
        return u'/' if self.is_front_page else u'/' + self.path

    def get_menu_entry(self, child_levels=1, t=None, current_url=None):
        # Guard against infinite recursion on parent loop and prevent lots of queries on default 2-level menu structure
        if child_levels > 0:
            children = [
                child_page.get_menu_entry(
                    child_levels=child_levels - 1,
                    t=t,
                    current_url=current_url,
                )

                # TODO check if this hits the prefetch
                for child_page in self.child_page_set.filter(visible_from__lte=t)
            ]
        else:
            children = []

        href = self.get_local_url()

        if current_url:
            if children:
                active = current_url.startswith(href)
            else:
                active = current_url == href
        else:
            active = False

        return MenuEntry(
            active=active,
            href=href,
            text=self.menu_text,
            children=children,
        )

    def as_dict(self):
        return pick_attrs(self,
            'path',
            'title',
            'override_menu_text',
            'body',
            'order',
            public_from=self.public_from.isoformat() if self.public_from else None,
            visible_from=self.visible_from.isoformat() if self.visible_from else None,
            created_at=self.created_at.isoformat() if self.created_at else None,
            updated_at=self.updated_at.isoformat() if self.updated_at else None,
        )

    def get_parent_path(self):
        assert self.path
        return u'/'.join(self.path.split('/')[:-1])

    def copy_to_site(self, site, **extra_keys):
        parent_path = self.get_parent_path()
        if parent_path:
            parent = Page.objects.get(site=site, path=parent_path)
        else:
            parent = None

        page_copy_attrs = dict(site=site, parent=parent)
        page_copy_attrs.update((key, getattr(self, key)) for key in Page.copy_to_site.fields_to_set)
        page_copy_attrs.update(extra_keys)

        original_slug = page_copy_attrs['slug']
        if Page.objects.filter(site=site, parent=parent, slug=page_copy_attrs['slug']).exists():
            counter = 0
            while True:
                counter += 1
                page_copy_attrs['slug'] = "{original_slug}-copy-{counter}".format(original_slug=original_slug, counter=counter)
                if not Page.objects.filter(site=site, parent=parent, slug=page_copy_attrs['slug']).exists():
                    break

        page_copy = Page(**page_copy_attrs)
        page_copy.save()

        return page_copy
    copy_to_site.fields_to_set = [
        'slug',
        'title',
        'override_menu_text',
        'body',
        'order',
    ]

    def render(self, request, **extra_vars):
        if self.page_controller_code:
            page_controller_func = get_code(self.page_controller_code)
            extra_vars.update(page_controller_func(request, self))

        return super(Page, self).render(request, **extra_vars)

    def _make_path(self):
        if self.parent is None:
            return self.slug
        else:
            return self.parent.path + '/' + self.slug

    def save(self, *args, **kwargs):
        if self.title and not self.slug:
            self.slug = slugify(self.title)

        if self.slug:
            self.path = self._make_path()

        return_value = super(Page, self).save(*args, **kwargs)

        # In case path changed, update child pages' paths.
        # TODO prevent parent loop in somewhere else
        for child_page in self.child_page_set.all():
            child_page.save()

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = u'sivu'
        verbose_name_plural = u'sivut'
        unique_together = [('site', 'path'), ('site', 'parent', 'slug')]

        # Usually searches are filtered by site and parent, so we skip them from the ordering.
        ordering = ('order',)


class Redirect(models.Model):
    site = models.ForeignKey(Site)
    path = models.CharField(**CommonFields.path)
    target = models.CharField(max_length=1023)

    def __unicode__(self):
        return self.path

    class Meta:
        unique_together = [('site', 'path')]
        verbose_name = u'uudelleenohjaus'
        verbose_name_plural = u'uudelleenohjaukset'


class BlogCategory(models.Model):
    site = models.ForeignKey(Site, verbose_name=u'Sivusto')
    slug = models.CharField(**CommonFields.slug)
    title = models.CharField(**CommonFields.title)

    def get_visible_blog_posts(self):
        return self.blog_posts.filter(visible_from__lte=now())

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.title and not self.slug:
            self.slug = slugify(self.title)

        return super(BlogCategory, self).save(*args, **kwargs)

    class Meta:
        verbose_name = u'Blogin kategoria'
        verbose_name_plural = u'Blogin kategoriat'

        unique_together = [('site', 'slug')]


STATE_CHOICES = [
    ('draft', u'Luonnos'),
    ('review', u'Odottaa tarkistusta'),
    ('ready', u'Valmis julkaistavaksi'),
]


class BlogPost(models.Model, RenderPageMixin, PageAdminMixin):
    site = models.ForeignKey(Site, related_name='blog_post_set', **CommonFields.site)
    path = models.CharField(**CommonFields.path)
    date = models.DateField(
        blank=True,
        verbose_name=u'Päivämäärä',
        help_text=u'Päivämäärä on osa postauksen osoitetta. Älä muuta päivämäärää julkaisun jälkeen. '
            u'Jos jätät kentän tyhjäksi, siihen valitaan tämä päivä.',
    )
    slug = models.CharField(**CommonFields.slug)
    author = models.ForeignKey(User,
        null=True,
        blank=True,
        verbose_name=u'Tekijä',
        help_text=u'Jos jätät kentän tyhjäksi, tekijäksi asetetaan automaattisesti sinut.',
    )

    state = models.CharField(
        max_length=7,
        default='draft',
        choices=STATE_CHOICES,
        verbose_name=u'Luonnoksen tila',
        help_text=u'Tämä kenttä kommunikoi muille julkaisujärjestelmän käyttäjille, onko sivu '
            u'kirjoittajan mielestä valmis julkaistavaksi. Jos et itse julkaise kirjoitustasi, '
            u'jätä kirjoituksesi tilaan "Odottaa tarkistusta" kun se on mielestäsi valmis. Tämä '
            u'kenttä ei vaikuta teknisesti kirjoituksen julkaisuun millään tavalla.'
    )
    internal_notes = models.TextField(
        blank=True,
        verbose_name=u'Sisäiset muistiinpanot',
        help_text=u'Tähän kenttään voit jättää muistiinpanoja itsellesi ja muille julkaisujärjestelmän '
            u'käyttäjille esimerkiksi suunnittelemastasi sisällöstä tai kirjoituksen julkaisuaikataulusta. '
            u'Nämä muistiinpanot eivät näy ulospäin, vaan ne on tarkoitettu puhtaasti julkaisujärjestelmän '
            u'toimittaja- ja ylläpitokäyttäjien tiedoksi.'
    )

    created_at = models.DateTimeField(**CommonFields.created_at)
    updated_at = models.DateTimeField(**CommonFields.updated_at)
    public_from = models.DateTimeField(**CommonFields.public_from)
    visible_from = models.DateTimeField(**CommonFields.visible_from)

    title = models.CharField(**CommonFields.title)
    body = models.TextField(**CommonFields.body)
    override_excerpt = models.TextField(
        verbose_name=u'Lyhennelmä',
        blank=True,
        default='',
        help_text=u'Kirjoita muutaman lauseen mittainen lyhennelmä kirjoituksesta. Lyhennelmä näkyy '
            u'blogilistauksessa. Mikäli lyhennelmää ei ole annettu, leikataan lyhennelmäksi sopivan '
            u'mittainen pätkä itse kirjoituksesta.',
    )

    categories = models.ManyToManyField(BlogCategory,
        verbose_name=u'Kategoriat',
        blank=True,
        related_name='blog_posts',
    )

    @property
    def edit_link(self):
        return reverse('admin:content_blogpost_change', args=(self.id,))

    @property
    def excerpt(self):
        max_chars = settings.TRACONTENT_BLOG_AUTO_EXCERPT_MAX_CHARS

        if self.override_excerpt:
            return self.override_excerpt
        else:
            plain_text = bleach.clean(self.body, tags=[], strip=True)
            if len(plain_text) <= max_chars:
                return plain_text
            else:
                return plain_text[:max_chars] + u'…'

    @property
    def template(self):
        return self.site.site_settings.blog_post_template

    def get_absolute_url(self):
        return u'//{domain}/{path}'.format(
            domain=self.site.domain,
            path=self.path,
        )

    def get_comments(self):
        return self.blog_comment_set.filter(removed_at__isnull=True)

    def _make_path(self):
        return reverse('content_blog_post_view', kwargs=dict(
            year=self.date.year,
            month="{:02d}".format(self.date.month),
            day="{:02d}".format(self.date.day),
            slug=self.slug,
        ))[1:] # remove leading /

    def save(self, *args, **kwargs):
        if self.title and not self.slug:
            self.slug = slugify(self.title)

        if self.date and self.slug:
            self.path = self._make_path()

        return super(BlogPost, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = u'blogipostaus'
        verbose_name_plural = u'blogipostaukset'
        unique_together = [('site', 'path'), ('site', 'date', 'slug')]

        # Usually queries are filtered by site, so we skip it from the ordering.
        ordering = ('-date', '-public_from')


class BlogComment(models.Model):
    blog_post = models.ForeignKey(BlogPost, verbose_name=u'Blogipostaus', db_index=True, related_name='blog_comment_set')
    author_name = models.CharField(
        max_length=1023,
        verbose_name=u'Nimi tai nimimerkki',
        help_text=u'Näkyy muille sivun lukijoille.',
    )
    author_email = models.EmailField(
        verbose_name=u'Sähköpostiosoite',
        help_text=u'Sähköpostiosoitetta ei julkaista.',
    )
    author_ip_address = models.CharField(
        max_length=17,
        blank=True,
        verbose_name=u'IP-osoite',
        help_text=u'IP-osoite näkyy vain ylläpitokäyttöliittymässä.',
    )

    comment = models.TextField(
        verbose_name=u'Kommentti',
        help_text=u'Pidetään keskustelu ystävällisenä, asiallisena ja muita kunnioittavana. Ylläpito poistaa asiattomat kommentit.',
    )

    created_at = models.DateTimeField(**CommonFields.created_at)
    removed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=u'Piilottamisaika',
    )
    removed_by = models.ForeignKey(User,
        null=True,
        blank=True,
        verbose_name=u'Piilottaja',
    )

    def admin_get_site(self):
        return self.blog_post.site
    admin_get_site.short_description = 'Sivusto'
    admin_get_site.admin_order_field = 'blog_post__site'

    @property
    def excerpt(self):
        if self.comment and len(self.comment) > BlogComment.admin_get_excerpt.max_length:
            return self.comment[:BlogComment.admin_get_excerpt.max_length] + u'…'
        else:
            return self.comment

    # Cannot set admin metadata on property object
    def admin_get_excerpt(self):
        return self.excerpt
    admin_get_excerpt.max_length = 100
    admin_get_excerpt.short_description = u'Kommentti (lyhennetty)'

    @property
    def is_active(self):
        return self.removed_at is None

    def admin_is_active(self):
        return self.is_active
    admin_is_active.short_description = u'Näkyvissä'
    admin_is_active.boolean = True
    admin_is_active.admin_order_field = 'removed_at'

    def get_absolute_url(self):
        return self.blog_post.get_absolute_url() + u'#comment-{id}'.format(id=self.id)

    @property
    def edit_link(self):
        return reverse('admin:content_blogcomment_change', args=(self.id,))

    def send_mail_to_moderators(self, request):
        subject = "{site_title}: Uusi blogikommentti".format(site_title=request.site.site_settings.title)
        body = get_template('content_email_blog_new_comment.eml').render(dict(
            site_settings=request.site.site_settings,
            blog_comment=self,
            settings=settings,
            comment_url=request.build_absolute_uri(self.get_absolute_url()),
            moderation_url=request.build_absolute_uri(self.edit_link),
        ), request)

        if settings.DEBUG:
            print body

        if settings.TRACONTENT_BLOG_COMMENT_MODERATORS:
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=format_emails(settings.TRACONTENT_BLOG_COMMENT_MODERATORS),
            )

    def __unicode__(self):
        return self.excerpt

    class Meta:
        verbose_name = u'blogikommentti'
        verbose_name_plural = u'blogikommentit'
        ordering = ('created_at',)
        index_together = [('blog_post', 'removed_at')]
