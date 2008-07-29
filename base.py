# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006-2007 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
# Copyright (C) 2007 Sylvain Taverne <sylvain@itaapy.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Import from the Standard Library
from datetime import datetime

# Import from itools
from itools.catalog import (CatalogAware, TextField, KeywordField,
    IntegerField, BoolField)
from itools.datatypes import FileName, String, Unicode, Integer, is_datatype
from itools.gettext import DomainAware, get_domain
from itools.handlers import checkid
from itools.http import Forbidden
from itools.i18n import get_language_name
from itools.stl import stl
from itools import vfs
from itools.web import get_context, Node as BaseNode
from itools.uri import Path
from itools.i18n import format_datetime
from itools.xml import XMLParser

# Import from ikaaro
from lock import Lock, lock_body
from messages import *
from metadata import Metadata
from registry import get_object_class
from workflow import WorkflowAware
from utils import reduce_string



class Node(BaseNode):

    class_views = []

    ########################################################################
    # HTTP
    ########################################################################
    def get_method(self, name):
        try:
            method = getattr(self, name)
        except AttributeError:
            return None
        return method


    GET__access__ = 'is_allowed_to_view'
    def GET(self, context):
        method = self.get_firstview()
        # Check access
        if method is None:
            raise Forbidden

        # Redirect
        return context.uri.resolve2(';%s' % method)


    POST__access__ = 'is_authenticated'
    def POST(self, context):
        for name in context.get_form_keys():
            if name.startswith(';'):
                method_name = name[1:]
                method = self.get_method(method_name)
                if method is None:
                    # XXX When the method is not defined, is it the best
                    # thing to do a Not-Found error?
                    # XXX Send a 404 status code.
                    return context.root.not_found(context)
                # Check security
                user = context.user
                ac = self.get_access_control()
                if not ac.is_access_allowed(user, self, method_name):
                    raise Forbidden
                # Call the method
                return method(context)

        raise Exception, 'the form did not define the action to do'


    ########################################################################
    # Tree
    ########################################################################
    def get_site_root(self):
        from website import WebSite
        object = self
        while not isinstance(object, WebSite):
            object = object.parent
        return object


    ########################################################################
    # Properties
    ########################################################################
    def get_property_and_language(self, name, language=None):
        return None, None


    def get_property(self, name, language=None):
        return self.get_property_and_language(name, language=language)[0]


    def get_title(self):
        return self.name


    ########################################################################
    # Icons
    ########################################################################
    @classmethod
    def get_class_icon(cls, size=16):
        icon = getattr(cls, 'class_icon%s' % size, None)
        if icon is None:
            return None
        return '/ui/%s' % icon


    @classmethod
    def get_object_icon(cls, size=16):
        icon = getattr(cls, 'icon%s' % size, None)
        if icon is None:
            return cls.get_class_icon(size)
        return ';icon%s' % size


    def get_method_icon(self, method_name, size='16x16', **kw):
        icon = getattr(self, '%s__icon__' % method_name, None)
        if icon is None:
            return None
        if callable(icon):
            icon = icon(**kw)
        if icon.startswith('/ui/'):
            return icon
        return '/ui/icons/%s/%s' % (size, icon)


    # FIXME For backwards compatibility (replaced by 'get_object_icon'), to
    # remove by 0.30
    @classmethod
    def get_path_to_icon(cls, size=16):
        return cls.get_object_icon(size)


    ########################################################################
    # Internationalization
    ########################################################################
    class_domain = 'ikaaro'

    @classmethod
    def select_language(cls, languages):
        accept = get_context().accept_language
        return accept.select_language(languages)


    @classmethod
    def gettext(cls, message, language=None):
        gettext = DomainAware.gettext

        if cls.class_domain == 'ikaaro':
            domain_names = ['ikaaro']
        else:
            domain_names = [cls.class_domain, 'ikaaro']

        for domain_name in domain_names:
            if language is None:
                domain = get_domain(domain_name)
                languages = domain.get_languages()
                language = cls.select_language(languages)

            translation = gettext(message, language, domain=domain_name)
            if translation != message:
                return translation

        return message


    ########################################################################
    # User interface
    ########################################################################
    def get_firstview(self):
        """Returns the first allowed object view url, or None if there
        aren't.
        """
        for view in self.get_views():
            return view
        return None


    def get_views(self):
        user = get_context().user
        ac = self.get_access_control()
        for view in self.class_views:
            view = view[0]
            name = view.split('?')[0]
            if ac.is_access_allowed(user, self, name):
                yield view


    def get_subviews(self, name):
        for block in self.class_views:
            if name in block:
                if len(block) == 1:
                    return []
                return block[:]
        return []



