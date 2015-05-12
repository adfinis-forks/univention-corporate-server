# -*- coding: utf-8 -*-
#
# Univention Management Console
#  next generation of UMC modules
#
# Copyright 2011-2014 Univention GmbH
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

"""
.. _sec-module-definitions:

Module definitions
==================

The UMC server does not load the python modules to get the details about
the modules name, description and functionality. Therefore each UMC
module must provide an XML file containing this kind of information.

The following example defines a module with the id *udm* ::

 <?xml version="1.0" encoding="UTF-8"?>
 <umc version="2.0">
   <module id="udm" icon="udm/module" version="1.0">
     <name>Univention Directory Manager</name>
     <description>Manages all UDM modules</description>
     <flavor icon="udm-users" id="users/user">
       <name>Users</name>
       <description>Managing users</description>
     </flavor>
     <categories>
       <category name="domain"/>
     </categories>
     <command name="udm/query" function="query">
     </command>
     <command name="udm/containers" function="containers" />
   </module>
 </umc>

The *module* tag defines the basic details of a UMC module

id
	This identifier must be unique among the modules of an UMC server. Other
	files may extend the definition of a module by adding more flavors
	or categories.

icon
	The value of this attribute defines an identifier for the icon that
	should be used for the module. Details for installing icons can be
	found in the section :ref:`chapter-packaging`

The child elements *name* and *description* define the English human
readable name and description of the module. For other translations the
build tools will create translation files. Details can be found in the
section :ref:`chapter-packaging`.

This example defines a so called flavor. A flavor defines a new name,
description and icon for the same UMC module. This can be used to show
several"virtual" modules in the overview of the web frontend. Additionally the flavor is passed to the UMC server with each request i.e. the UMC modul has the possibility to act differently for a specific flavor.

As the next element *categories* is defined in the example. The child
elements *category* set the categories wthin the overview where the
module should be shown. Each module can be more than one category. The
attribute name is to identify the category internally. The UMC server
brings a set of pre-defined categories:

favorites
	This category is intended to be filled by the user herself.

system
	Tools manipulating the system itself (e.g. software installation)
	should go in here.

At the end of the definition file a list of commands is specified. The
UMC server only passes commands to a UMC module that are defined. A
command definition has two attributes:

name
	is the name of the command that is passed to the UMC module. Within
	the UMCP message it is the first argument after the UMCP COMMAND.

function
	defines the method to be invoked within the python module when the
	command is called.

keywords
	defined keywords for the module to ensure searchability

The translations are stored in extra po files that are generated by the
UMC build tools.
"""

import copy
import os
import sys
import re
import xml.parsers.expat
import xml.etree.ElementTree as ET

from .tools import JSON_Object, JSON_List
from .log import RESOURCES
from .config import ucr

KEYWORD_PATTERN = re.compile(r'\s*,\s*')


class Command(JSON_Object):

	'''Represents a UMCP command handled by a module'''
	SEPARATOR = '/'

	def __init__(self, name='', method=None):
		self.name = name
		if method:
			self.method = method
		else:
			self.method = self.name.replace(Command.SEPARATOR, '_')

	def fromJSON(self, json):
		for attr in ('name', 'method'):
			setattr(self, attr, json[attr])


class Flavor(JSON_Object):

	'''Defines a flavor of a module. This provides another name and icon
	in the overview and may influence the behaviour of the module.'''

	def __init__(self, id='', icon='', name='', description='', overwrites=None, deactivated=False, priority=-1, translationId=None, keywords=None, categories=None):
		self.id = id
		self.name = name
		self.description = description
		self.icon = icon
		self.overwrites = overwrites or []
		self.keywords = keywords or []
		self.deactivated = deactivated
		self.priority = priority
		self.translationId = translationId
		self.categories = categories or []


