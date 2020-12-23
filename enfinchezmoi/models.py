# from django.conf import settings
import datetime
import os
import random

from datetime import datetime

from django.contrib.humanize.templatetags.humanize import intcomma
from django.db import models
from django.db.models import Model, Q
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _
from djangotoolbox.fields import EmbeddedModelField, ListField

from conf.settings import LANGUAGES
from ikwen.core.constants import PENDING, CONFIRMED
from ikwen.billing.models import AbstractProduct, AbstractSubscription, AbstractPayment, InvoiceEntry
from ikwen.accesscontrol.models import Member
from ikwen.core.models import Country, Model
from ikwen.core.fields import MultiImageField


UPLOAD_TO = 'post_images'

BUSY = 'Busy'
FREE = 'Free'
STATUS_CHOICES = (
    (BUSY, _('Busy')),
    (FREE, _('Free'))
)


class Owner(Model):
    member = models.ForeignKey(Member)
    phone = models.CharField(max_length=30, blank=True, help_text=_("Fill your phone number"))
    email = models.EmailField(max_length=100)

    def __unicode__(self):
        return self.member.get_full_name()


class City(Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)

    def __unicode__(self):
        return self.name

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.slug = slugify(self.name)
        super(City, self).save()


class Hood(Model):
    city = models.ForeignKey(City)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)

    def __unicode__(self):
        return self.name

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.slug = slugify(self.name)
        super(Hood, self).save()


class Category(Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    language = models.CharField(max_length=2, choices=LANGUAGES, default='en')

    def __unicode__(self):
        return self.name

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.slug = slugify(self.name)
        super(Category, self).save()


class SubCategory(Model):
    category = models.ForeignKey(Category)
    slug = models.SlugField(unique=True, blank=True)
    name = models.CharField(null=True, max_length=100)

    def __unicode__(self):
        return self.name

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.slug = slugify(self.name)
        super(SubCategory, self).save()


class Post(AbstractProduct):
    subcategory = models.ForeignKey(SubCategory)
    owner = models.ForeignKey(Owner, null=True, blank=True)
    hood = models.ForeignKey(Hood)
    surface = models.IntegerField(null=True, blank=True, help_text=_('Surface hood in meter square'), default=0)
    bedroom_count = models.IntegerField(null=True, help_text=_('Number of bed rooms'))
    bathroom_count = models.IntegerField(null=True, help_text=_('Number of bathrooms'))
    kitchen_count = models.IntegerField(null=True, help_text=_('Number of kitchens'))
    saloon_count = models.IntegerField(null=True, help_text=_('Number of saloons'))
    room_count = models.IntegerField(default=0)
    has_ac = models.BooleanField(blank=True, null=True)
    has_parking = models.BooleanField(blank=True, null=True)
    has_safeguard = models.BooleanField(blank=True, null=True)
    has_cleaning_service = models.BooleanField(blank=True, null=True)
    is_furnished = models.BooleanField(blank=True, null=True)
    is_registered = models.BooleanField(blank=True, null=True)
    photos = ListField(EmbeddedModelField('Photo'), editable=False, help_text=_('Cover image of the <b>post</b>'),
                       verbose_name=_('Post images'))
    description = models.TextField(blank=True)
    ref_ad = models.CharField(editable=True, max_length=8)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None, bedroom_count=None, bathroom_count=None, kitchen_count=None, saloon_count=None, cost=None):

        if not self.ref_ad:
            alphabet = [chr(ord('A') + i) for i in range(26)]

            while True:
                ref = ""
                for i in range(4):
                    ref = ref + random.choice(alphabet)
                ref = ref + '-'
                for i in range(3):
                    ref = ref + str(random.choice(range(0, 9)))
                if ref not in [post.ref_ad for post in Post.objects.all()]:
                    self.ref_ad = ref
                    break
        if not bedroom_count:
            if self.bedroom_count:
                self.room_count += int(self.bedroom_count)
        else:
            self.room_count += int(bedroom_count)

        if not bathroom_count:
            if self.bathroom_count:
                self.room_count += int(self.bathroom_count)
        else:
            self.room_count += int(bathroom_count)

        if not kitchen_count:
            if self.kitchen_count:
                self.room_count += int(self.kitchen_count)
        else:
            self.room_count += int(kitchen_count)

        if not saloon_count:
            if self.saloon_count:
                self.room_count += int(self.saloon_count)
        else:
            self.room_count += int(saloon_count)
        super(Post, self).save()

    def __unicode__(self):
        hood = self.hood
        if not(self.subcategory.slug == 'terrain' and self.subcategory.slug == 'land'):
            if self.surface:
                return "%s - %s/%s - %d  m2" % (self.subcategory.name, hood.city.name, hood.name, self.surface)
            else:
                return "%s - %s/%s" % (self.subcategory.name, hood.city.name, hood.name)
        else:
            return "%s - %s/%s - %d bedrooms" % (self.subcategory.name, hood.city.name, hood.name, self.bedroom_count)

    def _get_image(self):
        return self.photos[0].image if len(self.photos) > 0 else None
    image = property(_get_image)

    def get_photos_url_list(self):
        photo_list = []
        for photo in self.photos:
            photo_list.append({
                'original': photo.image.url,
                'small': photo.image.small_url,
                'thumb': photo.image.thumb_url
            })
        return photo_list

    def get_photos_ids_list(self):
        return ','.join([photo.id for photo in self.photos])

    def delete(self, *args, **kwargs):
        for photo in self.photos:
            photo.delete(*args, **kwargs)
        super(Post, self).delete(*args, **kwargs)

    def is_available(self, start_date, end_date):
        queryset = Reservation.objects\
            .filter(Q(start_on__range=(start_date, end_date)) | Q(end_on__range=(start_date, end_date)))\
            .filter(post=self.pk, status=CONFIRMED)

        return queryset.count() == 0


class Photo(models.Model):
    UPLOAD_TO = 'post_images/photos'
    PLACE_HOLDER = 'no_photo.png'
    image = MultiImageField(upload_to=UPLOAD_TO, max_size=800)

    def delete(self, *args, **kwargs):
        try:
            os.unlink(self.image.path)
            os.unlink(self.image.small_path)
            os.unlink(self.image.thumb_path)
        except:
            pass
        super(Photo, self).delete(*args, **kwargs)

    def __unicode__(self):
        return self.image.url


class Reservation(AbstractPayment):
    member = models.ForeignKey(Member)
    post = models.ForeignKey(Post)
    status = models.CharField(max_length=100, default=PENDING)
    start_on = models.DateField(blank=True, null=True, help_text=_("Reservation start date."))
    end_on = models.DateField(blank=True, null=True, help_text=_("Reservation expiry date"))
    entries = ListField(EmbeddedModelField('InvoiceEntry'), null=True, blank=True)

    def __unicode__(self):
        return "%s : %s" % (self.post, self.member)
