from django import forms
from django.utils.translation import gettext_lazy as _
from entangled.forms import EntangledModelForm

from djangocms_frontend import settings
from djangocms_frontend.common.background import BackgroundFormMixin
from djangocms_frontend.contrib import navigation
from djangocms_frontend.contrib.link.forms import AbstractLinkForm, LinkForm
from djangocms_frontend.fields import AttributesFormField, ButtonGroup, IconGroup
from djangocms_frontend.helpers import first_choice
from djangocms_frontend.models import FrontendUIItem
from djangocms_frontend.settings import NAVBAR_DESIGNS

mixin_factory = settings.get_forms(navigation)


class NavigationForm(
    mixin_factory("Navigation"),
    BackgroundFormMixin,
    EntangledModelForm,
):
    class Meta:
        model = FrontendUIItem
        entangled_fields = {
            "config": [
                "template",
                "navbar_container",
                "navbar_design",
                "navbar_breakpoint",
                "attributes",
            ]
        }
        untangled_fields = ()

    template = forms.ChoiceField(
        label=_("Template"),
        choices=settings.NAVIGATION_TEMPLATE_CHOICES,
        initial=first_choice(settings.NAVIGATION_TEMPLATE_CHOICES),
        widget=forms.HiddenInput
        if len(settings.NAVIGATION_TEMPLATE_CHOICES) < 2
        else forms.Select,
    )
    navbar_container = forms.BooleanField(
        label=_("Container"),
        required=False,
        initial=True,
    )
    navbar_design = forms.ChoiceField(
        label=_("Design"),
        required=True,
        choices=NAVBAR_DESIGNS,
        initial=first_choice(NAVBAR_DESIGNS),
        widget=ButtonGroup(attrs=dict(property="nav-design")),
    )
    navbar_breakpoint = forms.ChoiceField(
        label=_("Expand on device (and larger)"),
        required=False,
        choices=settings.EMPTY_CHOICE + settings.DEVICE_CHOICES,
        initial=settings.EMPTY_CHOICE[0][0],
        widget=IconGroup(),
    )
    attributes = AttributesFormField()


class PageTreeForm(mixin_factory("PageTree"), EntangledModelForm):
    class Meta:
        model = FrontendUIItem
        entangled_fields = {
            "config": [
                "template",
                "attributes",
            ]
        }
        untangled_fields = ()

    template = forms.ChoiceField(
        label=_("Template"),
        choices=settings.NAVIGATION_TEMPLATE_CHOICES,
        initial=first_choice(settings.NAVIGATION_TEMPLATE_CHOICES),
        widget=forms.HiddenInput
        if len(settings.NAVIGATION_TEMPLATE_CHOICES) < 2
        else forms.Select,
    )
    attributes = AttributesFormField()


class NavBrandForm(mixin_factory("NavBrand"), AbstractLinkForm, EntangledModelForm):
    class Meta:
        model = FrontendUIItem
        entangled_fields = {
            "config": [
                "simple_content",
                "attributes",
            ]
        }
        untangled_fields = ()

    simple_content = forms.CharField(
        label=_("Brand"),
        required=True,
        help_text=_("Enter brand name or add child plugins for brand icon or image"),
    )
    attributes = AttributesFormField()


class NavContainerForm(mixin_factory("NavContainer"), EntangledModelForm):
    class Meta:
        model = FrontendUIItem
        entangled_fields = {
            "config": [
                "attributes",
            ]
        }
        untangled_fields = ()

    attributes = AttributesFormField()


class NavLinkForm(mixin_factory("NavLink"), LinkForm):
    link_is_optional = True
    pass