class Module(JSON_Object):

	'''Represents a command attribute'''

	def __init__(self, id='', name='', description='', icon='', categories=None, flavors=None, commands=None, priority=-1, keywords=None):
		self.id = id
		self.name = name
		self.description = description
		self.keywords = keywords or []
		self.icon = icon
		self.priority = priority
		self.flavors = JSON_List()
		if flavors is not None:
			self.append_flavors(flavors)

		if categories is None:
			self.categories = JSON_List()
		else:
			self.categories = categories
		if commands is None:
			self.commands = JSON_List()
		else:
			self.commands = commands

	def fromJSON(self, json):
		if isinstance(json, dict):
			for attr in ('id', 'name', 'description', 'icon', 'categories', 'keywords'):
				setattr(self, attr, json[attr])
			commands = json['commands']
		else:
			commands = json
		for cmd in commands:
			command = Command()
			command.fromJSON(cmd)
			self.commands.append(command)

	def append_flavors(self, flavors):
		for flavor in flavors:
			# remove duplicated flavors
			if flavor.id not in [iflavor.id for iflavor in self.flavors] or flavor.deactivated:
				self.flavors.append(flavor)
			else:
				RESOURCES.warn('Duplicated flavor for module %s: %s' % (self.id, flavor.id))

	def merge(self, other):
		''' merge another Module object into current one '''
		if not self.name:
			self.name = other.name

		if not self.icon:
			self.icon = other.icon

		if not self.description:
			self.description = other.description

		self.keywords = list(set(self.keywords + other.keywords))

		self.append_flavors(other.flavors)

		for category in other.categories:
			if not category in self.categories:
				self.categories.append(category)

		for command in other.commands:
			if not command in self.commands:
				self.commands.append(command)


class XML_Definition(ET.ElementTree):

	'''container for the interface description of a module'''

	def __init__(self, root=None, filename=None):
		ET.ElementTree.__init__(self, element=root, file=filename)

	@property
	def name(self):
		return self.findtext('module/name')

	@property
	def description(self):
		return self.findtext('module/description')

	@property
	def keywords(self):
		return KEYWORD_PATTERN.split(self.findtext('module/keywords', '')) + [self.name]

	@property
	def id(self):
		return self.find('module').get('id')

	@property
	def priority(self):
		try:
			return float(self.find('module').get('priority', -1))
		except ValueError:
			RESOURCES.warn('No valid number type for property "priority": %s' % self.find('module').get('priority'))
		return None

	@property
	def translationId(self):
		return self.find('module').get('translationId', '')

	@property
	def notifier(self):
		return self.find('module').get('notifier')

	@property
	def icon(self):
		return self.find('module').get('icon')

	@property
	def deactivated(self):
		return self.find('module').get('deactivated', 'no').lower() in ('yes', 'true', '1')

	@property
	def flavors(self):
		'''Retrieve list of flavor objects'''
		for elem in self.findall('module/flavor'):
			name = elem.findtext('name')
			priority = None
			try:
				priority = float(elem.get('priority', -1))
			except ValueError:
				RESOURCES.warn('No valid number type for property "priority": %s' % elem.get('priority'))
			yield Flavor(
				id=elem.get('id'),
				icon=elem.get('icon'),
				name=name,
				overwrites=elem.get('overwrites', '').split(','),
				deactivated=(elem.get('deactivated', 'no').lower() in ('yes', 'true', '1')),
				translationId=self.translationId,
				description=elem.findtext('description'),
				keywords=re.split(KEYWORD_PATTERN, elem.findtext('keywords', '')) + [name],
				priority=priority,
				categories=[cat.get('name') for cat in elem.findall('categories/category')]
			)

	@property
	def categories(self):
		return [elem.get('name') for elem in self.findall('module/categories/category')]

	def commands(self):
		'''Generator to iterate over the commands'''
		for command in self.findall('module/command'):
			yield command.get('name')

	def get_module(self):
		return Module(self.id, self.name, self.description, self.icon, self.categories, self.flavors, priority=self.priority, keywords=self.keywords)

	def get_flavor(self, name):
		'''Retrieves details of a flavor'''
		for flavor in self.flavors:
			if flavor.name == name:
				cmd = Flavor(name, flavor.get('function'))
				return cmd

		return None

	def get_command(self, name):
		'''Retrieves details of a command'''
		for command in self.findall('module/command'):
			if command.get('name') == name:
				cmd = Command(name, command.get('function'))
				return cmd
		return None

	def __nonzero__(self):
		return bool(self.find('module'))

