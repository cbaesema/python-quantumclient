# Copyright 2012 OpenStack LLC.
# All Rights Reserved
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
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import argparse
import logging

from quantumclient.quantum import v2_0 as quantumv20


class ListSecurityGroup(quantumv20.ListCommand):
    """List security groups that belong to a given tenant."""

    resource = 'security_group'
    log = logging.getLogger(__name__ + '.ListSecurityGroup')
    _formatters = {}
    list_columns = ['id', 'name', 'description']


class ShowSecurityGroup(quantumv20.ShowCommand):
    """Show information of a given security group."""

    resource = 'security_group'
    log = logging.getLogger(__name__ + '.ShowSecurityGroup')
    allow_names = True


class CreateSecurityGroup(quantumv20.CreateCommand):
    """Create a security group."""

    resource = 'security_group'
    log = logging.getLogger(__name__ + '.CreateSecurityGroup')

    def add_known_arguments(self, parser):
        parser.add_argument(
            'name', metavar='NAME',
            help='Name of security group')
        parser.add_argument(
            '--description',
            help='description of security group')

    def args2body(self, parsed_args):
        body = {'security_group': {
            'name': parsed_args.name}}
        if parsed_args.description:
            body['security_group'].update(
                {'description': parsed_args.description})
        if parsed_args.tenant_id:
            body['security_group'].update({'tenant_id': parsed_args.tenant_id})
        return body


class DeleteSecurityGroup(quantumv20.DeleteCommand):
    """Delete a given security group."""

    log = logging.getLogger(__name__ + '.DeleteSecurityGroup')
    resource = 'security_group'
    allow_names = True


class ListSecurityGroupRule(quantumv20.ListCommand):
    """List security group rules that belong to a given tenant."""

    resource = 'security_group_rule'
    log = logging.getLogger(__name__ + '.ListSecurityGroupRule')
    _formatters = {}
    list_columns = ['id', 'security_group_id', 'direction', 'protocol',
                    'source_ip_prefix', 'source_group_id']
    replace_rules = {'security_group_id': 'security_group',
                     'source_group_id': 'source_group'}

    def get_parser(self, prog_name):
        parser = super(ListSecurityGroupRule, self).get_parser(prog_name)
        parser.add_argument(
            '--no-nameconv', action='store_true',
            help='Do not convert security group ID to its name')
        return parser

    @staticmethod
    def replace_columns(cols, rules, reverse=False):
        if reverse:
            rules = dict((rules[k], k) for k in rules.keys())
        return [rules.get(col, col) for col in cols]

    def retrieve_list(self, parsed_args):
        parsed_args.fields = self.replace_columns(parsed_args.fields,
                                                  self.replace_rules,
                                                  reverse=True)
        return super(ListSecurityGroupRule, self).retrieve_list(parsed_args)

    def extend_list(self, data, parsed_args):
        if parsed_args.no_nameconv:
            return
        quantum_client = self.get_client()
        search_opts = {'fields': ['id', 'name']}
        secgroups = quantum_client.list_security_groups(**search_opts)
        secgroups = secgroups.get('security_groups', [])
        sg_dict = dict([(sg['id'], sg['name'])
                        for sg in secgroups if sg['name']])
        for rule in data:
            for key in self.replace_rules:
                rule[key] = sg_dict.get(rule[key], rule[key])

    def setup_columns(self, info, parsed_args):
        parsed_args.columns = self.replace_columns(parsed_args.columns,
                                                   self.replace_rules,
                                                   reverse=True)
        # NOTE(amotoki): 2nd element of the tuple returned by setup_columns()
        # is a generator, so if you need to create a look using the generator
        # object, you need to recreate a generator to show a list expectedly.
        info = super(ListSecurityGroupRule, self).setup_columns(info,
                                                                parsed_args)
        cols = info[0]
        if not parsed_args.no_nameconv:
            cols = self.replace_columns(info[0], self.replace_rules)
            parsed_args.columns = cols
        return (cols, info[1])


class ShowSecurityGroupRule(quantumv20.ShowCommand):
    """Show information of a given security group rule."""

    resource = 'security_group_rule'
    log = logging.getLogger(__name__ + '.ShowSecurityGroupRule')
    allow_names = False


class CreateSecurityGroupRule(quantumv20.CreateCommand):
    """Create a security group rule."""

    resource = 'security_group_rule'
    log = logging.getLogger(__name__ + '.CreateSecurityGroupRule')

    def add_known_arguments(self, parser):
        parser.add_argument(
            'security_group_id', metavar='SECURITY_GROUP',
            help='Security group name or id to add rule.')
        parser.add_argument(
            '--direction',
            default='ingress', choices=['ingress', 'egress'],
            help='direction of traffic: ingress/egress')
        parser.add_argument(
            '--ethertype',
            default='IPv4',
            help='IPv4/IPv6')
        parser.add_argument(
            '--protocol',
            help='protocol of packet')
        parser.add_argument(
            '--port-range-min',
            help='starting port range')
        parser.add_argument(
            '--port_range_min',
            help=argparse.SUPPRESS)
        parser.add_argument(
            '--port-range-max',
            help='ending port range')
        parser.add_argument(
            '--port_range_max',
            help=argparse.SUPPRESS)
        parser.add_argument(
            '--source-ip-prefix',
            help='cidr to match on')
        parser.add_argument(
            '--source_ip_prefix',
            help=argparse.SUPPRESS)
        parser.add_argument(
            '--source-group-id', metavar='SOURCE_GROUP',
            help='source security group name or id to apply rule')
        parser.add_argument(
            '--source_group_id',
            help=argparse.SUPPRESS)

    def args2body(self, parsed_args):
        _security_group_id = quantumv20.find_resourceid_by_name_or_id(
            self.get_client(), 'security_group', parsed_args.security_group_id)
        body = {'security_group_rule': {
            'security_group_id': _security_group_id,
            'direction': parsed_args.direction,
            'ethertype': parsed_args.ethertype}}
        if parsed_args.protocol:
            body['security_group_rule'].update(
                {'protocol': parsed_args.protocol})
        if parsed_args.port_range_min:
            body['security_group_rule'].update(
                {'port_range_min': parsed_args.port_range_min})
        if parsed_args.port_range_max:
            body['security_group_rule'].update(
                {'port_range_max': parsed_args.port_range_max})
        if parsed_args.source_ip_prefix:
            body['security_group_rule'].update(
                {'source_ip_prefix': parsed_args.source_ip_prefix})
        if parsed_args.source_group_id:
            _source_group_id = quantumv20.find_resourceid_by_name_or_id(
                self.get_client(), 'security_group',
                parsed_args.source_group_id)
            body['security_group_rule'].update(
                {'source_group_id': _source_group_id})
        if parsed_args.tenant_id:
            body['security_group_rule'].update(
                {'tenant_id': parsed_args.tenant_id})
        return body


class DeleteSecurityGroupRule(quantumv20.DeleteCommand):
    """Delete a given security group rule."""

    log = logging.getLogger(__name__ + '.DeleteSecurityGroupRule')
    resource = 'security_group_rule'
    allow_names = False
