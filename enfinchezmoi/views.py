import json
import logging
import os
import sys
from threading import Thread
from datetime import datetime, timedelta

from ajaxuploader.views import AjaxFileUploader
from django.contrib import messages
from django.contrib.admin import helpers
from django.contrib.auth.decorators import permission_required
from django.core.files import File
from django.core.mail import EmailMessage
from django.db.models import Sum
from django.forms import ModelForm
from django.http.response import Http404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from conf.settings import WALLETS_DB_ALIAS
from ikwen.billing.utils import get_invoicing_config_instance, get_days_count, get_next_invoice_number, \
    get_payment_confirmation_message
from conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _, get_language, activate
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect, HttpResponse

from ikwen.accesscontrol.models import Member

from ikwen.core.models import Service, Application
from ikwen.core.views import HybridListView, ChangeObjectBase, ikwen_service, logger
from ikwen.core.utils import get_service_instance, get_model_admin_instance, DefaultUploadBackend, add_event, \
    XEmailMessage, get_mail_content, set_counters, increment_history_field
from ikwen.core.constants import CONFIRMED
from ikwen.billing.decorators import momo_gateway_request, momo_gateway_callback
from ikwen.billing.models import Invoice, MoMoTransaction, Payment, InvoiceItem, InvoiceEntry

from enfinchezmoi.admin import PostAdmin, CityAdmin, OwnerAdmin, CategoryAdmin, SubCategoryAdmin, HoodAdmin, \
    ReservationAdmin
from enfinchezmoi.models import Category, SubCategory, Post, City, Hood, Owner, Photo, Reservation
from enfinchezmoi.forms import SubmitAdForm, OwnerForm

# from conf import settings
from ikwen_kakocase.kako.utils import mark_duplicates
from ikwen_kakocase.kakocase.models import PRODUCT_PUBLISHED_EVENT
# from ikwen.revival.models import ProfileTag

reload(sys)
sys.setdefaultencoding('utf8')


class Home(TemplateView):
    template_name = 'enfinchezmoi/home.html'

    def get_context_data(self, **kwargs):
        context = super(Home, self).get_context_data(**kwargs)

        post_added = self.request.GET.get('post_added')
        if post_added:
            context['post_added'] = post_added

        post_list = Post.objects.filter(is_active=True)
        context = super(Home, self).get_context_data(**kwargs)
        context['service'] = get_service_instance()

        context['settings'] = settings
        context['city_list'] = [post.hood.city for post in post_list]
        context['hood_list'] = [post.hood for post in post_list]
        context['post_list'] = list(post_list)

        return context


class ShowPostList(TemplateView):
    template_name = 'enfinchezmoi/show_post_list.html'

    def get_context_data(self, **kwargs):
        context = super(ShowPostList, self).get_context_data(**kwargs)
        queryset = Post.objects

        subcategory_slug = kwargs.get('subcategory_slug')
        category_slug = kwargs.get('category_slug')
        try:
            category = Category.objects.get(slug=category_slug)
        except:
            pass
        hood = self.request.GET.get('hood_rent')
        address = self.request.GET.get('address')
        max_budget = self.request.GET.get('max_budget_rent')

        if not hood:
            hood = self.request.GET.get('hood_purchase')
            max_budget = self.request.GET.get('max_budget_purchase')

        subcategory_list = []
        for subcategory in SubCategory.objects.all():
            if self.request.GET.get(subcategory.name):
                subcategory = SubCategory.objects.get(name=subcategory.name)
                subcategory_list.append(subcategory)

        if len(subcategory_list) > 0:
            queryset = queryset.filter(subcategory__in=subcategory_list)

        if hood:
            hood = Hood.objects.get(name=hood)
            queryset = queryset.filter(hood=hood)
        if address:
            hood = Hood.objects.get(name=address)
            queryset = queryset.filter(hood=hood)
        if max_budget:
            queryset = queryset.filter(cost__lt=max_budget)
        if len(subcategory_list) > 0:
            queryset = queryset.filter(subcategory__in=subcategory_list)
        if category_slug:
            subcategory_list = []
            for subcategory in SubCategory.objects.filter(category=category):
                subcategory_list.append(subcategory)
            queryset = queryset.filter(subcategory__in=subcategory_list)
            context['category'] = category
        if subcategory_slug:
            subcategory = SubCategory.objects.get(category=category, slug=subcategory_slug)
            queryset = queryset.filter(subcategory=subcategory)
            context['subcategory'] = subcategory

        queryset = queryset.filter(is_active=True)

        context['post_list'] = queryset
        context['post_count'] = queryset.count()
        context['all_post_list'] = Post.objects.filter(is_active=True)
        return context


