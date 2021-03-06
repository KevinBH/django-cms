# -*- coding: utf-8 -*-
from distutils.version import LooseVersion

from classytags.arguments import Argument
from classytags.core import Options, Tag
from classytags.helpers import InclusionTag
from cms.utils import get_cms_setting
from cms.utils.admin import get_admin_menu_item_context
from cms.utils.permissions import get_any_page_view_permissions
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext
import django


register = template.Library()

if LooseVersion(django.get_version()) < LooseVersion('1.4'):
    CMS_ADMIN_ICON_BASE = "%sadmin/img/admin/" % settings.STATIC_URL
else:
    CMS_ADMIN_ICON_BASE = "%sadmin/img/" % settings.STATIC_URL


class ShowAdminMenu(InclusionTag):
    name = 'show_admin_menu'
    template = 'admin/cms/page/tree/menu.html'

    options = Options(
        Argument('page')
    )

    def get_context(self, context, page):
        request = context['request']

        if context.has_key("cl"):
            filtered = context['cl'].is_filtered()
        elif context.has_key('filtered'):
            filtered = context['filtered']



        # following function is newly used for getting the context per item (line)
        # if something more will be required, then get_admin_menu_item_context
        # function have to be updated. 
        # This is done because item can be reloaded after some action over ajax.
        context.update(get_admin_menu_item_context(request, page, filtered))

        # this here is just context specific for menu rendering - items itself does
        # not use any of following variables
        #context.update({
        #    'no_children': no_children,
        #})
        return context


register.tag(ShowAdminMenu)


class ShowLazyAdminMenu(InclusionTag):
    name = 'show_lazy_admin_menu'
    template = 'admin/cms/page/tree/lazy_child_menu.html'

    options = Options(
        Argument('page')
    )

    def get_context(self, context, page):
        request = context['request']

        if context.has_key("cl"):
            filtered = context['cl'].is_filtered()
        elif context.has_key('filtered'):
            filtered = context['filtered']



        # following function is newly used for getting the context per item (line)
        # if something more will be required, then get_admin_menu_item_context
        # function have to be updated. 
        # This is done because item can be reloaded after some action over ajax.
        context.update(get_admin_menu_item_context(request, page, filtered))

        # this here is just context specific for menu rendering - items itself does
        # not use any of following variables
        #context.update({
        #    'no_children': no_children,
        #})
        return context


register.tag(ShowLazyAdminMenu)


class CleanAdminListFilter(InclusionTag):
    """
    used in admin to display only these users that have actually edited a page
    and not everybody
    """
    name = 'clean_admin_list_filter'
    template = 'admin/filter.html'

    options = Options(
        Argument('cl'),
        Argument('spec'),
    )

    def get_context(self, context, cl, spec):
        choices = sorted(list(spec.choices(cl)), key=lambda k: k['query_string'])
        query_string = None
        unique_choices = []
        for choice in choices:
            if choice['query_string'] != query_string:
                unique_choices.append(choice)
                query_string = choice['query_string']
        return {'title': spec.title, 'choices': unique_choices}


register.tag(CleanAdminListFilter)


@register.filter
def boolean_icon(value):
    BOOLEAN_MAPPING = {True: 'yes', False: 'no', None: 'unknown'}
    return mark_safe(
        u'<img src="%sicon-%s.gif" alt="%s" />' % (CMS_ADMIN_ICON_BASE, BOOLEAN_MAPPING.get(value, 'unknown'), value))


@register.filter
def is_restricted(page, request):
    if get_cms_setting('PERMISSION'):
        all_perms = list(get_any_page_view_permissions(request, page))
        icon = boolean_icon(bool(all_perms))
        return mark_safe(
            ugettext('<span title="Restrictions: %(title)s">%(icon)s</span>') % {
                'title': u', '.join((perm.get_grant_on_display() for perm in all_perms)) or None,
                'icon': icon,
            })
    else:
        icon = boolean_icon(None)
        return mark_safe(
            ugettext('<span title="Restrictions: %(title)s">%(icon)s</span>') % {
                'title': None,
                'icon': icon,
            })


@register.filter
def preview_link(page, language):
    if settings.USE_I18N:

        # Which one of page.get_slug() and page.get_path() is the right
        # one to use in this block? They both seem to return the same thing.
        try:
            # attempt to retrieve the localized path/slug and return
            return page.get_absolute_url(language, fallback=False)
        except:
            # no localized path/slug. therefore nothing to preview. stay on the same page.
            # perhaps the user should be somehow notified for this.
            return ''
    return page.get_absolute_url(language)


class RenderPlugin(InclusionTag):
    template = 'cms/content.html'

    options = Options(
        Argument('plugin')
    )

    def get_context(self, context, plugin):
        return {'content': plugin.render_plugin(context, admin=True)}


register.tag(RenderPlugin)


class PageSubmitRow(InclusionTag):
    name = 'page_submit_row'
    template = 'admin/cms/page/submit_row.html'

    def get_context(self, context):
        opts = context['opts']
        change = context['change']
        is_popup = context['is_popup']
        save_as = context['save_as']
        basic_info = context.get('advanced_settings', False)
        advanced_settings = context.get('basic_info', False)
        language = context['language']
        return {
            'onclick_attrib': (opts.get_ordered_objects() and change
                               and 'onclick="submitOrderForm();"' or ''),
            'show_delete_link': False,
            'show_save_as_new': not is_popup and change and save_as,
            'show_save_and_add_another': False,
            'show_save_and_continue': not is_popup and context['has_change_permission'],
            'is_popup': is_popup,
            'basic_info': basic_info,
            'advanced_settings': advanced_settings,
            'show_save': True,
            'language': language,
            'object_id': context.get('object_id', None)
        }


register.tag(PageSubmitRow)


def in_filtered(seq1, seq2):
    return [x for x in seq1 if x in seq2]


in_filtered = register.filter('in_filtered', in_filtered)


@register.simple_tag
def admin_static_url():
    """
    If set, returns the string contained in the setting ADMIN_MEDIA_PREFIX, otherwise returns STATIC_URL + 'admin/'.
    """
    return getattr(settings, 'ADMIN_MEDIA_PREFIX', None) or ''.join([settings.STATIC_URL, 'admin/'])


class CMSAdminIconBase(Tag):
    name = 'cms_admin_icon_base'

    def render_tag(self, context):
        return CMS_ADMIN_ICON_BASE


register.tag(CMSAdminIconBase)
