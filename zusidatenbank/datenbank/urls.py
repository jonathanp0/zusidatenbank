from django.conf.urls import url

from . import views

app_name = 'db'
urlpatterns = [
    url(r'^streckenmodule/(?P<pk>[^/]+)$', views.StreckenModuleDetail.as_view(), name='smdetail'),
    url(r'^streckenmodule$', views.StreckenModuleList.as_view(), name='smlist'),
    url(r'^fahrplan/(?P<pk>[^/]+)$', views.FahrplanDetail.as_view(), name='fpdetail'),
    url(r'^fahrplan$', views.FahrplanList.as_view(), name='fplist'),
    url(r'^fahrplanzug/(?P<pk>[^/]+)/$', views.FahrplanZugDetail.as_view(), name='fzdetail'),
    url(r'^fahrplan/(?P<path>[^/]+)/(?P<gruppe>.+)$', views.FahrplanZugList.as_view(), name='fzgruppelist'),
    url(r'^fahrplanzug/random$', views.FahrplanZugRandom.as_view(), name='fzrandom'),
    url(r'^fahrplanzug$', views.FahrplanZugList.as_view(), name='fzlist'),
    url(r'^fuehrerstand/(?P<pk>[-_\.\\\w\d]+)/$', views.FuehrerstandDetail.as_view(), name='fsdetail'),
    url(r'^fuehrerstand$', views.FuehrerstandList.as_view(), name='fslist'),
    url(r'^fahrzeug/(?P<root_file>[^/]+)/(?P<haupt_id>[0-9]+)/(?P<neben_id>[0-9]+)/$', views.FahrzeugDetail.as_view(), name='fvdetail'),
    url(r'^fahrzeug/(?P<root_file>[^/]+)/$', views.FahrzeugList.as_view(), name='fvvariantlist'),
    url(r'^fahrzeug$', views.FahrzeugList.as_view(), name='fvlist'),
    url(r'^aktuell$', views.FlatblockView.as_view(extra_context={'flatblock': 'home.altaktuell'}), name='altaktuell'),
    url(r'^fahrplanzug/none$', views.FlatblockView.as_view(extra_context={'flatblock': 'error.keinzug'}), name='keinzug'),
    url(r'^impressum$', views.FlatblockView.as_view(extra_context={'flatblock': 'home.impressum'}), name='impressum'),
    url(r'^$', views.IndexView.as_view(), name='index'),
]