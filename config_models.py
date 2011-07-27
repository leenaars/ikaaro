# -*- coding: UTF-8 -*-
# Copyright (C) 2011 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from itools
from itools.gettext import MSG

# Import from ikaaro
from autoedit import AutoEdit
from config import Configuration
from config_common import NewResource_Local, NewInstance_Local
from fields import Select_Field
from fields import Integer_Field, Text_Field
from folder import Folder
from resource_ import DBResource


class FieldType_Field(Select_Field):

    options = [
        {'name': 'text', 'value': MSG(u'Text')},
        {'name': 'integer', 'value': MSG(u'Integer')}]



class ModelField(DBResource):

    class_id = 'model-field'
    class_title = MSG(u'...')
    class_description = MSG(u'...')
    class_icon48 = 'icons/48x48/folder.png' # XXX

    # Fields
    fields = DBResource.fields + ['field_type']
    field_type = FieldType_Field(required=True, title=MSG(u'Field type'))

    # Views
    class_views = ['edit', 'commit_log']
    new_instance = NewInstance_Local(fields=['field_type', 'title'])
    edit = AutoEdit(fields=['field_type', 'title'])



#class ModelField_Choice(ModelField):
#
#    class_id = 'model-field-choices'
#
#    # Fields
#    fields = ModelField.fields + ['field_options']
#    field_options =



class BaseClass_Field(Select_Field):

    options = [
        {'name': 'event', 'value': MSG(u'Event')}]


class Model(Folder):

    class_id = 'model'
    class_title = MSG(u'...')
    class_description = MSG(u'...')

    # Fields
    fields = Folder.fields + ['base_class']
    base_class = BaseClass_Field(required=True, title=MSG(u'Base class'))
    title = Folder.title(required=True)

    # Views
    class_views = ['browse_content', 'add_field', 'edit', 'commit_log']
    new_instance = NewInstance_Local(fields=['base_class', 'title'])
    add_field = NewResource_Local(title=MSG(u'Add field'))

    def get_document_types(self):
        return [ModelField]#, ModelField_Choice]


    def build_resource_class(self):
        fields_map = {
            'text': Text_Field,
            'integer': Integer_Field}

        # bases
        base_class = self.get_value('base_class')
        base_class = self.database.get_resource_class(base_class)
        bases = (base_class,)
        # dict
        class_dict = {
            'class_id': str(self.abspath),
            'class_title': MSG(self.get_value('title'))}
        fields = []
        for field in self.get_resources():
            field_type = field.get_value('field_type')
            class_dict[field.name] = fields_map[field_type]
            fields.append(field.name)
        class_dict['fields'] = base_class.fields + fields

        return type(self.name, bases, class_dict)


###########################################################################
# The configuration plugin
###########################################################################
class Config_Models(Folder):

    class_id = 'config-models'
    class_title = MSG(u'Content models')
    class_description = MSG(u'Define new types of content resources.')

    # Configuration
    config_name = 'models'
    config_group = 'content'

    # Views
    class_views = ['browse_content', 'add_model', 'edit', 'commit_log']
    add_model = NewResource_Local(title=MSG(u'Add model'))

    def get_document_types(self):
        return [Model]


Configuration.register_plugin(Config_Models)
