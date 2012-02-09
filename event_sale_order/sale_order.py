# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from osv import fields, osv
class product(osv.osv):
    _inherit='product.product'
    _columns={
    'event_ok':fields.boolean('Event'),
    'event_type':fields.many2one('event.type','Type of Event'),
    }
product()

class sale_order_line(osv.osv):
    _inherit='sale.order.line'
    _columns={
    'event':fields.many2one('event.event','Event'),
    'event_type':fields.char('event_type',128),
    'event_ok':fields.boolean('event_ok'),
    }

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
    uom=False, qty_uos=0, uos=False, name='', partner_id=False,
    lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        res = {}
        if product:
            product_res = self.pool.get('product.product').browse(cr, uid, product)
            if product_res.event_type:
                res={'value' : {
                                'event_type':product_res.event_type.name,
                                'event_ok':product_res.event_ok
                                }
                    }
            return  res

        return super(sale_order_line,self).product_id_change(cr,uid,ids,res,context)

    def button_confirm(self,cr,uid,ids,context=None):
        registration = self.browse(cr,uid,ids,context=None)
        for registration in registration:    
            if registration.event.id:
                self.pool.get('event.registration').create(cr,uid,{
                'name':registration.order_id.partner_invoice_id.name,
                'partner_id':registration.order_id.partner_id.id,
                'contact_id':registration.order_id.partner_invoice_id.id,
                'email':registration.order_id.partner_id.email,
                'phone':registration.order_id.partner_id.phone,
                'street':registration.order_id.partner_invoice_id.street,
                'city':registration.order_id.partner_invoice_id.city,
                'origin':registration.order_id.name,
                'nb_register':1,
                'event_id':registration.event.id,
                })
                message = ("The sales order '%s' create a registration.") % (registration.order_id.name,)
                self.log(cr, uid, registration.event.id, message)
        return super(sale_order_line, self).button_confirm(cr, uid, ids, context)



