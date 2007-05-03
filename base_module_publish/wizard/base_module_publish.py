##############################################################################
#
# Copyright (c) 2005-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import time
import wizard
import osv
import pooler
import urllib

intro_form = '''<?xml version="1.0"?>
<form string="Module publication">
	<separator string="Publication information" colspan="4"/>
	<field name="text" colspan="4" nolabel="1"/>
</form>'''

intro_fields = {
	'text': {'string':'Introduction', 'type':'text', 'readonly':True, 'default': lambda *args: """
This system will automatically publish the selected module to the
Tiny ERP official website. You can use it to quickly publish a new
module or update an existing one (new version).

Make sure you read the publication manual and modules guidelines
before continuing:
  http://tinyerp.com

Thank you for contributing !
"""},
}

def _get_selection(*Args):
	a = urllib.urlopen('http://www.tinyerp.com/mtree_interface.php')
	contents = a.read()
	content = filter(None, contents.split('\n'))
	return map(lambda x:x.split('='), content)


check_form = '''<?xml version="1.0"?>
<form string="Module publication">
	<separator string="Verify your module information" colspan="4"/>
	<notebook>
	<page string="General">
		<field name="name"/>
		<field name="version"/>
		<field name="author"/>
		<field name="website" widget="url"/>
		<field name="shortdesc"/>
		<field name="operation"/>
		<field name="category"/>
		<field name="licence"/>
		<field name="url_download"/>
		<label colspan="2" string="(Keep empty for an auto upload of the module)"/>
		<field name="docurl"/> <label colspan="2" string="(empty to keep existing value)"/>
		<field name="demourl"/> <label colspan="2" string="(empty to keep existing value)"/>
		<field name="image"/> <label colspan="2" string="(support only .png files)"/>
	</page><page string="Description">
		<field name="description" colspan="4" nolabel="1"/>
	</page>
	</notebook>
</form>'''

check_fields = {
	'name': {'string':'Name', 'type':'char', 'size':64, 'readonly':True},
	'shortdesc': {'string':'Small description', 'type':'char', 'size':200, 'readonly':True},
	'author': {'string':'Author', 'type':'char', 'size':128, 'readonly':True},
	'website': {'string':'Website', 'type':'char', 'size':200, 'readonly':True},
	'url': {'string':'Download URL', 'type':'char', 'size':200, 'readonly':True},
	'image': {'string':'Image file', 'type':'image'},
	'description': {'string':'Description', 'type':'text', 'readonly':True},
	'version': {'string':'Version', 'type':'char', 'readonly':True},
	'demourl': {'string':'Demo URL', 'type':'char', 'size':100},
	'docurl': {'string':'Documentation URL', 'type':'char', 'size':100},
	'category': {'string':'Category', 'type':'selection', 'size':64, 'required':True,
		'selection': _get_selection
	},
	'licence': {
		'string':'Licence', 'type':'selection', 'size':64, 'required':True,
		'selection': [('GPL', 'GPL'), ('Other proprietary','Other proprietary')],
		'default': lambda *args: 'GPL'
	},
	'operation': {
		'string':'Operation', 
		'type':'selection', 
		'readonly':True, 
		'selection':[('0','Creation'),('1','Modification')],
	},
	'url_download': {'string':'Download URL', 'type':'char', 'size':128},
}


upload_info_form = '''<?xml version="1.0"?>
<form string="Module publication">
	<separator string="User information" colspan="4"/>
	<label align="0.0" string="Please provide here your login on the Tiny ERP website." colspan="4"/>
	<label align="0.0" string="If you don't have an access, you can create one http://tinyerp.com." colspan="4"/>
	<field name="login"/>
	<field name="password"/>
	<newline/>
	<field name="email"/>
</form>'''

def _get_edit(self, cr, uid, datas, *args):
	pool = pooler.get_pool(cr.dbname)
	name = pool.get('ir.module.module').read(cr, uid, [datas['id']], ['name'])[0]['name']
	a = urllib.urlopen('http://www.tinyerp.com/mtree_interface.php?module=%s' % (name,))
	content = a.read()
	try:
		email = self.pool.get('res.users').browse(cr, uid, uid).address.email or ''
	except:
		email =''
	return {'operation': content[0], 'email':email}


upload_info_fields = {
	'login': {'string':'Login', 'type':'char', 'size':32, 'required':True},
	'email': {'string':'Email', 'type':'char', 'size':100, 'required':True},
	'password': {'string':'Password', 'type':'char', 'size':32, 'required':True, 'invisible':True},
}

