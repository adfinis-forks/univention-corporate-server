#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Python Heimdal
#  setup description for the python distutils
#
# Copyright 2003-2018 Univention GmbH
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

from distutils.core import setup, Extension
import platform as plat

if '64bit' in plat.architecture():
	libdir = '/usr/lib/x86_64-linux-gnu'
else:
	libdir = '/usr/lib/i386-linux-gnu'

setup(
	name='python-heimdal',
	version='0.1',
	description='Heimdal Python bindings',
	author='Univention GmbH',
	author_email='packages@univention.de',
	url='http://www.univention.de/',

	ext_modules=[
		Extension(
			'heimdal',
			['module.c', 'error.c', 'context.c', 'principal.c',
				'creds.c', 'ticket.c', 'keytab.c', 'ccache.c',
				'salt.c', 'enctype.c', 'keyblock.c', 'asn1.c'],
			libraries=['krb5', 'kadm5clnt', 'hdb', 'asn1', 'com_err', 'roken'],
			library_dirs=[libdir + '/heimdal'],
			include_dirs=['/usr/include/heimdal']
		)
	],
)