_manager = None


class Manager(dict):

	'''Manager of all available modules'''

	DIRECTORY = os.path.join(sys.prefix, 'share/univention-management-console/modules')

	def __init__(self):
		dict.__init__(self)

	def modules(self):
		'''Returns list of module names'''
		return self.keys()

	def load(self):
		'''Loads the list of available modules. As the list is cleared
		before, the method can also be used for reloading'''
		RESOURCES.info('Loading modules ...')
		self.clear()
		for filename in os.listdir(Manager.DIRECTORY):
			if not filename.endswith('.xml'):
				continue
			try:
				mod = XML_Definition(filename=os.path.join(Manager.DIRECTORY, filename))
				if not mod:
					RESOURCES.info('Empty XML file: %s' % (filename,))
					continue
				if mod.deactivated:
					RESOURCES.info('Module is deactivated: %s' % filename)
					continue
				RESOURCES.info('Loaded module %s' % filename)
			except (xml.parsers.expat.ExpatError, ET.ParseError) as e:
				RESOURCES.warn('Failed to load module %s: %s' % (filename, str(e)))
				continue
			# save list of definitions in self
			self.setdefault(mod.id, []).append(mod)

	def permitted_commands(self, hostname, acls):
		'''Retrieves a list of all modules and commands available
		according to the ACLs (instance of LDAP_ACLs)

		{ id : Module, ... }
		'''
		RESOURCES.info('Retrieving list of permitted commands')
		modules = {}
		for module_id in self:
			# get first Module and merge all subsequent Module objects into it
			mod = None
			for module_xml in self[module_id]:
				nextmod = module_xml.get_module()
				if mod:
					mod.merge(nextmod)
				else:
					mod = nextmod

			if ucr.is_true('umc/module/%s/disabled' % (module_id)):
				RESOURCES.info('module %s is deactivated by UCR' % (module_id))
				continue

			if not mod.flavors:
				flavors = [Flavor(id=None)]
			else:
				flavors = copy.copy(mod.flavors)

			deactivated_flavors = set()
			for flavor in flavors:
				if ucr.is_true('umc/module/%s/%s/disabled' % (module_id, flavor.id)):
					RESOURCES.info('flavor %s (module=%s) is deactivated by UCR' % (flavor.id, module_id))
					# flavor is deactivated by UCR variable
					flavor.deactivated = True

				RESOURCES.info('mod=%s  flavor=%s  deactivated=%s' % (module_id, flavor.id, flavor.deactivated))
				if flavor.deactivated:
					deactivated_flavors.add(flavor.id)
					continue

				at_least_one_command = False
				# iterate over all commands in all XML descriptions
				for module_xml in self[module_id]:
					for command in module_xml.commands():
						if acls.is_command_allowed(command, hostname, flavor=flavor.id):
							if not module_id in modules:
								modules[module_id] = mod
							cmd = module_xml.get_command(command)
							if not cmd in modules[module_id].commands:
								modules[module_id].commands.append(cmd)
							at_least_one_command = True

				# if there is not one command allowed with this flavor
				# it should not be shown in the overview
				if not at_least_one_command and mod.flavors:
					mod.flavors.remove(flavor)

			mod.flavors = JSON_List(filter(lambda f: f.id not in deactivated_flavors, mod.flavors))

			overwrites = set()
			for flavor in mod.flavors:
				overwrites.update(flavor.overwrites)

			mod.flavors = JSON_List(filter(lambda f: f.id not in overwrites, mod.flavors))

		return modules

	def module_providing(self, modules, command):
		'''Searches a dictionary of modules (as returned by
		permitted_commands) for the given command. If found, the id of
		the module is returned, otherwise None'''
		RESOURCES.info('Searching for module providing command %s' % command)
		for module_id in modules:
			for cmd in modules[module_id].commands:
				if cmd.name == command:
					RESOURCES.info('Found module %s' % module_id)
					return module_id

		RESOURCES.info('No module provides %s' % command)
		return None

if __name__ == '__main__':
	mgr = Manager()
