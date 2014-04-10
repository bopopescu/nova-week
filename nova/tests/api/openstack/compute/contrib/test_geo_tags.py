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

import datetime
import mock
from webob import exc

from nova.api.openstack.compute.contrib import geo_tags
from nova import context
from nova import exception
from nova.objects import base
from nova.objects import geo_tags as geo_tags_obj
from nova import test


class FakeRequest(object):
    environ = {"nova.context": context.get_admin_context()}
    GET = {}


def fake_geotag_db(gt_id, server, state, latitude=None, longitude=None):
    return {'server_name': server,
            'valid_invalid': state,
            'ip_address': None,
            'mac_address': None,
            'parent_mac': None,
            'plt_latitude': latitude,
            'plt_longitude': longitude,
            'deleted': 0,
            'deleted_at': datetime.datetime(2014, 9, 3),
            'created_at': datetime.datetime(2014, 3, 3),
            'updated_at': datetime.datetime(2014, 3, 4),
            'rfid': None,
            'alerts': 0,
            'rfid_signature': None,
            'id': gt_id
            }


class GeotagsTest(test.NoDBTestCase):
    def setUp(self):
        super(GeotagsTest, self).setUp()
        self.controller = geo_tags.GeoTagsController()
        self.context = context.get_admin_context()
        self.db_list = (fake_geotag_db(1, 'server1', 'Valid', 100, 20),
                        fake_geotag_db(2, 'server2', 'Invalid', 300, 100))

        self.geo_tag_list = base.obj_make_list(context,
            geo_tags_obj.GeoTagList(), geo_tags_obj.GeoTag, self.db_list)

    @mock.patch('nova.db.geo_tag_get_all')
    def test_geo_tags_empty(self, db_mock):
        db_mock.return_value = {}
        req = FakeRequest()
        res_dict = self.controller.index(req)
        response = {'geo_tags': []}
        self.assertEqual(res_dict, response)
        db_mock.assert_called_once_with(req.environ['nova.context'], {})

    @mock.patch('nova.db.geo_tag_get_all')
    def test_geo_tags(self, db_mock):
        db_mock.return_value = self.db_list
        req = FakeRequest()
        res_dict = self.controller.index(req)
        self.assertTrue(len(res_dict['geo_tags']), 2)
        first_gt = res_dict['geo_tags'][0]
        self.assertTrue(first_gt.server_name, self.db_list[0]['server_name'])
        second_gt = res_dict['geo_tags'][1]
        self.assertEquals(second_gt.server_name,
                          self.db_list[1]['server_name'])
        db_mock.assert_called_once_with(req.environ['nova.context'], {})

    @mock.patch('nova.db.geo_tag_create')
    @mock.patch('nova.compute.api.HostAPI._assert_host_exists')
    def test_geo_tags_create(self, host_exists_mock, geo_tag_db_mock):
        host_exists_mock.return_value = 'server3'
        geo_tag_db_mock.return_value = fake_geotag_db(3, 'server3',
                                                     'Active', 33, 44)
        body = {'geo_tag': {'compute_name': 'server3',
                            'valid_invalid': 'Valid',
                            'plt_longitude': '33',
                            'plt_latitude': '44'}}

        req = FakeRequest()
        res_dict = self.controller.create(req, body)
        self.assertEquals(res_dict['geo_tag'].server_name, 'server3')
        expected = dict(body['geo_tag'])
        #(licostan): BIG NOTE, normalize server-name to compute_name
        #if we go por
        expected['server_name'] = expected.pop('compute_name')
        geo_tag_db_mock.assert_called_once_with(req.environ['nova.context'],
                                        expected)

    @mock.patch('nova.compute.api.HostAPI._assert_host_exists')
    def test_geo_tags_create_fails_invalid_host(self, host_exists_mock):
        host = 'xxxserver3'
        host_exists_mock.side_effect = exception.ComputeHostNotFound(host=host)
        body = {'geo_tag': {'compute_name': 'xxxserver3',
                            'valid_invalid': 'Valid',
                            'plt_longitude': '33',
                            'plt_latitude': '44'}}

        req = FakeRequest()
        self.assertRaises(exc.HTTPNotFound, self.controller.create, req, body)

    @mock.patch('nova.db.geo_tag_update')
    @mock.patch('nova.db.geo_tag_get_by_node_name')
    @mock.patch('nova.compute.api.HostAPI._assert_host_exists')
    def test_geo_tags_update(self, host_exists_mock, geo_tag_get_mock,
                             geo_tag_update_mock):
        host_exists_mock.return_value = 'server4'
        obj = fake_geotag_db(4, 'server4', 'Inactive', 11, 11)
        geo_tag_get_mock.return_value = obj
        geo_tag_update_mock.return_value = obj

        body = {'geo_tag': {'valid_invalid': 'Valid',
                            'plt_longitude': '33',
                            'plt_latitude': '44'}}

        req = FakeRequest()
        res_dict = self.controller.update(req, 'server4', body)
        self.assertEquals(res_dict['geo_tag'].server_name, 'server4')
        expected = dict(body['geo_tag'])
        #(licostan): BIG NOTE, normalize server-name to compute_name
        #if we go por
        geo_tag_update_mock.assert_called_once_with(
                                        req.environ['nova.context'],
                                        obj['id'], expected)

    @mock.patch('nova.db.geo_tag_destroy')
    @mock.patch('nova.db.geo_tag_get_by_id_or_node_name')
    def test_geo_tags_delete(self, geo_tag_get_mock, geo_tag_destroy_mock):
        #(licostan): Why the get? just destroy?... TODO
        obj = fake_geotag_db(4, 'server4', 'Inactive', 11, 11)
        geo_tag_get_mock.return_value = obj
        req = FakeRequest()
        res_dict = self.controller.delete(req, 'server4')
        geo_tag_destroy_mock.assert_called_once_with(
                                        req.environ['nova.context'], obj['id'])
