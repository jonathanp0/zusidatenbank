from django.conf.urls import url

from . import views

app_name = 'db'
urlpatterns = [
    url(r'^streckenmodules/(?P<pk>[^/]+)$', views.StreckenModuleDetail.as_view(), name='smdetail'),
    url(r'^streckenmodule/list/$', views.StreckenModuleList.as_view(), name='smlist'),
    url(r'^fahrplanzug/list/$', views.FahrplanZugList.as_view(), name='fzlist'),
    url(r'^fahrplanzug/(?P<slug>[^/]+)/$', views.FuehrerstandList.as_view(), name='fzdetail'),
    url(r'^fuehrerstand/list/$', views.FuehrerstandList.as_view(), name='fslist'),
    url(r'^fuehrerstand/(?P<pk>[-_\.\\\w\d]+)/$', views.FuehrerstandDetail.as_view(), name='fsdetail'),
    url(r'^autor/(?P<pk>[^/]+)$', views.StreckenModuleDetail.as_view(), name='autordetail'),
]