end_form = '''<?xml version="1.0"?>
<form string="Module publication">
	<notebook>
	<page string="Information">
		<field name="text_end" colspan="4" nolabel="1"/>
	</page><page string="Result">
		<field name="result" colspan="4" nolabel="1"/>
	</page>
	</notebook>
</form>'''

end_fields = {
	'text_end': {'string':'Summary', 'type':'text', 'readonly':True, 'default': lambda *args: """
Thank you for contributing !

Your module has been successfully uploaded to the official website.
You must wait a few hours/days so that the Tiny ERP core team review
your module for approval on the website.
"""},
	'result': {'string':'Result page', 'type':'text', 'readonly':True}
}

import httplib, mimetypes

def post_multipart(host, selector, fields, files):
	def encode_multipart_formdata(fields, files):
		BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
		CRLF = '\r\n'
		L = []
		for (key, value) in fields:
			L.append('--' + BOUNDARY)
			L.append('Content-Disposition: form-data; name="%s"' % key)
			L.append('')
			L.append(value)
		for (key,value) in files:
			L.append('--' + BOUNDARY)
			L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, key+'.png'))
			L.append('Content-Type: application/octet-stream')
			L.append('')
			L.append(value)
		L.append('--' + BOUNDARY + '--')
		L.append('')
		body = CRLF.join(L)
		content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
		return content_type, body
	content_type, body = encode_multipart_formdata(fields, files)
	import httplib

	headers = {"Content-type": content_type, "Accept": "*/*"}
	conn = httplib.HTTPConnection(host)
	conn.request("POST", selector, body, headers = headers)
	response = conn.getresponse()
	val = response.status
	res = response.read()
	print res
	print host, selector, val
	conn.close()
	return res


def _upload(self, cr, uid, datas, context):
	download = datas['form']['url_download'] or ''
	if not download:
		# Create a .ZIP file and send them online
		# Set the download url to this .ZIP file
		download = '/'
	lpool = pooler.get_pool(cr.dbname)
	mod = pool.get('ir.module.module').browse(cr, uid, datas['id'])
	updata = {
		'link_name': mod.shortdesc or '',
		'new_cat_id': datas['form']['category'],
		'link_desc': (mod.description or '').replace('\n','<br/>\n'),
		'website': mod.website or '',
		'price': '0.0',
		'email': datas['form']['email'] or '',
		'cust_1': download,
		'cust_2': datas['form']['demourl'] or '',   # Put here the download url
		'cust_3': mod.url or '/',
		'cust_4': datas['form']['docurl'] or '',
		'cust_5': datas['form']['licence'] or '',
		'cust_6': mod.latest_version or '',
		'cust_7': mod.name,
		'option': 'com_mtree',
		'task': 'savelisting',
		'Itemid': '99999999',
		'cat_id': '0',
		'adminForm': '',
		'auto_login': datas['form']['login'],
		'auto_password': datas['form']['password']
	}
	files = []
	if datas['form']['image']:
		files.append(('link_image', datas['form']['image']))
	result = post_multipart('www.tinyerp.com', '/index.php', updata.items(), files)
	return {'result': result}

def module_check(self, cr, uid, data, context):
	pool = pooler.get_pool(cr.dbname)
	module = pool.get('ir.module.module').browse(cr, uid, data['id'], context)
	return {
		'name': module.name, 
		'shortdesc': module.shortdesc,
		'author': module.author,
		'website': module.website,
		'url': module.url,
		'description': module.description,
		'version': module.latest_version
	}

class base_module_publish(wizard.interface):
	states = {
		'init': {
			'actions': [], 
			'result': {
				'type':'form', 
				'arch':intro_form,
				'fields':intro_fields, 
				'state':[
					('end','Cancel'),
					('step1','Continue')
				]
			}
		},
		'step1': {
			'actions': [module_check,_get_edit],
			'result': {
				'type':'form', 
				'arch':check_form,
				'fields':check_fields, 
				'state':[
					('end','Cancel'),
					('init', 'Previous'),
					('step2','Continue')
				]
			}
		},
		'step2': {
			'actions': [],
			'result': {
				'type':'form', 
				'arch':upload_info_form,
				'fields':upload_info_fields, 
				'state':[
					('end','Cancel'),
					('step1', 'Previous'),
					('publish','Publish Now !')
				]
			}
		},
		'publish': {
			'actions': [_upload], # Action to develop: upload method
			'result': {
				'type':'form', 
				'arch':end_form,
				'fields':end_fields, 
				'state':[
					('end','Close')
				]
			}
		}
	}
base_module_publish('base_module_publish.module_publish')

