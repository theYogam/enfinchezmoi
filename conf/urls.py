from django.conf.urls import url, include, patterns
from django.contrib import admin
from enfinchezmoi.views import Home

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^i18n/', include('django.conf.urls.i18n')),

    url(r'^laakam/', include(admin.site.urls)),
    url(r'^billing/', include('ikwen.billing.urls', namespace='billing')),
    url(r'^cashout/', include('ikwen.cashout.urls', namespace='cashout')),
    url(r'^retail/', include('ikwen.partnership.urls', namespace='partnership')),
    url(r'^theming/', include('ikwen.theming.urls', namespace='theming')),
    url(r'^rewarding/', include('ikwen.rewarding.urls', namespace='rewarding')),
    url(r'^revival/', include('ikwen.revival.urls', namespace='revival')),
    url(r'^kakocase/', include('ikwen_kakocase.kakocase.urls', namespace='kakocase')),
    url(r'^shavida/', include('ikwen_shavida.shavida.urls', namespace='shavida')),
    url(r'^webnode/', include('ikwen_webnode.webnode.urls', namespace='webnode')),
    url(r'^daraja/', include('daraja.urls', namespace='daraja')),
    url(r'^foulassi/', include('ikwen_foulassi.foulassi.urls', namespace='foulassi')),
    url(r'^ikwen/', include('ikwen.core.urls', namespace='ikwen')),

    # Enfinchezmoi URLs

    url(r'^', include('enfinchezmoi.urls', namespace='enfinchezmoi')),
    url(r'^$', Home.as_view(), name='home'),
)
