# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the managed client hosts
#
# Copyright 2004-2018 Univention GmbH
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

from ldap.filter import filter_format

from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.handlers
import univention.admin.password
import univention.admin.allocators
import univention.admin.localization
import univention.admin.uldap
import univention.admin.nagios as nagios
import univention.admin.handlers.dns.forward_zone
import univention.admin.handlers.dns.reverse_zone
import univention.admin.handlers.groups.group
import univention.admin.handlers.networks.network
import time

translation = univention.admin.localization.translation('univention.admin.handlers.computers')
_ = translation.translate

module = 'computers/ubuntu'
operations = ['add', 'edit', 'remove', 'search', 'move']
docleanup = 1
childs = 0
short_description = _('Computer: Ubuntu')
long_description = ''
options = {
	'posix': univention.admin.option(
		short_description=_('Posix account'),
		default=1,
		objectClasses=('posixAccount', 'shadowAccount'),
	),
	'kerberos': univention.admin.option(
		short_description=_('Kerberos principal'),
		default=1,
		objectClasses=('krb5Principal', 'krb5KDCEntry'),
	),
	'samba': univention.admin.option(
		short_description=_('Samba account'),
		editable=True,
		default=1,
		objectClasses=('sambaSamAccount',),
	)
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Hostname'),
		long_description='',
		syntax=univention.admin.syntax.hostName,
		multivalue=False,
		include_in_default_search=True,
		options=[],
		required=True,
		may_change=True,
		identifies=True
	),
	'description': univention.admin.property(
		short_description=_('Description'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		include_in_default_search=True,
		required=False,
		may_change=True,
		identifies=False
	),
	'operatingSystem': univention.admin.property(
		short_description=_('Operating system'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		include_in_default_search=True,
		required=False,
		may_change=True,
		identifies=False
	),
	'operatingSystemVersion': univention.admin.property(
		short_description=_('Operating system version'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		required=False,
		may_change=True,
		identifies=False
	),
	'domain': univention.admin.property(
		short_description=_('Domain'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		include_in_default_search=True,
		required=False,
		may_change=True,
		identifies=False
	),
	'mac': univention.admin.property(
		short_description=_('MAC address'),
		long_description='',
		syntax=univention.admin.syntax.MAC_Address,
		multivalue=True,
		include_in_default_search=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'network': univention.admin.property(
		short_description=_('Network'),
		long_description='',
		syntax=univention.admin.syntax.network,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'ip': univention.admin.property(
		short_description=_('IP address'),
		long_description='',
		syntax=univention.admin.syntax.ipAddress,
		multivalue=True,
		include_in_default_search=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'dnsEntryZoneForward': univention.admin.property(
		short_description=_('Forward zone for DNS entry'),
		long_description='',
		syntax=univention.admin.syntax.dnsEntry,
		multivalue=True,
		options=[],
		required=False,
		may_change=True,
		dontsearch=True,
		identifies=False
	),
	'dnsEntryZoneReverse': univention.admin.property(
		short_description=_('Reverse zone for DNS entry'),
		long_description='',
		syntax=univention.admin.syntax.dnsEntryReverse,
		multivalue=True,
		options=[],
		required=False,
		may_change=True,
		dontsearch=True,
		identifies=False
	),
	'dnsEntryZoneAlias': univention.admin.property(
		short_description=_('Zone for DNS alias'),
		long_description='',
		syntax=univention.admin.syntax.dnsEntryAlias,
		multivalue=True,
		options=[],
		required=False,
		may_change=True,
		dontsearch=True,
		identifies=False
	),
	'dnsAlias': univention.admin.property(
		short_description=_('DNS alias'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'dhcpEntryZone': univention.admin.property(
		short_description=_('DHCP service'),
		long_description='',
		syntax=univention.admin.syntax.dhcpEntry,
		multivalue=True,
		options=[],
		required=False,
		may_change=True,
		dontsearch=True,
		identifies=False
	),
	'password': univention.admin.property(
		short_description=_('Password'),
		long_description='',
		syntax=univention.admin.syntax.passwd,
		multivalue=False,
		options=['kerberos', 'posix', 'samba'],
		required=False,
		may_change=True,
		identifies=False,
		dontsearch=True
	),
	'unixhome': univention.admin.property(
		short_description=_('Unix home directory'),
		long_description='',
		syntax=univention.admin.syntax.absolutePath,
		multivalue=False,
		options=['posix'],
		required=True,
		may_change=True,
		identifies=False,
		default=('/dev/null', [])
	),
	'shell': univention.admin.property(
		short_description=_('Login shell'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=['posix'],
		required=False,
		may_change=True,
		identifies=False,
		default=('/bin/bash', [])
	),
	'primaryGroup': univention.admin.property(
		short_description=_('Primary group'),
		long_description='',
		syntax=univention.admin.syntax.GroupDN,
		multivalue=False,
		options=['posix'],
		required=True,
		dontsearch=True,
		may_change=True,
		identifies=False
	),
	'inventoryNumber': univention.admin.property(
		short_description=_('Inventory number'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
		include_in_default_search=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'groups': univention.admin.property(
		short_description=_('Groups'),
		long_description='',
		syntax=univention.admin.syntax.GroupDN,
		multivalue=True,
		options=[],
		required=False,
		may_change=True,
		dontsearch=True,
		identifies=False
	),
	'sambaRID': univention.admin.property(
		short_description=_('Relative ID'),
		long_description='',
		syntax=univention.admin.syntax.integer,
		multivalue=False,
		required=False,
		may_change=True,
		dontsearch=True,
		identifies=False,
		options=['samba']
	),
}

layout = [
	Tab(_('General'), _('Basic settings'), layout=[
		Group(_('Computer account'), layout=[
			['name', 'description'],
			['operatingSystem', 'operatingSystemVersion'],
			'inventoryNumber',
		]),
		Group(_('Network settings '), layout=[
			'network',
			'mac',
			'ip',
		]),
		Group(_('DNS Forward and Reverse Lookup Zone'), layout=[
			'dnsEntryZoneForward',
			'dnsEntryZoneReverse',
		]),
		Group(_('DHCP'), layout=[
			'dhcpEntryZone'
		]),
	]),
	Tab(_('Account'), _('Account'), advanced=True, layout=[
		'password',
		'primaryGroup'
	]),
	Tab(_('Unix account'), _('Unix account settings'), advanced=True, layout=[
		['unixhome', 'shell']
	]),
	Tab(_('Groups'), _('Group memberships'), advanced=True, layout=[
		'groups',
	]),
	Tab(_('DNS alias'), _('Alias DNS entry'), advanced=True, layout=[
		'dnsEntryZoneAlias'
	]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('domain', 'associatedDomain', None, univention.admin.mapping.ListToString)
mapping.register('inventoryNumber', 'univentionInventoryNumber')
mapping.register('mac', 'macAddress')
mapping.register('network', 'univentionNetworkLink', None, univention.admin.mapping.ListToString)
mapping.register('unixhome', 'homeDirectory', None, univention.admin.mapping.ListToString)
mapping.register('shell', 'loginShell', None, univention.admin.mapping.ListToString)
mapping.register('operatingSystem', 'univentionOperatingSystem', None, univention.admin.mapping.ListToString)
mapping.register('operatingSystemVersion', 'univentionOperatingSystemVersion', None, univention.admin.mapping.ListToString)

# add Nagios extension
nagios.addPropertiesMappingOptionsAndLayout(property_descriptions, mapping, options, layout)


class object(univention.admin.handlers.simpleComputer, nagios.Support):
	module = module

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes=[]):
		univention.admin.handlers.simpleComputer.__init__(self, co, lo, position, dn, superordinate, attributes)
		nagios.Support.__init__(self)

	def open(self):
		global options
		univention.admin.handlers.simpleComputer.open(self)
		self.nagios_open()

		self.modifypassword = 0

		if self.exists():

			if 'posix' in self.options and not self.info.get('primaryGroup'):
				primaryGroupNumber = self.oldattr.get('gidNumber', [''])[0]
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'primary group number = %s' % (primaryGroupNumber))
				if primaryGroupNumber:
					primaryGroupResult = self.lo.searchDn(filter_format('(&(objectClass=posixGroup)(gidNumber=%s))', [primaryGroupNumber]))
					if primaryGroupResult:
						self['primaryGroup'] = primaryGroupResult[0]
						univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'Set primary group = %s' % (self['primaryGroup']))
					else:
						self['primaryGroup'] = None
						self.save()
						raise univention.admin.uexceptions.primaryGroup
				else:
					self['primaryGroup'] = None
					self.save()
					raise univention.admin.uexceptions.primaryGroup
			if 'samba' in self.options:
				sid = self.oldattr.get('sambaSID', [''])[0]
				pos = sid.rfind('-')
				self.info['sambaRID'] = sid[pos + 1:]

		if self.exists():
			userPassword = self.oldattr.get('userPassword', [''])[0]
			if userPassword:
				self.info['password'] = userPassword
				self.modifypassword = 0
			self.save()

		else:
			self.modifypassword = 0
			if 'posix' in self.options:
				res = univention.admin.config.getDefaultValue(self.lo, 'univentionDefaultClientGroup', position=self.position)
				if res:
					self['primaryGroup'] = res

	def _ldap_pre_create(self):
		super(object, self)._ldap_pre_create()
		if not self['password']:
			self['password'] = self.oldattr.get('password', [''])[0]
			self.modifypassword = 0

	def _ldap_addlist(self):
		if not set(self.options) & set(['posix', 'kerberos']):
			raise univention.admin.uexceptions.invalidOptions(_(' At least posix or kerberos is required.'))

		ocs = ['top', 'person', 'univentionHost', 'univentionUbuntuClient']
		al = []
		if 'kerberos' in self.options:
			domain = univention.admin.uldap.domain(self.lo, self.position)
			realm = domain.getKerberosRealm()

			if realm:
				al.append(('krb5MaxLife', '86400'))
				al.append(('krb5MaxRenew', '604800'))
				al.append(('krb5KDCFlags', '126'))
				krb_key_version = str(int(self.oldattr.get('krb5KeyVersionNumber', ['0'])[0]) + 1)
				al.append(('krb5KeyVersionNumber', self.oldattr.get('krb5KeyVersionNumber', []), krb_key_version))
			else:
				# can't do kerberos
				self._remove_option('kerberos')
		if 'posix' in self.options:
			self.uidNum = univention.admin.allocators.request(self.lo, self.position, 'uidNumber')
			self.alloc.append(('uidNumber', self.uidNum))
			gidNum = self.get_gid_for_primary_group()
			al.append(('uidNumber', [self.uidNum]))
			al.append(('gidNumber', [gidNum]))

		if self.modifypassword or self['password']:
			if 'kerberos' in self.options:
				krb_keys = univention.admin.password.krb5_asn1(self.krb5_principal(), self['password'])
				al.append(('krb5Key', self.oldattr.get('password', ['1']), krb_keys))
			if 'posix' in self.options:
				password_crypt = "{crypt}%s" % (univention.admin.password.crypt(self['password']))
				al.append(('userPassword', self.oldattr.get('userPassword', [''])[0], password_crypt))
			if 'samba' in self.options:
				password_nt, password_lm = univention.admin.password.ntlm(self['password'])
				al.append(('sambaNTPassword', self.oldattr.get('sambaNTPassword', [''])[0], password_nt))
				al.append(('sambaLMPassword', self.oldattr.get('sambaLMPassword', [''])[0], password_lm))
				sambaPwdLastSetValue = str(long(time.time()))
				al.append(('sambaPwdLastSet', self.oldattr.get('sambaPwdLastSet', [''])[0], sambaPwdLastSetValue))
			self.modifypassword = 0
		if 'samba' in self.options:
			acctFlags = univention.admin.samba.acctFlags(flags={'W': 1})
			self.machineSid = self.getMachineSid(self.lo, self.position, self.uidNum, self.get('sambaRID'))
			self.alloc.append(('sid', self.machineSid))
			al.append(('sambaSID', [self.machineSid]))
			al.append(('sambaAcctFlags', [acctFlags.decode()]))
			al.append(('displayName', self.info['name']))

		al.insert(0, ('objectClass', ocs))

		return al

	def _ldap_post_create(self):
		if 'posix' in self.options:
			if hasattr(self, 'uid') and self.uid:
				univention.admin.allocators.confirm(self.lo, self.position, 'uid', self.uid)
			univention.admin.handlers.simpleComputer.primary_group(self)
			univention.admin.handlers.simpleComputer.update_groups(self)
		univention.admin.handlers.simpleComputer._ldap_post_create(self)
		self.nagios_ldap_post_create()

	def _ldap_pre_remove(self):
		self.open()
		if 'posix' in self.options and self.oldattr.get('uidNumber'):
			self.uidNum = self.oldattr['uidNumber'][0]

	def _ldap_post_remove(self):
		if 'posix' in self.options:
			univention.admin.allocators.release(self.lo, self.position, 'uidNumber', self.uidNum)
		groupObjects = univention.admin.handlers.groups.group.lookup(self.co, self.lo, filter_s=filter_format('uniqueMember=%s', [self.dn]))
		if groupObjects:
			for i in range(0, len(groupObjects)):
				groupObjects[i].open()
				if self.dn in groupObjects[i]['users']:
					groupObjects[i]['users'].remove(self.dn)
					groupObjects[i].modify(ignore_license=1)

		self.nagios_ldap_post_remove()
		univention.admin.handlers.simpleComputer._ldap_post_remove(self)
		# Need to clean up oldinfo. If remove was invoked, because the
		# creation of the object has failed, the next try will result in
		# a 'object class violation' (Bug #19343)
		self.oldinfo = {}

	def krb5_principal(self):
		domain = univention.admin.uldap.domain(self.lo, self.position)
		realm = domain.getKerberosRealm()
		if self.info.has_key('domain') and self.info['domain']:
			kerberos_domain = self.info['domain']
		else:
			kerberos_domain = domain.getKerberosRealm()
		return 'host/' + self['name'] + '.' + kerberos_domain.lower() + '@' + realm

	def _ldap_post_modify(self):
		univention.admin.handlers.simpleComputer.primary_group(self)
		univention.admin.handlers.simpleComputer.update_groups(self)
		univention.admin.handlers.simpleComputer._ldap_post_modify(self)
		self.nagios_ldap_post_modify()

	def _ldap_pre_modify(self):
		if self.hasChanged('password'):
			if not self['password']:
				self['password'] = self.oldattr.get('password', [''])[0]
				self.modifypassword = 0
			elif not self.info['password']:
				self['password'] = self.oldattr.get('password', [''])[0]
				self.modifypassword = 0
			else:
				self.modifypassword = 1
		self.nagios_ldap_pre_modify()
		univention.admin.handlers.simpleComputer._ldap_pre_modify(self)

	def _ldap_modlist(self):
		ml = univention.admin.handlers.simpleComputer._ldap_modlist(self)

		self.nagios_ldap_modlist(ml)

		if self.hasChanged('name'):
			if 'posix' in self.options:
				if hasattr(self, 'uidNum'):
					univention.admin.allocators.confirm(self.lo, self.position, 'uidNumber', self.uidNum)
				requested_uid = "%s$" % self['name']
				try:
					self.uid = univention.admin.allocators.request(self.lo, self.position, 'uid', value=requested_uid)
				except Exception:
					self.cancel()
					raise univention.admin.uexceptions.uidAlreadyUsed(': %s' % requested_uid)
					return []

				self.alloc.append(('uid', self.uid))

				ml.append(('uid', self.oldattr.get('uid', [None])[0], self.uid))

			if 'samba' in self.options:
				ml.append(('displayName', self.oldattr.get('displayName', [None])[0], self['name']))

			if 'kerberos' in self.options:
				ml.append(('krb5PrincipalName', self.oldattr.get('krb5PrincipalName', []), [self.krb5_principal()]))

		if self.modifypassword and self['password']:
			if 'kerberos' in self.options:
				krb_keys = univention.admin.password.krb5_asn1(self.krb5_principal(), self['password'])
				krb_key_version = str(int(self.oldattr.get('krb5KeyVersionNumber', ['0'])[0]) + 1)
				ml.append(('krb5Key', self.oldattr.get('password', ['1']), krb_keys))
				ml.append(('krb5KeyVersionNumber', self.oldattr.get('krb5KeyVersionNumber', []), krb_key_version))
			if 'posix' in self.options:
				password_crypt = "{crypt}%s" % (univention.admin.password.crypt(self['password']))
				ml.append(('userPassword', self.oldattr.get('userPassword', [''])[0], password_crypt))
			if 'samba' in self.options:
				password_nt, password_lm = univention.admin.password.ntlm(self['password'])
				ml.append(('sambaNTPassword', self.oldattr.get('sambaNTPassword', [''])[0], password_nt))
				ml.append(('sambaLMPassword', self.oldattr.get('sambaLMPassword', [''])[0], password_lm))
				sambaPwdLastSetValue = str(long(time.time()))
				ml.append(('sambaPwdLastSet', self.oldattr.get('sambaPwdLastSet', [''])[0], sambaPwdLastSetValue))

		# add samba option
		if self.exists() and self.option_toggled('samba') and 'samba' in self.options:
			acctFlags = univention.admin.samba.acctFlags(flags={'W': 1})
			self.machineSid = self.getMachineSid(self.lo, self.position, self.oldattr['uidNumber'][0], self.get('sambaRID'))
			self.alloc.append(('sid', self.machineSid))
			ml.append(('sambaSID', '', [self.machineSid]))
			ml.append(('sambaAcctFlags', '', [acctFlags.decode()]))
			ml.append(('displayName', '', self.info['name']))
			sambaPwdLastSetValue = str(long(time.time()))
			ml.append(('sambaPwdLastSet', self.oldattr.get('sambaPwdLastSet', [''])[0], sambaPwdLastSetValue))
		if self.exists() and self.option_toggled('samba') and 'samba' not in self.options:
			for key in ['sambaSID', 'sambaAcctFlags', 'sambaNTPassword', 'sambaLMPassword', 'sambaPwdLastSet', 'displayName']:
				if self.oldattr.get(key, []):
					ml.insert(0, (key, self.oldattr.get(key, []), ''))

		if self.hasChanged('sambaRID') and not hasattr(self, 'machineSid'):
			self.machineSid = self.getMachineSid(self.lo, self.position, self.oldattr['uidNumber'][0], self.get('sambaRID'))
			ml.append(('sambaSID', self.oldattr.get('sambaSID', ['']), [self.machineSid]))

		return ml

	def cleanup(self):
		self.open()
		self.nagios_cleanup()
		univention.admin.handlers.simpleComputer.cleanup(self)

	def cancel(self):
		for i, j in self.alloc:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'cancel: release (%s): %s' % (i, j))
			univention.admin.allocators.release(self.lo, self.position, i, j)


def rewrite(filter, mapping):
	if filter.variable == 'ip':
		filter.variable = 'aRecord'
	else:
		univention.admin.mapping.mapRewrite(filter, mapping)


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0):

	res = []
	filter_s = univention.admin.filter.replace_fqdn_filter(filter_s)
	if str(filter_s).find('(dnsAlias=') != -1:
		filter_s = univention.admin.handlers.dns.alias.lookup_alias_filter(lo, filter_s)
		if filter_s:
			res += lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit)
	else:
		filter = univention.admin.filter.conjunction('&', [
			univention.admin.filter.expression('objectClass', 'univentionHost'),
			univention.admin.filter.expression('objectClass', 'univentionUbuntuClient'),
			univention.admin.filter.conjunction('|', [
				univention.admin.filter.expression('objectClass', 'posixAccount'),
				univention.admin.filter.conjunction('&', [
					univention.admin.filter.expression('objectClass', 'krb5KDCEntry'),
					univention.admin.filter.expression('objectClass', 'krb5Principal'),
				])
			])
		])

		if filter_s:
			filter_p = univention.admin.filter.parse(filter_s)
			univention.admin.filter.walk(filter_p, rewrite, arg=mapping)
			filter.expressions.append(filter_p)

		for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit):
			res.append(object(co, lo, None, dn, attributes=attrs))
	return res


def identify(dn, attr, canonical=0):
	return 'univentionHost' in attr.get('objectClass', []) and 'univentionUbuntuClient' in attr.get('objectClass', []) and ('posixAccount' in attr.get('objectClass', []) or ('krb5KDCEntry' in attr.get('objectClass', []) and 'krb5Principal' in attr.get('objectClass', [])))
