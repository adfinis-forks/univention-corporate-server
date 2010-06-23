#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Client Basesystem
#  helper script for creation the configuration of thin client
#
# Copyright 2001-2010 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

import univention.uldap, univention.dns
import univention_baseconfig

dns_mapping = {
	('_ldap',				'txt', 'ldap/base'),
	('_ldap._tcp',				'srv', 'ldap/server/name'),
	('_kerberos',				'txt', 'kerberos/realm'),
	('_kerberos._udp',			'srv', 'kerberos/kdc'),
	('_windows-domain',			'txt', 'windows/domain'),
	('_windows-terminal-server._tcp',	'srv', 'windows/terminal-server'),
	('_univention-application-server._tcp',	'srv', 'client/desktopserver'),
	('_univention-file-server._tcp',	'srv', 'client/fileserver'),
}

attr_mapping = {
	'univentionSoundEnabled':	'sound/enabled',
	'univentionSoundModule':	'sound/module',

	'univentionBootImage':		'client/boot/image',
	'univentionBootMethod':		'client/boot/method',
	'univentionBootServer':		'client/boot/server',

	'univentionXModule':		'x/module',
	'univentionXResolution':	'x/resolution',
	'univentionXColorDepth':	'x/color-depth',
	'univentionXVRefresh':		'x/v-refresh',
	'univentionXHSync':		'x/h-sync',
	'univentionXMouseProtocol':	'x/mouse/protocol',
	'univentionXMouseDevice':	'x/mouse/device',
	'univentionXKeyboardLayout':	'x/keyboard/layout',
	'univentionXKeyboardVariant':	'x/keyboard/variant',
}

baseConfig=univention_baseconfig.baseConfig()

# query dns
for query, type, key in dns_mapping:
	result=univention.dns.lookup(query, type)
	if not result:
		continue
	if type == 'srv':
		baseConfig[dns_mapping[key]]=result[2]
	elif type == 'txt':
		baseConfig[dns_mapping[key]]=result

# search ldap
lo=univention.uldap.access(host=baseConfig['ldap/server/name'], base=baseConfig['ldap/base'])
attrs=lo.search_s(filter='(&(objectClass=univentionThinClient)(cn=%s))'%hostname, required=1, unique=1, policies=1)[0][1]
for key, value in attrs.items():
	if attr_mapping.has_key(key):
		baseConfig[attr_mapping[key]]=value[0]

baseConfig.save()