class PostDetail(TemplateView):
    template_name = 'enfinchezmoi/post_detail.html'

    def get(self, request, *args, **kwargs):
        post_id = request.GET.get('post_id')
        start_on = request.GET.get('start_on')
        end_on = request.GET.get('end_on')
        if start_on and end_on:
            start_on = datetime.strptime(start_on, "%Y-%m-%d")
            end_on = datetime.strptime(end_on, "%Y-%m-%d")
            post = get_object_or_404(Post, pk=post_id)

            action = request.GET.get('action')

            if action == 'check_availability':
                is_available = post.is_available(start_on, end_on)
                if is_available:
                    reservation = Reservation.objects.create(post=post, start_on=start_on, end_on=end_on,
                                                             amount=post.cost, member=self.request.user)
                    return HttpResponse(json.dumps({'success': is_available, 'reservation': reservation.pk}),
                                        content_type='application/json')

            if action == 'cancel_reservation':
                try:
                    reservation = Reservation.objects.get(post=post, start_on=start_on,
                                                          end_on=end_on, member=self.request.user)
                    reservation.delete()
                except:
                    pass
                return HttpResponse(json.dumps({'success': post.is_available(start_on, end_on)}),
                                    content_type='application/json')

        return super(PostDetail, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(PostDetail, self).get_context_data(**kwargs)
        post_id = kwargs['post_id']
        post = Post.objects.get(pk=post_id)
        # post.cost = int(post.cost)
        context['post'] = post
        context['related_post_list'] = Post.objects.filter(subcategory=post.subcategory, is_active=True).exclude(pk=post.pk)
        context['owner'] = post.owner
        context['request'] = self.request
        return context

    def post(self, request, *args, **kwargs):
        user = request.user
        post_id = kwargs['post_id']
        _post = Post.objects.get(pk=post_id)
        owner = _post.owner
        subject = _("New request for your ad %s" % _post.ref_ad)
        ref_ad = _post.ref_ad
        service = get_service_instance()
        sender = '%s <no-reply@ikwen.com>' % service.project_name

        name = self.request.POST.get('name')
        email = self.request.POST.get('email')
        phone = self.request.POST.get('phone')
        context = self.get_context_data(**kwargs)
        staff_list = [member.email for member in Member.objects.filter(is_staff=True)]
        if name and email and phone:
            try:
                html_content = get_mail_content(subject, template_name='enfinchezmoi/mails/send_contacts.html',
                                                extra_context={'name': name,
                                                               'email': email,
                                                               'phone': phone,
                                                               'ref_ad': ref_ad})

                recipient_list = [owner.email, owner.member.email, service.member.email, service.config.contact_email]
                recipient_list += staff_list
                context['recipient_list'] = recipient_list
                msg = XEmailMessage(subject, html_content, sender, recipient_list)
                msg.content_subtype = "html"
                Thread(target=lambda m: m.send(), args=(msg,)).start()

            except Exception as e:
                pass
                context['error'] = e
                return render(request, self.template_name, context)
            context['call_success_message'] = _('Your addresses have been successfully sent to the owner')
            return render(request, self.template_name, context)

        try:
            member = user
            user_message = self.request.POST.get('email_message')
            company_name = service.config.company_name
            html_content = get_mail_content(subject, template_name='enfinchezmoi/mails/get_information.html',
                                            extra_context={'member': member,
                                                           'ref_ad': ref_ad,
                                                           'company_name': company_name,
                                                           'user_message': user_message})
            recipient_list = [owner.email, owner.member.email, service.member.email, service.config.contact_email]
            recipient_list += staff_list
            context['recipient_list'] = recipient_list
            msg = XEmailMessage(subject, html_content, sender, recipient_list)
            msg.content_subtype = "html"
            Thread(target=lambda m: m.send(), args=(msg,)).start()

        except Exception as e:
            pass
            # context['error'] = e
            # return render(request, self.template_name, context)
        context['send_email_success_message'] = _('Your message has been successfully sent to the owner')
        return render(request, self.template_name, context)


class PostPhotoUploadBackend(DefaultUploadBackend):
    """
    Ajax upload handler for :class:`enfinchezmoi.models.Post` photos
    """
    def upload_complete(self, request, filename, *args, **kwargs):
        path = self.UPLOAD_DIR + "/" + filename
        self._dest.close()
        media_root = getattr(settings, 'MEDIA_ROOT')
        try:
            with open(media_root + path, 'r') as f:
                content = File(f)
                destination = media_root + Photo.UPLOAD_TO + "/" + filename
                photo = Photo()
                photo.image.save(destination, content)
                post_id = request.GET.get('post_id')
                if post_id:
                    try:
                        post = Post.objects.get(pk=post_id)
                        post.photos.append(photo)
                        post.save()
                    except:
                        pass

            os.unlink(media_root + path)
            return {
                'id': photo.id,
                'url': photo.image.small_url
            }
        except IOError as e:
            if getattr(settings, 'DEBUG', False):
                raise e
            return {'error': 'File failed to upload. May be invalid or corrupted image file'}


post_photo_uploader = AjaxFileUploader(PostPhotoUploadBackend)


class Receipt(TemplateView):
    template_name = 'enfinchezmoi/receipt.html'

    def get_context_data(self, **kwargs):
        context = super(Receipt, self).get_context_data(**kwargs)
        config = get_service_instance().config
        receipt_id = self.kwargs.get('receipt_id')
        try:
            reservation = Reservation.objects.select_related('member').get(pk=receipt_id)
        except Reservation.DoesNotExist:
            raise Http404("Reservation not found")
        context['currency_symbol'] = config.currency_symbol
        context['payment'] = reservation
        context['member'] = reservation.member
        context['amount'] = reservation.post.cost
        context['payment_number'] = get_next_invoice_number()
        return context


@momo_gateway_request
def set_reservation_checkout(request, *args, **kwargs):
    """
    This function has no URL associated with it.
    It serves as ikwen setting "MOMO_BEFORE_CHECKOUT"
    """
    post_id = request.POST['product_id']
    reservation = Reservation.objects.get(pk=post_id)
    days = (reservation.end_on - reservation.start_on).days
    amount = reservation.post.cost * days
    notification_url = reverse('enfinchezmoi:confirm_reservation_payment', args=(reservation.id,))
    post = reservation.post
    cancel_url = reverse('enfinchezmoi:post_detail', args=(post.subcategory.slug, post.subcategory.category.slug,
                                                           post.hood.slug, post.id))
    return_url = reverse('enfinchezmoi:receipt', args=(reservation.id, ))
    return reservation, amount, notification_url, return_url, cancel_url


@momo_gateway_callback
def confirm_reservation_payment(request, *args, **kwargs):
    """
    This view is run after successful user cashout "MOMO_AFTER_CHECKOUT"
    """
    tx = kwargs['tx']  # Decoration with @momo_gateway_callback makes 'tx' available in kwargs
    amount = tx.amount
    now = datetime.now()

    # Update reservation status --- Confirm reservation
    reservation_id = tx.object_id
    reservation = Reservation.objects.get(pk=reservation_id)
    reservation.processor_tx_id = tx.processor_tx_id
    reservation.method = Reservation.MOBILE_MONEY
    reservation.status = CONFIRMED
    item = InvoiceItem(label=_("Reservation of %s " % reservation.post), amount=reservation.amount)
    short_description = reservation.start_on.strftime("%Y/%m/%d") + ' - ' + reservation.end_on.strftime("%Y/%m/%d")
    entry = InvoiceEntry(item=item, short_description=short_description, total=reservation.amount, quantity_unit='')
    reservation.entries = [entry]
    reservation.save()

    # Share earnings
    weblet = get_service_instance(check_cache=False)
    config = weblet.config
    ikwen_charges = tx.amount * config.ikwen_share_rate / 100
    ikwen_share_rate = config.ikwen_share_fixed
    tx.fees = ikwen_charges
    tx.save()
    amount = (100 - ikwen_share_rate) * amount/100
    weblet.raise_balance(amount, provider=tx.wallet)
    set_counters(weblet)
    increment_history_field(weblet, 'turnover_history', amount)
    increment_history_field(weblet, 'earnings_history', amount)
    increment_history_field(weblet, 'transaction_count_history')

    member = reservation.member

    # Notify customer and staff

    payer_email = member.email
    email = config.contact_email
    if not email:
        email = weblet.member.email
    if email or payer_email:
        subject = _("New reservation of %s done" % reservation.post)
        try:
            html_content = get_mail_content(subject, template_name='enfinchezmoi/mails/payment_notice.html',
                                            extra_context={'currency_symbol': config.currency_symbol,
                                                           'post': reservation,
                                                           'payer': member,
                                                           'tx_date': tx.updated_on.strftime('%Y-%m-%d'),
                                                           'tx_time': tx.updated_on.strftime('%H:%M:%S')})
            sender = '%s <no-reply@%s>' % (weblet.project_name, weblet.domain)
            msg = EmailMessage(subject, html_content, sender, [payer_email])
            msg.bcc = [email]
            msg.content_subtype = "html"
            if getattr(settings, 'UNIT_TESTING', False):
                msg.send()
            else:
                Thread(target=lambda m: m.send(), args=(msg,)).start()
        except:
            logger.error("%s - Failed to send notice mail to %s." % (weblet, email), exc_info=True)

    # if member.email:
    #     activate(member.language)
    #     invoice_url = ikwen_service.url + reverse('billing:invoice_detail', args=(invoice.id,))
    #     subject, message, sms_text = get_payment_confirmation_message(payment, member)
    #     html_content = get_mail_content(subject, message, service=vendor, template_name='billing/mails/notice.html',
    #                                     extra_context={'member_name': member.first_name, 'invoice': invoice,
    #                                                    'cta': _("View invoice"), 'invoice_url': invoice_url,
    #                                                    'early_payment': is_early_payment})
    #     sender = '%s <no-reply@%s>' % (vendor.config.company_name, ikwen_service.domain)
    #     msg = XEmailMessage(subject, html_content, sender, [member.email])
    #     if vendor != ikwen_service and not vendor_is_dara:
    #         msg.service = vendor
    #     if invoice_pdf_file:
    #         msg.attach_file(invoice_pdf_file)
    #     msg.content_subtype = "html"
    #     if getattr(settings, 'UNIT_TESTING', False):
    #         msg.send()
    #     else:
    #         Thread(target=lambda m: m.send(), args=(msg,)).start()
    return HttpResponse("Notification received")


class SubmitAd(ChangeObjectBase):
    template_name = 'enfinchezmoi/submit_ad.html'
    model_admin = PostAdmin
    model = Post
    context_object_name = 'post'

    def get(self, request, *args, **kwargs):
        action = request.GET.get('delete_photo')
        if action == 'delete_photo':
            return self.delete_photo(request)
        return super(SubmitAd, self).get(request, *args, **kwargs)

    def delete_photo(self, request, *args, **kwargs):
        post_id = request.GET.get('post_id')
        photo_id = request.GET['photo_id']
        photo = Photo(id=photo_id)
        if post_id:
            post = Post.objects.get(pk=post_id)
            if photo in post.photos:
                post.photos.remove(photo)
                post.save()
        try:
            Photo.objects.get(pk=photo_id).delete()
        except:
            pass
        return HttpResponse(
            json.dumps({'success': True}),
            content_type='application/json'
        )

    def get_context_data(self, **kwargs):
        context = super(SubmitAd, self).get_context_data(**kwargs)
        form = kwargs.get('form')
        error = kwargs.get('error')

        if form and error:
            context['form'] = form
            context['error'] = error
        context['subcategory_list'] = list(SubCategory.objects.all())
        context['city_list'] = City.objects.all()
        context['hood_list'] = Hood.objects.all()
        return context

    # @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        service = get_service_instance()
        post_admin = get_model_admin_instance(self.model, self.model_admin)
        form = SubmitAdForm(request.POST)
        if form.is_valid():
            hood = request.POST.get('hood')
            subcategory = request.POST.get('subcategory')
            surface = float(request.POST.get('surface'))
            bedroom_count = request.POST.get('bedroom_count')
            bathroom_count = request.POST.get('bathroom_count')
            kitchen_count = request.POST.get('kitchen_count')
            saloon_count = request.POST.get('saloon_count')
            cost = request.POST.get('cost')
            description = request.POST.get('description')
            has_ac = request.POST.get('has_ac')
            has_cleaning_service = request.POST.get('has_cleaning_service')
            has_parking = request.POST.get('has_parking')
            has_safeguard = request.POST.get('has_safeguard')
            is_furnished = request.POST.get('is_furnished')
            is_registered = request.POST.get('is_registered')
            owner_email = request.POST.get('owner_email')
            owner_phone = request.POST.get('owner_phone')

            photos_ids = request.POST.get('photos_ids')
            photos_ids_list = photos_ids.strip(',').split(',') if photos_ids else []

            post_hood = Hood.objects.get(name=hood)
            post_subcategory = SubCategory.objects.get(name=subcategory)

            member = request.user

            owner_form = OwnerForm({'phone': owner_phone, 'email': owner_email})

            if owner_form.is_valid():
                try:
                    owner = Owner.objects.get(member=member, phone=owner_phone, email=owner_email)
                except:
                    owner = Owner.objects.create(member=member, phone=owner_phone, email=owner_email)
            else:
                context = self.get_context_data(**kwargs)
                context['model_admin_form'] = owner_form
                error = _("Post was not created. Owner fields are invalid.")
                kwargs['error'] = error
                messages.error(request, _("Post was not created. Owner fields are invalid."))
                return render(request, self.template_name, context)

            post_owner = owner

            post = Post.objects.create(subcategory=post_subcategory, hood=post_hood, owner=post_owner, cost=cost)

            post.description = description
            post.surface = surface
            post.bedroom_count = bedroom_count
            post.bathroom_count = bathroom_count
            post.kitchen_count = kitchen_count
            post.saloon_count = saloon_count

            if has_ac:
                post.has_ac = has_ac

            if has_cleaning_service:
                post.has_cleaning_service = has_cleaning_service

            if has_parking:
                post.has_parking = has_parking

            if has_safeguard:
                post.has_safeguard = has_safeguard

            if is_furnished:
                post.is_furnished = is_furnished

            if is_registered:
                post.is_registered = is_registered

            post.save(bedroom_count, bathroom_count, kitchen_count, saloon_count)

            post.photos = []

            for photo_id in photos_ids_list:
                if photo_id:
                    try:
                        photo = Photo.objects.get(pk=photo_id)
                        post.photos.append(photo)
                    except:
                        pass

            post.save()

            next_url = reverse('home')
            messages.success(request, _("Post %s successfully created." % post))
            # mark_duplicates(post)
            # tag = '__' + category.slug
            # category_auto_profile_tag, update = ProfileTag.objects.get_or_create(name=category.name, slug=tag,
            #                                                                      is_auto=True)
            # auto_profiletag_id_list = [category_auto_profile_tag.id]
            # revival_mail_renderer = 'ikwen_kakocase.kako.utils.render_posts_added'
            #
            # self.save_object_profile_tags(request, post, auto_profiletag_id_list=auto_profiletag_id_list,
            #                               do_revive=do_revive, revival_mail_renderer=revival_mail_renderer, **kwargs)
            return HttpResponseRedirect(next_url + '?post_added=yes')
        else:
            context = self.get_context_data(**kwargs)
            # admin_form = helpers.AdminForm(form, list(post_admin.get_fieldsets(self.request)),
            #                                post_admin.get_prepopulated_fields(self.request),
            #                                post_admin.get_readonly_fields(self.request))
            # context['model_admin_form'] = admin_form
            context['form'] = form
            error = _("Post was not created. One ore more fields are invalid.")
            context['error'] = error
            messages.error(request, _("Post was not created. One ore more fields are invalid."))
            return render(request, self.template_name, context)


class PostList(HybridListView):
    """
    Here is the admin post list view.
    """
    model = Post
    ordering = ('-id',)
    list_filter = ('subcategory', 'hood', 'surface', 'cost', 'owner',)


class CityList(HybridListView):
    """
    Here is the admin city list view.
    """
    model = City
    ordering = ('name',)


class HoodList(HybridListView):
    """
    Here is the admin hood list view.
    """
    model = Hood
    ordering = ('name',)
    list_filter = ('city',)


class CategoryList(HybridListView):
    """
    Here is the admin category list view.
    """
    model = Category
    ordering = ('name',)


class SubCategoryList(HybridListView):
    """
    Here is the admin subcategory list view.
    """
    model = SubCategory
    ordering = ('name',)
    list_filter = ('category',)


class ChangePost(ChangeObjectBase):
    model = Post
    model_admin = PostAdmin
    label_field = 'subcategory'


class ChangeCity(ChangeObjectBase):
    model = City
    model_admin = CityAdmin


class ChangeHood(ChangeObjectBase):
    model = Hood
    model_admin = HoodAdmin


class ChangeCategory(ChangeObjectBase):
    model = Category
    model_admin = CategoryAdmin


class ChangeSubCategory(ChangeObjectBase):
    model = SubCategory
    model_admin = SubCategoryAdmin


class ChangeOwner(ChangeObjectBase):
    model = Owner
    model_admin = OwnerAdmin


class ChangeReservation(ChangeObjectBase):
    model = Reservation
    model_admin = ReservationAdmin


class ReservationList(HybridListView):
    model = Reservation
    list_filter = ('post', 'start_on', 'end_on', 'status')


# class PaymentList(HybridListView):
#     model = Payment


