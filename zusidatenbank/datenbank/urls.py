from django.conf.urls import url

from . import views

app_name = 'db'
urlpatterns = [
    url(r'^streckenmodule/(?P<pk>[^/]+)$', views.StreckenModuleDetail.as_view(), name='smdetail'),
    url(r'^streckenmodule$', views.StreckenModuleList.as_view(), name='smlist'),
    url(r'^fahrplanzug/(?P<slug>[^/]+)/$', views.FuehrerstandList.as_view(), name='fzdetail'),
    url(r'^fahrplanzug$', views.FahrplanZugList.as_view(), name='fzlist'),
    url(r'^fuehrerstand/(?P<pk>[-_\.\\\w\d]+)/$', views.FuehrerstandDetail.as_view(), name='fsdetail'),
    url(r'^fuehrerstand$', views.FuehrerstandList.as_view(), name='fslist'),
    url(r'^autor/(?P<pk>[^/]+)$', views.StreckenModuleDetail.as_view(), name='autordetail'),
    url(r'^fahrzeug/(?P<slug>[^/]+)/$', views.FuehrerstandList.as_view(), name='fzedetail'),
    url(r'^fahrzeug$', views.FahrzeugList.as_view(), name='fzelist'),
]