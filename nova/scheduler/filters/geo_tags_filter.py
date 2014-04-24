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

from nova.objects import geo_tags as geo_tags_obj
from nova.openstack.common import jsonutils
from nova.openstack.common import log as logging
from nova.scheduler import filters

CONF = cfg.CONF

LOG = logging.getLogger(__name__)


class GeoTagsFilter(filters.BaseHostFilter):
    """Filter on geo tags filters if available."""

    def _is_valid_rack_loc(self, host_rack, wanted_rack):
        wanted = wanted_rack.split('-')
        host = host_rack.split('-')
        if not wanted[-1]:
            wanted.pop()
        rack_aff = zip(wanted, host)
        for x, v in rack_aff:
            #may be empty due to to split
            if x != v:
                return False
        return True

    def host_passes(self, host_state, filter_properties):
        context = filter_properties['context']
        scheduler_hints = filter_properties.get('scheduler_hints') or {}
        #(licostan): in the future, HostManager shall include geo_tag filters
        #if it's going to be updated by each compute-node itself tru ipmi or
        #something like that..... ( host_state.geo_tag for instance),
        #instead of querying the db
        try:
            geo_tags_hint = jsonutils.loads(scheduler_hints.get('geo_tags',
                                                                '{}'))
        except Exception as e:
            LOG.error('Cannot parse json gtags')
            return False
        #(licostan): Should we use objects? don't know...
        #anyways this call should not happen in production
        geo_tag = geo_tags_obj.GeoTag.get_by_node_name(context,
                                                       host_state.host)
        if not geo_tag:
            LOG.info('NO GEO TAG FOUND FOR %s' % host_state.host)
            return True

        if geo_tag['valid_invalid'].lower() != 'valid':
            #check geo_tags here if needed
            LOG.info('GEO TAG Invalid  FOR %s' % host_state.host)
            return False

        wanted_rack = geo_tags_hint.get('rack_location', None)
        host_loc = geo_tag.get('loc_or_error_msg')

        if wanted_rack and not self._is_valid_rack_loc(host_loc, wanted_rack):
            LOG.info('Invalid rack location wanted: %(want)s '
                     ' host_loc: %(host_loc)s' % {'want': wanted_rack,
                                                 'host_loc': host_loc})
            return False

        LOG.info('GEO TAG VALID FOR  %s' % host_state.host)
        return True
