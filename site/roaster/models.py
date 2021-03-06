import re

from django.core.urlresolvers import reverse
from django.db import models
from django.template.defaultfilters import slugify

WEEKDAY_CHOICES = (
    (0, 'Monday'),
    (1, 'Tuesday'),
    (2, 'Wednesday'),
    (3, 'Thursday'),
    (4, 'Friday'),
    (5, 'Saturday'),
    (6, 'Sunday'),
)

def format_phone_number(phone):
    phone = re.sub('[^\w]', '', phone)
    if (len(phone) == 10):
        return '(%s) %s-%s' % (phone[:3], phone[3:6], phone[6:10])
    return ''

# TODO: Move Business and BusinessHours models to generic app.
# TODO: Add tests

class Business(models.Model):
    name = models.CharField(max_length=200, db_index=True,)
    slug = models.SlugField()
    active = models.BooleanField()
    address = models.CharField(max_length=200, blank=True,)
    lat = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True,)
    lng = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True,)
    phone = models.CharField(max_length=14, blank=True,)
    url = models.URLField(max_length=200, verbose_name='URL', blank=True,)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    modified_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        ordering = ['name',]
        get_latest_by = 'created_at'
 
    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.pk:
            self.slug = Business.unique_slugify(self.name)

        # Sanitize the phone number
        self.phone = format_phone_number(self.phone)

        super(Business, self).save(*args, **kwargs)

    @staticmethod
    def unique_slugify(value, num=0):
        if (num > 0):
            slug = slugify("%s-%s" % (value, num))
        else:
            slug = slugify(value)
        
        try:
            Business.objects.get(slug=slug)

            # Slug is not unique!
            slug = Business.unique_slugify(value, num+1)
        except Business.DoesNotExist:
            pass

        return slug


class BusinessHours(models.Model):
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES, default=0,)
    open = models.TimeField()
    close = models.TimeField()
    business = models.ForeignKey(Business, related_name='hours',)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True,)
    modified_at = models.DateTimeField(auto_now=True, db_index=True,)

    class Meta:
        ordering = ['weekday',]
        verbose_name = 'Business Hours'
        verbose_name_plural = 'Business Hours'
        unique_together = (('weekday', 'business'),)

    def __unicode__(self):
        return "{weekday}: {open} to {close}".format(
                weekday=self.get_weekday_display(), open=self.open,
                close=self.close)

class Cafe(Business):
    def get_absolute_url(self):
        return reverse('roaster.views.cafe_details', args=[self.slug])

class Roaster(Business):
    description = models.TextField(blank=True,)
    photo_url = models.URLField(max_length=200, verbose_name='Photo URL',
            blank=True,)
    video_url = models.URLField(max_length=200, verbose_name='Video URL',
            blank=True,)
    online_only = models.BooleanField(db_index=True)
    order_online = models.BooleanField(db_index=True)
    cafe_on_site = models.BooleanField(db_index=True)
    open_to_public = models.BooleanField(db_index=True)
    cafes = models.ManyToManyField('Cafe', blank=True,
            related_name='roasters')

    def get_absolute_url(self):
        return reverse('roaster.views.roaster_details', args=[self.slug])

class Roast(models.Model):
    name = models.CharField(max_length=200, unique=True, db_index=True,)
    roaster = models.ForeignKey('Roaster', related_name='roasts',)
    active = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True,)
    modified_at = models.DateTimeField(auto_now=True, db_index=True,)

    class Meta:
        ordering = ['name',]

    def __unicode__(self):
        return self.name
