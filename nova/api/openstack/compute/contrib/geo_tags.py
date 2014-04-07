
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

"""The GeoTag API extension."""
from webob import exc

from nova.api.openstack import extensions
from nova.compute import api as compute_api
from nova import exception
from nova.openstack.common.gettextutils import _
from nova.openstack.common import log as logging

LOG = logging.getLogger(__name__)
#(licostan): change to right policy and add it to policy file
authorize = extensions.extension_authorizer('compute', 'services')


def _get_context(req):
    return req.environ['nova.context']


class GeoTagsController(object):
    """The GeoTag API controller for the OpenStack API."""
    def __init__(self):
        self.api = compute_api.HostAPI()
        super(GeoTagsController, self).__init__()

    def index(self, req):
        """Returns all geo tags."""
        context = _get_context(req)
        authorize(context)
        filters = None
        if 'host' in req.GET:
            filters = {'host': req.GET['host']}
        gt = self.api.geo_tags_get_all(context, filters)
        return {'geo_tags': [g for g in gt.objects]}

    def create(self, req, body):
        """Creates a geotag
        """
        context = _get_context(req)
        authorize(context)

        if len(body) != 1:
            raise exc.HTTPBadRequest()

        try:
            geo_tag = body['geo_tag']
            compute_name = geo_tag["compute_name"]
        except KeyError:
            raise exc.HTTPBadRequest()

        longitude = geo_tag.get('plt_longitude')
        latitude = geo_tag.get('plt_latitude')
        state = geo_tag.get('valid_invalid')

        try:
            gt = self.api.geo_tags_create(context, compute_name, state,
                                          longitude=longitude,
                                          latitude=latitude)
        except exception.GeoTagExists as e:
            LOG.info(e)
            raise exc.HTTPConflict()
        except exception.ComputeHostNotFound as e:
            msg = _('Host %(host)s do not exists') % {'host': compute_name}
            LOG.info(msg)
            raise exc.HTTPNotFound(explanation=e.format_message())

        return {'geo_tag': gt}

    def show(self, req, id):
        """Shows the details of an aggregate, hosts and metadata included."""
        context = _get_context(req)
        authorize(context)
        try:
            geo_tag = self.api.geo_tag_get_by_id_or_node_name(context, id)
        except exception.NotFound:
            LOG.info(_("Cannot show geo_tag: %s"), id)
            raise exc.HTTPNotFound()
        return {'geo_tag': geo_tag}

    def update(self, req, id, body):
        """Update geotag by server_name right now.
           id  == server_name
        """
        context = _get_context(req)
        authorize(context)
        valid_keys = ['plt_longitude', 'plt_latitude', 'valid_invalid']

        if len(body) != 1:
            raise exc.HTTPBadRequest()
        try:
            update_values = body["geo_tag"]
        except KeyError:
            raise exc.HTTPBadRequest()

        if len(update_values) < 1:
            raise exc.HTTPBadRequest()
        #(licostan): iteraate update_values and check valid_keys if not
        #throw error
        longitude = update_values.get('plt_longitude')
        latitude = update_values.get('plt_latitude')
        state = update_values.get('valid_invalid')
         #(licostan): remove compute_name and pass **update_values
         #to remove args
        try:
            geo_tag = self.api.geo_tags_update(context, id,
                                           valid_invalid=state,
                                           longitude=longitude,
                                           latitude=latitude)
        except exception.NotFound as e:
            LOG.info(_('Cannot update geotag'))
            raise exc.HTTPNotFound(explanation=e.format_message())

        return {'geo_tag': geo_tag}

    def show(self, req, id):
        """Shows the details of Geo Tags."""
        context = _get_context(req)
        authorize(context)
        try:
            geo_tag = self.api.geo_tags_get_by_id_or_name(context, id)
        except exception.NotFound:
            LOG.info(_("Cannot show GeoTag: %s"), id)
            raise exc.HTTPNotFound()
        return {'geo_tag': geo_tag}

    def delete(self, req, id):
        """Removes a GeoTag by id/servername."""
        context = _get_context(req)
        authorize(context)
        try:
            self.api.geo_tags_delete(context, id)
        except exception.NotFound:
            LOG.info(_('Cannot delete GeoTag: %s'), id)
            raise exc.HTTPNotFound()


class Geo_tags(extensions.ExtensionDescriptor):
    """Admin-only geo tags administration."""

    name = "Geo Tags"
    alias = "os-geo-tags"
    namespace = "http://docs.openstack.org/compute/ext/os-geo-tags/api/v1.1"
    updated = "2012-01-12T00:00:00+00:00"

    def get_resources(self):
        resources = []
        res = extensions.ResourceExtension('os-geo-tags',
                GeoTagsController())
        resources.append(res)
        return resources
