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

import mock

from nova import context
from nova.objects import geo_tags
from nova.openstack.common import timeutils
from nova.tests.objects import test_objects


NOW = timeutils.utcnow().replace(microsecond=0)


def fake_db_geo_tag(**updates):
    db_instance = {
            'server_name': 'server',
            'valid_invalid': 'Valid',
            'ip_address': None,
            'mac_address': None,
            'parent_mac': None,
            'plt_latitude': '12.22',
            'plt_longitude': '13.33',
            'deleted': 0,
            'deleted_at': NOW,
            'created_at': NOW,
            'updated_at': NOW,
            'rfid': None,
            'alerts': 0,
            'rfid_signature': None,
            'id': 1
            }

    if updates:
        db_instance.update(updates)
    return db_instance


class _TestGeoTagObject(object):

    @mock.patch('nova.db.geo_tag_get_by_id')
    def test_get_by_id(self, db_mock):
        ctxt = context.get_admin_context()
        fake_tag = fake_db_geo_tag()
        db_mock.return_value = fake_tag
        tag = geo_tags.GeoTag.get_by_id(ctxt, fake_tag['id'])
        self.compare_obj(tag, fake_tag)
        db_mock.assert_called_once_with(ctxt, fake_tag['id'])

    @mock.patch('nova.db.geo_tag_get_by_node_name')
    def test_get_by_id(self, db_mock):
        ctxt = context.get_admin_context()
        fake_tag = fake_db_geo_tag()
        db_mock.return_value = fake_tag
        tag = geo_tags.GeoTag.get_by_node_name(ctxt, fake_tag['server_name'])
        self.compare_obj(tag, fake_tag)
        db_mock.assert_called_once_with(ctxt, fake_tag['server_name'])

    @mock.patch('nova.db.geo_tag_create')
    def test_create(self, db_mock):
        ctxt = context.get_admin_context()
        fake_tag = fake_db_geo_tag()
        db_mock.return_value = fake_tag
        gt = geo_tags.GeoTag()
        gt.server_name = 'TestServer'
        gt.valid_invalid = 'Valid'
        gt.create(ctxt)
        db_mock.assert_called_once_with(ctxt, {'server_name': 'TestServer',
                                               'valid_invalid': 'Valid'})

    @mock.patch('nova.db.geo_tag_update')
    def test_save(self, db_mock):
        ctxt = context.get_admin_context()
        fake_tag = fake_db_geo_tag()
        db_mock.return_value = fake_tag
        gt = geo_tags.GeoTag()
        gt.id = 22
        gt.server_name = 'TestServer'
        gt.valid_invalid = 'Valid'
        gt.save(ctxt)
        db_mock.assert_called_once_with(ctxt, 22,
                                        {'server_name': 'TestServer',
                                         'valid_invalid': 'Valid'})

    @mock.patch('nova.db.geo_tag_destroy')
    def test_delete(self, db_mock):
        ctxt = context.get_admin_context()
        fake_tag = fake_db_geo_tag()
        db_mock.return_value = fake_tag
        gt = geo_tags.GeoTag()
        gt.id = 22
        gt.destroy(ctxt)
        db_mock.assert_called_once_with(ctxt, 22)


class TestGeoTagsObject(test_objects._LocalTest,
                          _TestGeoTagObject):
    pass


class TestRemoteGeoTagsObject(test_objects._RemoteTest,
                                _TestGeoTagObject):
    pass
