# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, json

@frappe.whitelist()
def get_items(start, page_length, price_list, item_group, search_value=""):
	serial_no = ""
	batch_no = ""
	item_code = search_value

	if search_value:
		# search serial no
		serial_no_data = frappe.db.get_value('Serial No', search_value, ['name', 'item_code'])
		if serial_no_data:
			serial_no, item_code = serial_no_data

		if not serial_no:
			batch_no_data = frappe.db.get_value('Batch', search_value, ['name', 'item'])
			if batch_no_data:
				batch_no, item_code = batch_no_data

	lft, rgt = frappe.db.get_value('Item Group', item_group, ['lft', 'rgt'])
	# locate function is used to sort by closest match from the beginning of the value
	res = frappe.db.sql("""select i.name as item_code, i.item_name, i.image as item_image,
		item_det.price_list_rate, item_det.currency
		from `tabItem` i LEFT JOIN
			(select item_code, price_list_rate, currency from
				`tabItem Price`	where price_list=%(price_list)s) item_det
		ON
			(item_det.item_code=i.name or item_det.item_code=i.variant_of)
		where
			i.disabled = 0 and i.has_variants = 0
			and i.item_group in (select name from `tabItem Group` where lft >= {lft} and rgt <= {rgt})
			and (i.item_code like %(item_code)s
			or i.item_name like %(item_code)s or i.barcode like %(item_code)s)
		limit {start}, {page_length}""".format(start=start, page_length=page_length, lft=lft, rgt=rgt),
		{
			'item_code': '%%%s%%'%(frappe.db.escape(item_code)),
			'price_list': price_list
		} , as_dict=1)

	res = {
		'items': res
	}

	if serial_no:
		res.update({
			'serial_no': serial_no
		})

	if batch_no:
		res.update({
			'batch_no': batch_no
		})

	return res

@frappe.whitelist()
def submit_invoice(doc):
	if isinstance(doc, basestring):
		args = json.loads(doc)

	doc = frappe.new_doc('Sales Invoice')
	doc.update(args)
	doc.run_method("set_missing_values")
	doc.run_method("calculate_taxes_and_totals")
	doc.submit()

	return doc
