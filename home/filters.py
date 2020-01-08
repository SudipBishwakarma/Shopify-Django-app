import django_filters
from shopify_app.models import Product
from django import forms


def get_field_as_choices(store, field):
    model = Product.objects.filter(store=store).values(f'{field}').distinct()
    choices = []
    for _ in model:
        choice = _.get(f'{field}')
        if choice:
            choices.append((choice, choice))
    return choices


class ProductFilter(django_filters.FilterSet):

    def __init__(self, *args, **kwargs):
        _store = kwargs.pop('store')
        super().__init__(*args, **kwargs)
        self.filters['type'].extra['choices'] = get_field_as_choices(_store, 'type')
        self.filters['vendor'].extra['choices'] = get_field_as_choices(_store, 'vendor')

    title = django_filters.CharFilter(lookup_expr='icontains')
    type = django_filters.ChoiceFilter(choices=[],
                                       empty_label='---Select Type---',
                                       widget=forms.Select(attrs={'class': 'filter_type'}))
    vendor = django_filters.ChoiceFilter(choices=[],
                                         empty_label='---Select Vendor---',
                                         widget=forms.Select(attrs={'class': 'vendor_filter'}))

    class Meta:
        model = Product
        fields = ['title', 'vendor', 'type']