class DBObject(CatalogAware, Node, DomainAware):

    def __init__(self, metadata):
        self.metadata = metadata
        self._handler = None
        # The tree
        self.name = ''
        self.parent = None


    @staticmethod
    def make_object(cls, container, name, *args, **kw):
        cls._make_object(cls, container.handler, name, *args, **kw)
        object = container.get_object(name)
        # Events, add
        get_context().server.add_object(object)

        return object


    @staticmethod
    def _make_object(cls, folder, name, **kw):
        metadata = cls.build_metadata(**kw)
        folder.set_handler('%s.metadata' % name, metadata)


    def get_handler(self):
        if self._handler is None:
            cls = self.class_handler
            database = self.metadata.database
            if self.parent is None:
                uri = self.metadata.uri.resolve('.')
            else:
                uri = self.metadata.uri.resolve(self.name)
            if database.has_handler(uri):
                self._handler = database.get_handler(uri, cls=cls)
            else:
                handler = cls()
                handler.database = database
                handler.uri = uri
                handler.timestamp = None
                handler.dirty = datetime.now()
                database.cache[uri] = handler
                self._handler = handler
        return self._handler

    handler = property(get_handler, None, None, '')


    ########################################################################
    # Metadata
    ########################################################################
    @classmethod
    def get_metadata_schema(cls):
        return {
            'title': Unicode,
            'description': Unicode,
            'subject': Unicode,
            }


    def has_property(self, name, language=None):
        return self.metadata.has_property(name, language=language)


    def get_property_and_language(self, name, language=None):
        return self.metadata.get_property_and_language(name, language=language)


    def set_property(self, name, value, language=None):
        get_context().server.change_object(self)
        self.metadata.set_property(name, value, language=language)


    def del_property(self, name, language=None):
        get_context().server.change_object(self)
        self.metadata.del_property(name, language=language)


    ########################################################################
    # Indexing
    ########################################################################
    def to_text(self):
        raise NotImplementedError


    def get_catalog_fields(self):
        return [
            KeywordField('abspath', is_stored=True),
            TextField('text'),
            TextField('title', is_stored=True),
            BoolField('is_role_aware'),
            KeywordField('format', is_stored=True),
            KeywordField('workflow_state', is_stored=True),
            KeywordField('members'),
            # For referencial-integrity, keep links between cms objects, where
            # a link is the physical path.
            KeywordField('links'),
            # Folder's view
            KeywordField('parent_path'),
            KeywordField('paths'),
            KeywordField('name', is_stored=True),
            KeywordField('mtime', is_indexed=True, is_stored=True),
            IntegerField('size', is_indexed=False, is_stored=True)]


    def get_catalog_values(self):
        from access import RoleAware
        from file import File

        abspath = self.get_canonical_path()
        mtime = self.get_mtime()
        if mtime is None:
            mtime = datetime.now()

        document = {
            'name': self.name,
            'abspath': str(abspath),
            'format': self.metadata.format,
            'title': self.get_title(),
            'mtime': mtime.strftime('%Y%m%d%H%M%S')}

        # Full text
        try:
            text = self.to_text()
        except NotImplementedError:
            pass
        except:
            context = get_context()
            if context is not None:
                context.server.log_error(context)
        else:
            document['text'] = text

        # Links
        document['links'] = self.get_links()

        # Parent path
        if str(abspath) != '/':
            parent_path = abspath.resolve2('..')
            document['parent_path'] = str(parent_path)

        # All paths
        document['paths'] = [ abspath[:x] for x in range(len(abspath) + 1) ]

        # Size
        if isinstance(self, File):
            # FIXME We add an arbitrary size so files will always be bigger
            # than folders. This won't work when there is a folder with more
            # than that size.
            document['size'] = 2**30 + self.get_size()
        else:
            names = self.get_names()
            document['size'] = len(names)

        # Workflow state
        if isinstance(self, WorkflowAware):
            document['workflow_state'] = self.get_workflow_state()

        # Role Aware
        if isinstance(self, RoleAware):
            document['is_role_aware'] = True
            document['members'] = self.get_members()

        return document


    ########################################################################
    # API
    ########################################################################
    def get_handlers(self):
        """Return all the handlers attached to this object, except the
        metadata.
        """
        return [self.handler]


    def rename_handlers(self, new_name):
        """Consider we want to rename this object to the given 'new_name',
        return the old a new names for all the attached handlers (except the
        metadata).

        This method is required by the "move_object" method.
        """
        return [(self.name, new_name)]


    def get_mtime(self):
        handlers = [self.metadata] + self.get_handlers()

        mtimes = []
        for handler in handlers:
            if handler is not None:
                mtime = handler.get_mtime()
                if mtime is not None:
                    mtimes.append(mtime)

        if not mtimes:
            return None
        return max(mtimes)


    def get_links(self):
        return []


    ########################################################################
    # Upgrade
    ########################################################################
    def get_next_versions(self):
        cls_version = self.class_version
        obj_version = self.metadata.version
        # Set zero version if the object does not have a version
        if obj_version is None:
            obj_version = '00000000'

        # Get all the version numbers
        versions = []
        for cls in self.__class__.mro():
            for name in cls.__dict__.keys():
                if not name.startswith('update_'):
                    continue
                kk, version = name.split('_', 1)
                if len(version) != 8:
                    continue
                try:
                    int(version)
                except ValueError:
                    continue
                if version > obj_version and version <= cls_version:
                    versions.append(version)

        versions.sort()
        return versions


    def update(self, version):
        # We don't check the version is good
        getattr(self, 'update_%s' % version)()
        metadata = self.metadata
        metadata.set_changed()
        metadata.version = version


    ########################################################################
    # Locking
    ########################################################################
    def lock(self):
        lock = Lock(username=get_context().user.name)

        self = self.get_real_object()
        if self.parent is None:
            self.handler.set_handler('.lock', lock)
        else:
            self.parent.handler.set_handler('%s.lock' % self.name, lock)

        return lock.key


    def unlock(self):
        self = self.get_real_object()
        if self.parent is None:
            self.handler.del_handler('.lock')
        else:
            self.parent.handler.del_handler('%s.lock' % self.name)


    def is_locked(self):
        self = self.get_real_object()
        if self.parent is None:
            return self.handler.has_handler('.lock')
        return self.parent.handler.has_handler('%s.lock' % self.name)


    def get_lock(self):
        self = self.get_real_object()
        if self.parent is None:
            return self.handler.get_handler('.lock')
        return self.parent.handler.get_handler('%s.lock' % self.name)


    ########################################################################
    # HTTP
    ########################################################################
    PUT__access__ = 'is_authenticated'
    def PUT(self, context):
        # Save the data
        body = context.get_form_value('body')
        self.handler.load_state_from_string(body)
        context.server.change_object(self)


    LOCK__access__ = 'is_authenticated'
    def LOCK(self, context):
        if self.is_locked():
            return None
        # Lock the resource
        lock = self.lock()
        # Build response
        response = context.response
        response.set_header('Content-Type', 'text/xml; charset="utf-8"')
        response.set_header('Lock-Token', 'opaquelocktoken:%s' % lock)

        return lock_body % {'owner': context.user.name, 'locktoken': lock}


    UNLOCK__access__ = 'is_authenticated'
    def UNLOCK(self, context):
        # Check wether the resource is locked
        if not self.is_locked():
            # XXX Send some nice response to the client
            raise ValueError, 'resource is not locked'

        # Check wether we have the right key
        request = context.request
        key = request.get_header('Lock-Token')
        key = key[len('opaquelocktoken:'):]

        lock = self.get_lock()
        if lock.key != key:
            # XXX Send some nice response to the client
            raise ValueError, 'can not unlock resource, wrong key'

        # Unlock the resource
        self.unlock()


    ########################################################################
    # User interface
    ########################################################################
    @staticmethod
    def new_instance_form(cls, context):
        root = context.root
        # Build the namespace
        namespace = {}
        namespace['title'] = context.get_form_value('title', type=Unicode)
        namespace['name'] = context.get_form_value('name', default='')
        # The class id and title
        namespace['class_id'] = cls.class_id
        namespace['class_title'] = cls.gettext(cls.class_title)

        handler = root.get_object('ui/base/new_instance.xml')
        return stl(handler, namespace)


    @staticmethod
    def new_instance(cls, container, context):
        name = context.get_form_value('name')
        title = context.get_form_value('title', type=Unicode)

        # Check the name
        name = name.strip() or title.strip()
        if not name:
            return context.come_back(MSG_NAME_MISSING)

        name = checkid(name)
        if name is None:
            return context.come_back(MSG_BAD_NAME)

        # Check the name is free
        if container.has_object(name):
            return context.come_back(MSG_NAME_CLASH)

        object = cls.make_object(cls, container, name)
        # The metadata
        metadata = object.metadata
        language = container.get_content_language(context)
        metadata.set_property('title', title, language=language)

        goto = './%s/;%s' % (name, object.get_firstview())
        return context.come_back(MSG_NEW_RESOURCE, goto=goto)


    def get_title(self, language=None):
        return self.get_property('title', language=language) or self.name


    def get_content_language(self, context=None):
        if context is None:
            context = get_context()

        site_root = self.get_site_root()
        languages = site_root.get_property('website_languages')
        # Check cookie
        language = context.get_cookie('language')
        if language in languages:
            return language
        # Default
        return languages[0]


    def _browse_namespace(self, object, icon_size):
        from versioning import VersioningAware
        from workflow import WorkflowAware

        line = {}
        id = self.get_canonical_path().get_pathto(object.get_abspath())
        id = str(id)
        line['id'] = id
        title = object.get_title()
        line['title_or_name'] = title
        firstview = object.get_firstview()
        if firstview is None:
            href = None
        else:
            href = '%s/;%s' % (id, firstview)
        line['name'] = (id, href)
        line['format'] = self.gettext(object.class_title)
        line['title'] = object.get_property('title')
        # Titles
        line['short_title'] = reduce_string(title, 12, 40)
        # The size
        line['size'] = object.get_human_size()
        # The url
        line['href'] = href
        # The icon
        path_to_icon = object.get_object_icon(icon_size)
        if path_to_icon.startswith(';'):
            path_to_icon = Path('%s/' % object.name).resolve(path_to_icon)
        line['img'] = path_to_icon
        # The modification time
        context = get_context()
        accept = context.accept_language
        line['mtime'] = format_datetime(object.get_mtime(), accept=accept)
        # Last author
        line['last_author'] = u''
        if isinstance(object, VersioningAware):
            revisions = object.get_revisions(context)
            if revisions:
                username = revisions[0]['username']
                try:
                    user = self.get_object('/users/%s' % username)
                except LookupError:
                    line['last_author'] = username
                else:
                    line['last_author'] = user.get_title()

        # The workflow state
        line['workflow_state'] = ''
        if isinstance(object, WorkflowAware):
            statename = object.get_statename()
            state = object.get_state()
            msg = self.gettext(state['title']).encode('utf-8')
            state = ('<a href="%s/;state_form" class="workflow">'
                     '<strong class="wf_%s">%s</strong>'
                     '</a>') % (self.get_pathto(object), statename, msg)
            line['workflow_state'] = XMLParser(state)
        # Objects that should not be removed/renamed/etc
        parent = object.parent
        if parent is None:
            line['checkbox'] = False
        else:
            line['checkbox'] = object.name not in parent.__fixed_handlers__

        return line


    def browse_namespace(self, icon_size, sortby=['title'], sortorder='up',
                         batchsize=20, query=None, results=None):
        from widgets import batch

        context = get_context()
        # Load variables from the request
        start = context.get_form_value('batchstart', type=Integer, default=0)
        size = context.get_form_value('batchsize', type=Integer,
                                      default=batchsize)

        # Search
        root = context.root
        if results is None:
            results = root.search(query)

        reverse = (sortorder == 'down')
        if sortby in ('order', ['order']):
            # TODO a catalog index would help
            # but requires reindexing a single index at once
            bulk = results.get_documents()
            ordered = self.get_ordered_objects(bulk, mode='mixed',
                                               reverse=reverse)
            if size > 0:
                documents = ordered[start:start+size]
            elif start > 0:
                documents = ordered[start:]
            else:
                documents = ordered
        else:
            documents = results.get_documents(sort_by=sortby, reverse=reverse,
                                              start=start, size=size)

        # Get the objects, check security
        user = context.user
        objects = []
        for document in documents:
            object = root.get_object(document.abspath)
            ac = object.get_access_control()
            if ac.is_allowed_to_view(user, object):
                objects.append(object)

        # Get the object for the visible documents and extracts values
        object_lines = []
        for object in objects:
            line = self._browse_namespace(object, icon_size)
            object_lines.append(line)

        # Build namespace
        namespace = {}
        total = results.get_n_documents()
        namespace['total'] = total
        namespace['objects'] = object_lines

        # The batch
        namespace['batch'] = batch(context.uri, start, size, total)

        return namespace


    ########################################################################
    # UI / Metadata
    ########################################################################
    @classmethod
    def build_metadata(cls, format=None, **kw):
        """Return a Metadata object with sensible default values.
        """
        if format is None:
            format = cls.class_id

        if isinstance(cls, WorkflowAware):
            kw['state'] = cls.workflow.initstate

        return Metadata(handler_class=cls, format=format, **kw)


    edit_metadata_form__access__ = 'is_allowed_to_edit'
    edit_metadata_form__label__ = u'Metadata'
    edit_metadata_form__sublabel__ = u'Metadata'
    edit_metadata_form__icon__ = 'metadata.png'
    def edit_metadata_form(self, context):
        # Build the namespace
        namespace = {}
        # Language
        language = self.get_content_language(context)
        language_name = get_language_name(language)
        namespace['language_name'] = self.gettext(language_name)
        # Title, Description, Subject
        for name in 'title', 'description', 'subject':
            namespace[name] = self.get_property(name, language=language)

        handler = self.get_object('/ui/base/edit_metadata.xml')
        return stl(handler, namespace)


    edit_metadata__access__ = 'is_allowed_to_edit'
    def edit_metadata(self, context):
        title = context.get_form_value('title', type=Unicode)
        description = context.get_form_value('description', type=Unicode)
        subject = context.get_form_value('subject', type=Unicode)
        language = self.get_content_language(context)
        self.set_property('title', title, language=language)
        self.set_property('description', description, language=language)
        self.set_property('subject', subject, language=language)

        return context.come_back(MSG_CHANGES_SAVED)


    ########################################################################
    # UI / Rich Text Editor
    ########################################################################
    @classmethod
    def get_rte_css(cls, context):
        css_names = ['/ui/aruni/aruni.css', '/ui/tiny_mce/content.css']
        css = []
        here = context.object
        root = context.root
        for name in css_names:
            handler = root.get_object(name)
            css.append(str(here.get_pathto(handler)))
        return ','.join(css)


    @classmethod
    def get_rte(cls, context, name, data, template='/ui/tiny_mce/rte.xml'):
        namespace = {}
        namespace['form_name'] = name
        namespace['js_data'] = data
        namespace['scripts'] = ['/ui/tiny_mce/tiny_mce_src.js',
                                '/ui/tiny_mce/javascript.js']
        namespace['css'] = cls.get_rte_css(context)
        # Dressable
        dress_name = context.get_form_value('dress_name')
        namespace['dress_name'] = dress_name
        # TODO language

        here = context.object.get_abspath()
        prefix = here.get_pathto(template)

        handler = context.root.get_object(template)
        return stl(handler, namespace, prefix=prefix)


    #######################################################################
    # UI / Edit / Inline / toolbox: add images
    #######################################################################
    addimage_form__access__ = 'is_allowed_to_edit'
    def addimage_form(self, context):
        from file import File
        from binary import Image
        from widgets import Breadcrumb

        # Build the bc
        if isinstance(self, File):
            start = self.parent
        else:
            start = self

        # Construct namespace
        namespace = {}
        namespace['bc'] = Breadcrumb(filter_type=Image, start=start,
                                     icon_size=48)
        namespace['message'] = context.get_form_value('message')
        mode = context.get_form_value('mode', default='html')
        namespace['mode'] = mode
        if mode == 'wiki':
            scripts = ['/ui/wiki/javascript.js']
        else:
            scripts = ['/ui/tiny_mce/javascript.js',
                       '/ui/tiny_mce/tiny_mce_src.js',
                       '/ui/tiny_mce/tiny_mce_popup.js']
        namespace['scripts'] = scripts
        namespace['caption'] = self.gettext(MSG_CAPTION).encode('utf_8')

        template = self.get_object('/ui/html/addimage.xml')
        prefix = self.get_pathto(template)
        return stl(template, namespace, prefix=prefix)


    addimage__access__ = 'is_allowed_to_edit'
    def addimage(self, context):
        """Allow to upload and add an image to epoz
        """
        from binary import Image
        root = context.root
        # Get the container
        container = root.get_object(context.get_form_value('target_path'))
        # Add the image to the object
        uri = Image.new_instance(Image, container, context)
        if ';addimage_form' not in uri.path:
            caption = self.gettext(MSG_CAPTION).encode('utf_8')
            mode = context.get_form_value('mode', default='html')
            if mode == 'wiki':
                scripts = ['/ui/wiki/javascript.js']
            else:
                scripts = ['/ui/tiny_mce/javascript.js',
                           '/ui/tiny_mce/tiny_mce_src.js',
                           '/ui/tiny_mce/tiny_mce_popup.js']

            object = container.get_object(uri.path[0])
            path = context.object.get_pathto(object)
            script_template = '<script type="text/javascript" src="%s" />'
            body = ''
            for script in scripts:
                body += script_template % script

            body += """
                <script type="text/javascript">
                    select_img('%s', '%s');
                </script>"""
            return body % (path, caption)

        return context.come_back(message=uri.query['message'])


    #######################################################################
    # UI / Edit / Inline / toolbox: add links
    #######################################################################
    addlink_form__access__ = 'is_allowed_to_edit'
    def addlink_form(self, context):
        from file import File
        from widgets import Breadcrumb

        # Build the bc
        if isinstance(self, File):
            start = self.parent
        else:
            start = self

        # Construct namespace
        namespace = {}
        namespace['bc'] = Breadcrumb(filter_type=File, start=start,
                                     icon_size=48)
        namespace['message'] = context.get_form_value('message')
        mode = context.get_form_value('mode', default='html')
        namespace['mode'] = mode
        if mode == 'wiki':
            scripts = ['/ui/wiki/javascript.js']
            type = 'WikiPage'
        else:
            scripts = ['/ui/tiny_mce/javascript.js',
                       '/ui/tiny_mce/tiny_mce_src.js',
                       '/ui/tiny_mce/tiny_mce_popup.js']
            type = 'application/xhtml+xml'
        namespace['scripts'] = scripts
        namespace['type'] = type
        namespace['wiki_mode'] = (mode == 'wiki')

        template = self.get_object('/ui/html/addlink.xml')
        prefix = self.get_pathto(template)
        return stl(template, namespace, prefix=prefix)


    addlink__access__ = 'is_allowed_to_edit'
    def addlink(self, context):
        """Allow to upload a file and link it to epoz
        """
        # Get the container
        root = context.root
        container = root.get_object(context.get_form_value('target_path'))
        # Add the file to the object
        class_id = context.get_form_value('type')
        cls = get_object_class(class_id)
        uri = cls.new_instance(cls, container, context)
        if ';addlink_form' not in uri.path:
            mode = context.get_form_value('mode', default='html')
            if mode == 'wiki':
                scripts = ['/ui/wiki/javascript.js']
            else:
                scripts = ['/ui/tiny_mce/javascript.js',
                           '/ui/tiny_mce/tiny_mce_src.js',
                           '/ui/tiny_mce/tiny_mce_popup.js']

            object = container.get_object(uri.path[0])
            path = context.object.get_pathto(object)
            script_template = '<script type="text/javascript" src="%s" />'
            body = ''
            for script in scripts:
                body += script_template % script

            body += """
                <script type="text/javascript">
                    select_link('%s');
                </script>"""
            return body % path

        return context.come_back(message=uri.query['message'])


    #######################################################################
    # Update
    #######################################################################
    def update_20071215(self, remove=None, rename=()):
        metadata = self.metadata
        properties = metadata.properties

        schema = self.get_metadata_schema()

        metadata.set_changed()

        # Default values
        if remove is None:
            remove = ['id', 'owner', 'dc:language', 'ikaaro:user_theme']

        # The version is now an attribute
        if 'version' in properties:
            metadata.version = properties.pop('version')

        # Remove obsolete properties
        for name in remove:
            if name in properties:
                del properties[name]

        # Rename (when changing a name for another)
        for src, dst in rename:
            if src in properties:
                properties[dst] = properties.pop(src)

        # Rename (when removing the prefix is enough)
        names = properties.keys()
        for name in names:
            if ':' in name:
                new_name = name.split(':', 1)[1]
                value = properties.pop(name)
                # Skip empty values
                if isinstance(value, dict):
                    for key in value.keys():
                        if value[key].strip() == '':
                            del value[key]
                    if len(value) == 0:
                        continue
                elif isinstance(value, list):
                    pass
                elif value.strip() == '':
                    continue
                # Check the schema
                if new_name not in schema:
                    raise ValueError, 'unexpected property "%s"' % name
                datatype = schema[new_name]
                # Multilingual
                if isinstance(value, dict):
                    properties[new_name] = {}
                    for key in value:
                        properties[new_name][key] = datatype.decode(value[key])
                # Record
                elif isinstance(value, list):
                    for revision in value:
                        for subname in revision:
                            new_subname = subname.split(':', 1)[-1]
                            # Using the record schema
                            subdatatype = datatype.schema[new_subname]
                            subdata = revision.pop(subname)
                            subvalue = subdatatype.decode(subdata)
                            revision[new_subname] = subvalue
                    properties[new_name] = value
                elif is_datatype(datatype, Unicode):
                    value = datatype.decode(value).strip()
                    if value:
                        properties[new_name] = value
                else:
                    properties[new_name] = datatype.decode(value)
            else:
                if name not in schema:
                    raise ValueError, 'unexpected property "%s"' % name

