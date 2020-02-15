from django.conf.urls import url, patterns
from django.contrib.auth.decorators import permission_required, login_required

from enfinchezmoi.views import ShowPostList, PostDetail, SubmitAd, \
    PostList, TownList, AreaList, CategoryList, SubCategoryList, \
    ChangePost, ChangeTown, ChangeArea, ChangeCategory, ChangeSubCategory, ChangeOwner, post_photo_uploader

urlpatterns = patterns(
    '',
    # url(r'^aboutUs/$', AboutUs.as_view(), name='about_us'),
    url(r'^submitAd/$', login_required(SubmitAd.as_view()), name='submit_ad'),
    url(r'^showPosts/$', ShowPostList.as_view(), name='show_post_list'),

    url(r'^posts/$', permission_required('enfinchezmoi.ik_manage_post')(PostList.as_view()),
        name='post_list'),
    url(r'^changePost/$', permission_required('enfinchezmoi.ik_manage_post')(ChangePost.as_view()), name='change_post'),
    url(r'^changePost/(?P<object_id>[-\w]+)/$', permission_required('enfinchezmoi.ik_manage_post')(ChangePost.as_view())
        , name='change_post'),

    url(r'^townList/$', permission_required('enfinchezmoi.ik_manage_post')(TownList.as_view()),
        name='town_list'),
    url(r'^changeTown/$', permission_required('enfinchezmoi.ik_manage_post')(ChangeTown.as_view()), name='change_town'),
    url(r'^changeTown/(?P<object_id>[-\w]+)/$', permission_required('enfinchezmoi.ik_manage_post')(ChangeTown.as_view())
        , name='change_town'),

    url(r'^areaList/$', permission_required('enfinchezmoi.ik_manage_post')(AreaList.as_view()),
        name='area_list'),
    url(r'^changeArea/$', permission_required('enfinchezmoi.ik_manage_post')(ChangeArea.as_view()), name='change_area'),
    url(r'^changeArea/(?P<object_id>[-\w]+)/$', permission_required('enfinchezmoi.ik_manage_post')(ChangeArea.as_view()),
        name='change_area'),


    url(r'^categories/$', permission_required('enfinchezmoi.ik_manage_post')(CategoryList.as_view()),
        name='category_list'),
    url(r'^changeCategory/$', permission_required('enfinchezmoi.ik_manage_post')(ChangeCategory.as_view()),
        name='change_category'),
    url(r'^changeCategory/(?P<object_id>[-\w]+)/$', permission_required('enfinchezmoi.ik_manage_post')
    (ChangeCategory.as_view()), name='change_category'),


    url(r'^subcategories/$', permission_required('enfinchezmoi.ik_manage_post')(SubCategoryList.as_view()),
        name='subcategory_list'),
    url(r'^changeSubCategory/$', permission_required('enfinchezmoi.ik_manage_post')(ChangeSubCategory.as_view()),
        name='change_subcategory'),
    url(r'^changeSubCategory/(?P<object_id>[-\w]+)/$', permission_required('enfinchezmoi.ik_manage_post')
    (ChangeSubCategory.as_view()), name='change_subcategory'),


    url(r'^changeOwner/$', permission_required('enfinchezmoi.ik_manage_post')(ChangeOwner.as_view()),
        name='change_owner'),
    url(r'^changeOwner/(?P<object_id>[-\w]+)/$', permission_required('enfinchezmoi.ik_manage_post')(ChangeOwner.as_view()),
        name='change_owner'),

    url(r'^post_photo_uploader$', post_photo_uploader, name='post_photo_uploader'),

    url(r'^(?P<category_slug>[-\w]+)/$', ShowPostList.as_view(), name='show_post_list'),
    url(r'^(?P<category_slug>[-\w]+)/(?P<subcategory_slug>[-\w]+)/$', ShowPostList.as_view(), name='show_post_list'),
    url(r'^(?P<category_slug>[-\w]+)/(?P<subcategory_slug>[-\w]+)/(?P<area_slug>[-\w]+)/(?P<post_id>[-\w]+)/$',
        PostDetail.as_view(), name='post_detail'),
)


