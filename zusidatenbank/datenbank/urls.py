from django.conf.urls import url

from . import views

app_name = 'db'
urlpatterns = [
    url(r'^streckenmodule/list/$', views.StreckenModuleList.as_view(), name='smlist'),
    url(r'^streckenmodules/(?P<slug>[^/]+)/$', views.StreckenModuleList.as_view(), name='smdetail'),
    url(r'^fahrplanzug/list/$', views.FahrplanZugList.as_view(), name='fzlist'),
    url(r'^fahrplanzug/(?P<slug>[^/]+)/$', views.FuehrerstandList.as_view(), name='fzdetail'),
    url(r'^fuehrerstand/list/$', views.FuehrerstandList.as_view(), name='fslist'),
    url(r'^fuehrerstand/(?P<slug>[-_\.\\\w\d]+)/$', views.FuehrerstandList.as_view(), name='fsdetail'),
]