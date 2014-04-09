# Copyright (c) 2012 OpenStack Foundation
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

from oslo.config import cfg

from nova import db
from nova.openstack.common import log as logging
from nova.scheduler import filters

CONF = cfg.CONF

LOG = logging.getLogger(__name__)


class GeoTagsFilter(filters.BaseHostFilter):
    """Filter on geo tags filters if available."""

    def host_passes(self, host_state, filter_properties):
        context = filter_properties['context']
        scheduler_hints = filter_properties.get('scheduler_hints') or {}
        #(licostan): in the future, HostManager shall include geo_tag filters
        #if it's going to be updated by each compute-node itself tru ipmi or
        #something like that..... ( host_state.geo_tag for instance),
        #instead of querying the db
        geo_tags = scheduler_hints.get('geo_tags', None)

        #filters = {'host': host_state.host, 'valid_invalid': 'Valid'}
        #(licostan): Should we use objects? don't know... 
        #anyways this call should not happen in production
        geo_tag = db.geo_tag_get_by_node_name(context, host_state.host)
        if not geo_tag:
            LOG.info('NO GEO TAG FOUND FOR %s' % host_state.host)
            return True

        if geo_tag['valid_invalid'].lower() == 'valid':
            #check geo_tags here if needed
            LOG.info('GEO TAG FOUND FOR %s' % host_state.host)
            return True

        LOG.info('GEO TAG INVALID FOR  %s' % host_state.host)
        #always true for now.
        return False
