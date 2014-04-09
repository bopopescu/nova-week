# Copyright 2013 Intel Corporation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from nova import db
from nova import exception
from nova.objects import base
from nova.objects import fields
from nova.openstack.common import log as logging


LOG = logging.getLogger(__name__)


class GeoTag(base.NovaPersistentObject, base.NovaObject):

    """Object to represent GeoTag Info
    """

    # Version 1.0: Initial version
    # Version 1.1: String attributes updated to support unicode
    VERSION = '1.0'

    fields = {
        'id': fields.IntegerField(),
        'alerts': fields.IntegerField(nullable=True),
        'server_name': fields.StringField(nullable=True),
        'ip_address': fields.StringField(nullable=True),
        'mac_address': fields.StringField(nullable=True),
        'parent_mac': fields.StringField(nullable=True),
        'valid_invalid': fields.StringField(default='Valid'),
        'plt_latitude': fields.StringField(nullable=True),
        'plt_longitude': fields.StringField(nullable=True),
        'rfid': fields.StringField(nullable=True),
        'rfid_signature': fields.StringField(nullable=True)
    }

    def __init__(self, *args, **kwargs):
        super(GeoTag, self).__init__(*args, **kwargs)

    @staticmethod
    def _from_db_object(context, geo_tag, db_dev):
        if not db_dev:
            return None
        for key in geo_tag.fields:
            geo_tag[key] = db_dev[key]

        geo_tag._context = context
        geo_tag.obj_reset_changes()
        return geo_tag

    @base.remotable_classmethod
    def get_by_node_name(cls, context, name):
        db_dev = db.geo_tag_get_by_node_name(context, name)
        return cls._from_db_object(context, cls(), db_dev)

    @base.remotable_classmethod
    def get_by_id(cls, context, gt_id):
        db_dev = db.geo_tag_get_by_id(context, gt_id)
        return cls._from_db_object(context, cls(), db_dev)

    @base.remotable_classmethod
    def get_by_id_or_node_name(cls, context, gt_id):
        db_dev = db.geo_tag_get_by_id_or_node_name(context, gt_id)
        return cls._from_db_object(context, cls(), db_dev)

    @base.remotable
    def create(self, context):
        """Create a Geo Tag."""
        if self.obj_attr_is_set('id'):
            raise exception.ObjectActionError(action='create',
                                              reason='already created')
        updates = self.obj_get_changes()
        updates.pop('id', None)
        db_gtag = db.geo_tag_create(context, updates)
        self._from_db_object(context, self, db_gtag)

    @base.remotable
    def save(self, context):
        updates = self.obj_get_changes()
        """
        set notif?
        """
        updates.pop('id', None)
        db_geo_tag = db.geo_tag_update(context, self.id, updates)
        self._from_db_object(context, self, db_geo_tag)

    @base.remotable
    def destroy(self, context):
        db.geo_tag_destroy(context, self.id)


class GeoTagList(base.ObjectListBase, base.NovaObject):
    # Version 1.0: Initial version

    VERSION = '1.0'

    fields = {
        'objects': fields.ListOfObjectsField('GeoTag'),
        }
    child_versions = {}

    @base.remotable_classmethod
    def get_all(cls, context, filters=None):
        db_dev = db.geo_tag_get_all(context, filters)
        return base.obj_make_list(context, GeoTagList(), GeoTag, db_dev)

    @base.remotable_classmethod
    def get_by_filters(cls, context, filters):
        db_dev = db.geo_tags_get_all_by_filters(context, filters)
        return base.obj_make_list(context, GeoTagList(), GeoTag,
                                  db_dev)
