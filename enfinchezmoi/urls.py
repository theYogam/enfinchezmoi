from django.conf.urls import url, patterns
from django.contrib.auth.decorators import permission_required, login_required

from enfinchezmoi.views import ShowPostList, PostDetail, SubmitAd, \
    PostList, CityList, HoodList, CategoryList, SubCategoryList, \
    ChangePost, ChangeCity, ChangeHood, ChangeCategory, ChangeSubCategory, ChangeOwner, post_photo_uploader, \
    ReservationList, ChangeReservation, set_reservation_checkout, confirm_reservation_payment, Receipt

urlpatterns = patterns(
    '',
    # url(r'^aboutUs/$', AboutUs.as_view(), name='about_us'),
    url(r'^submitAd/$', permission_required('enfinchezmoi.ik_manage_post')(login_required(SubmitAd.as_view())), name='submit_ad'),
    url(r'^showPosts/$', ShowPostList.as_view(), name='show_post_list'),

    url(r'^posts/$', permission_required('enfinchezmoi.ik_manage_post')(PostList.as_view()),
        name='post_list'),
    url(r'^changePost/$', permission_required('enfinchezmoi.ik_manage_post')(ChangePost.as_view()), name='change_post'),
    url(r'^changePost/(?P<object_id>[-\w]+)/$', permission_required('enfinchezmoi.ik_manage_post')(ChangePost.as_view())
        , name='change_post'),

    # url(r'^payments/$', permission_required('council.ik_manage_payment')(PaymentList.as_view()),
    #     name='payment_list'),

    url(r'^cityList/$', permission_required('enfinchezmoi.ik_manage_post')(CityList.as_view()),
        name='city_list'),
    url(r'^changeCity/$', permission_required('enfinchezmoi.ik_manage_post')(ChangeCity.as_view()), name='change_city'),
    url(r'^changeCity/(?P<object_id>[-\w]+)/$', permission_required('enfinchezmoi.ik_manage_post')(ChangeCity.as_view())
        , name='change_city'),

    url(r'^hoodList/$', permission_required('enfinchezmoi.ik_manage_post')(HoodList.as_view()),
        name='hood_list'),
    url(r'^changeHood/$', permission_required('enfinchezmoi.ik_manage_post')(ChangeHood.as_view()), name='change_hood'),
    url(r'^changeHood/(?P<object_id>[-\w]+)/$', permission_required('enfinchezmoi.ik_manage_post')(ChangeHood.as_view()),
        name='change_hood'),


    url(r'^categories/$', permission_required('enfinchezmoi.ik_manage_post')(CategoryList.as_view()),
        name='category_list'),
    url(r'^changeCategory/$', permission_required('enfinchezmoi.ik_manage_post')(ChangeCategory.as_view()),
        name='change_category'),
    url(r'^changeCategory/(?P<object_id>[-\w]+)/$', permission_required('enfinchezmoi.ik_manage_post')
    (ChangeCategory.as_view()), name='change_category'),


    url(r'^reservations/$', permission_required('enfinchezmoi.ik_manage_reservation')(ReservationList.as_view()),
        name='reservation_list'),
    url(r'^changeReservation/$', permission_required('enfinchezmoi.ik_manage_reservation')(ChangeReservation.as_view()),
        name='change_reservation'),
    url(r'^changeReservation/(?P<object_id>[-\w]+)/$', permission_required('enfinchezmoi.ik_manage_reservation')
    (ChangeReservation.as_view()), name='change_reservation'),


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
    url(r'^set_reservation_checkout$', set_reservation_checkout, name='set_reservation_checkout'),
    url(r'^confirm_reservation_payment/(?P<object_id>[-\w]+)$', confirm_reservation_payment, name='confirm_reservation_payment'),
    url(r'^confirm_reservation_payment/(?P<object_id>[-\w]+)/(?P<signature>[-\w]+)$', confirm_reservation_payment, name='confirm_reservation_payment'),
    url(r'^receipt/(?P<receipt_id>[-\w]+)/$', login_required(Receipt.as_view()), name='receipt'),

    url(r'^(?P<category_slug>[-\w]+)/$', ShowPostList.as_view(), name='show_post_list'),
    url(r'^(?P<category_slug>[-\w]+)/(?P<subcategory_slug>[-\w]+)/$', ShowPostList.as_view(), name='show_post_list'),
    url(r'^(?P<category_slug>[-\w]+)/(?P<subcategory_slug>[-\w]+)/(?P<hood_slug>[-\w]+)/(?P<post_id>[-\w]+)/$',
        PostDetail.as_view(), name='post_detail'),
)


