odoo.define('nomin_comparison.sheet', function (require) {
"use strict";

var core = require('web.core');
var data = require('web.data');
var form_common = require('web.form_common');
var formats = require('web.formats');
var Model = require('web.DataModel');
var time = require('web.time');
var utils = require('web.utils');

var QWeb = core.qweb;
var _t = core._t;
var supps = [];
var supp_ids = {};
var WeeklyTimesheet = form_common.FormWidget.extend(form_common.ReinitializeWidgetMixin, {
    events: {
        "click .oe_partner a": "go_to_partner",
        "click .oe_supplier a": "go_to_purchase_order",
        "click .oe_product a": "go_to_product",

    },
    ignore_fields: function() {
        return ['line_id'];
    },
    init: function() {
        
        this._super.apply(this, arguments);
        this.set({
            sheets: [],
            date_from: false,
            date_to: false,
        });
        this.field_manager.on("field_changed:order_ids", this, this.query_sheets);
        // console.log('%c init', "background: blue; color: black; padding-left:10px;",this.field_manager.on("field_changed:order_ids", this, this.query_sheets));
        this.on("change:sheets", this, this.update_sheets);
        this.res_o2m_drop = new utils.DropMisordered();
        this.render_drop = new utils.DropMisordered();
        this.description_line = _t("/");
    },

    go_to_partner: function(event) {
        var id = JSON.parse($(event.target).data("id"));
        this.do_action({
            type: 'ir.actions.act_window',
            res_model: "res.partner",
            res_id: id,
            views: [[false, 'form']],
        });
    },

    go_to_product: function(event) {
        var id = JSON.parse($(event.target).data("id"));
        this.do_action({
            type: 'ir.actions.act_window',
            res_model: "product.product",
            res_id: id,
            views: [[false, 'form']],
        });
    },

    go_to_purchase_order: function(event) {
        var id = JSON.parse($(event.target).data("id"));
        this.do_action({
            type: 'ir.actions.act_window',
            res_model: "purchase.order",
            res_id: id,
            views: [[false, 'form']],
        });
    },
    query_sheets: function() {
        if (this.updating) {
            return;
        }
        var commands = this.field_manager.get_field_value("order_ids");
        var self = this;

        this.res_o2m_drop.add(new Model(this.view.model).call("resolve_2many_commands", 
                ["order_ids", commands, [], new data.CompoundContext()]))
            .done(function(result) {
                self.querying = true;
                self.set({sheets: result});
                self.querying = false;
            });
            // console.log('%c query_sheets', "background: blue; color: black; padding-left:10px;");   
    },
    update_sheets: function() {
        if(this.querying) {
            return;
        }
        this.updating = true;
        console.log('%c update_sheets', "background: blue; color: black; padding-left:10px;");
        var commands = [form_common.commands.delete_all()];
        _.each(this.get("sheets"), function (_data) {
            var data = _.clone(_data);
            if(data.id) {
                commands.push(form_common.commands.link_to(data.id));
                commands.push(form_common.commands.update(data.id, data));
            } else {
                commands.push(form_common.commands.create(data));
            }
        });

        var self = this;
        this.field_manager.set_values({'order_ids': commands}).done(function() {
            self.updating = false;
        });
    },
    initialize_field: function() {
        // console.log('%c initialize_field', "background: blue; color: black; padding-left:10px;");
        // form_common.ReinitializeWidgetMixin.initialize_field.call(this);
        form_common.ReinitializeWidgetMixin.initialize_field.call(this);
        this.on("change:sheets", this, this.initialize_content);
        // this.on("change:date_to", this, this.initialize_content);
        // this.on("change:date_from", this, this.initialize_content);
        // this.on("change:user_id", this, this.initialize_content);
    },
    has_product:function(id){
            // console.log("has_product",this.product_objs);
            var index;
            for(index in this.product_objs){
                obj = this.product_objs[index];

                if(obj['id'] == id){
                    return true;
                }
            }
            return false;
        },
    initialize_content: function() {
        if(this.setting) {
            return;
        }
        var self = this;
        // console.log('%c initialize_content', "background: blue; color: black; padding-left:10px;");
        self.suppliers = [];
            self.order_ids = [];
            self.products = [];
            self.product_objs = [];
            self.product_names = {};
            self.supplier_names = {};
            self.supplier_id = {};
            self.order_id = {};
            self.orders = this.field_manager.get_field_value("order_ids");
            _.each(self.orders, function(order) {
                self.order_ids.push(order[1]);
            });
            var loaded = self.fetch('purchase.order',
                    ['id', 'name', 'partner_id', 'amount_total',  'order_line',
                        'untax_amount','tax_amount','delivery_condition','delivery_cost','installation_condition','installation_cost',
                        'vat_amount','total_amount','delivery_term','warranty_period',
                        'return_condition','loan_term','barter_percentage',
                        'state','currency_rate','market_price_total','rfq_return_condition','rfq_delivery_term',
                        'rfq_warranty_period','rfq_barter_percentage','rfq_loan_term','currency_id','vat_condition'],
                    [['id', 'in', self.order_ids]])
                    .then(function(order_objs) {
                        self.suppliers = [];
                       // console.log("asfdasdfasfsad")
                        self.order_names = [];
                        self.untax_amount = {};
                        self.delivery_condition = {};
                        self.delivery_cost = {};
                        self.installation_condition = {};
                        self.installation_cost = {};
                        self.vat_condition = {};
                        self.vat_amount = {};
                        self.total_amount = {};
                        self.delivery_term = {};
                        self.warranty_period = {};
                        self.return_condition = {};
                        self.loan_term = {};
                        self.barter_percentage = {};
                        self.market_price_total = {};
                        self.planned_loan_term = '';
                        self.planned_delivery_term = '';
                        self.planned_return_condition = '';
                        self.planned_warranty_period = '';

                        self.quotation_price = {};
                        self.product_qty = {};
                        self.product_price = {};
                        self.product_id = {};
                        self.products = [];
                        self.product_objs = [];
                        self.product_names = {};
                        self.product_description = {};
                        self.supplier_names = {};
                        self.supplier_id = {};
                        self.order_id = {};
                        self.currency_rate = {};
                        self.currency_id = {};
                                    
                        self.states = {};
                        self.attachments = {};

                        var order_lines = {};
                        console.log("order_objs",order_objs)
                        _.each(order_objs, function(order_obj) {
                            self.suppliers.push(order_obj.name);
                            console.log('order_obj.name',order_obj.name)
                            // self.attachments[order_obj.name] = [];

                            // var attch = self.fetch('ir.attachment', ['id', 'datas_fname'], [['res_model', '=', 'purchase.order'],['res_id','=',order_obj.id]]).then(function(attachs) {
                            //     console.log('attachsssss: ', order_objs);
                            //     _.each(attachs, function(attach) {
                            //         console.log('attach.id: ', attach.id);
                            //         var found = 0;
                            //         for (i in self.attachments[order_obj.name]){
                            //             console.log('i: ', i);
                            //             console.log('self.attachments[order_obj.name][i][id]: ', self.attachments[order_obj.name][i]['id']);
                            //             console.log('attach.id: ', attach.id);
                            //             if (self.attachments[order_obj.name][i]['id'] == attach.id){
                            //                 found = 1;
                            //                 console.log('found');
                            //             }
                            //         }
                            //         if (found == 0){
                            //             self.attachments[order_obj.name].push({'id':attach.id, 'filename' : attach.datas_fname});
                            //         }
                            //     });
                            // });
                            var rate1 = 1;
                            var currency = self.fetch('res.currency', ['id', 'name', 'rate'], [['id', '=',order_obj.currency_id[0] ]]).then(function(currencies) {
                                    _.each(currencies, function(currency) {

                                        rate1 = currency.rate;
                                        // console.log('order_obj.currency',currency.rate)
                                        
                                    //    self.currency_rate[order_obj.name]= currency.rate
                                    //     if (order_obj.amount_total == false) {
                                    //     self.quotation_price[order_obj.name] = 0;
                                    //     } else {
                                    //             if( self.currency_rate[order_obj.name] != false){
                                    //                 self.quotation_price[order_obj.name] = order_obj.amount_total *self.currency_rate[order_obj.name];
                                    //             }
                                    //     }
                                    //    // self.attachments[order_obj.name].push({'id':attach.id, 'filename' : attach.datas_fname});
                                    //    console.log(' currency', currency)
                                    //    console.log(' self.quotation_price[order_obj.name]', order_obj.name)
                                    
                                });
                            });

                            // quotation өгч бгаа үнэнүүд хоорондоо солигдоод бсан тул дээрх давталт дотороос amount_total-г гаргаж бичив

                            self.currency_rate[order_obj.name]= rate1;
                            self.untax_amount[order_obj.name] = order_obj.untax_amount;
                            self.delivery_cost[order_obj.name] = order_obj.delivery_cost;
                            self.installation_cost[order_obj.name] = order_obj.installation_cost;
                            self.vat_amount[order_obj.name] = order_obj.tax_amount;
                            self.total_amount[order_obj.name] = order_obj.total_amount;
                            self.market_price_total = order_obj.market_price_total;
                            self.planned_loan_term = order_obj.loan_term || '';
                            self.planned_delivery_term = order_obj.delivery_term || '';
                            self.planned_return_condition = order_obj.return_condition || '';
                            self.planned_warranty_period = order_obj.warranty_period || '';
                            self.planned_barter_percentage = order_obj.barter_percentage || '';

                            console.log('order.obj market_price_total',order_obj.market_price_total);
                            console.log('self.obj market_price_total',self.market_price_total);
                            self.return_condition[order_obj.name] = order_obj.rfq_return_condition || ''
                            self.delivery_term[order_obj.name] = order_obj.rfq_delivery_term || ''
                            self.warranty_period[order_obj.name] = order_obj.rfq_warranty_period || ''
                            self.loan_term[order_obj.name] = order_obj.rfq_loan_term || ''
                            self.barter_percentage[order_obj.name] = order_obj.rfq_barter_percentage || ''
                           // self.attachments[order_obj.name].push({'id':attach.id, 'filename' : attach.datas_fname});

                        //    console.log(' self.quotation_price[order_obj.name]', order_obj.name)

                            supp_ids[order_obj.name] = order_obj.id;


                            self.supplier_names[order_obj.name] = order_obj.partner_id[1];
                            self.supplier_id[order_obj.name] = order_obj.partner_id[0];
                            self.order_id[order_obj.name] = order_obj['id'];

                            order_lines[order_obj.name] = order_obj.order_line;

                            self.currency_id[order_obj.name] = order_obj.currency_id[0];
                            
                            // self.currency_rate[order_obj.name] = order_obj.currency_rate;

                            var state_translation = {'cancel':'Шалгараагүй',
                                                'draft':'Ноорог PO',
                                                'comparison_created':'Харьцуулалт үүссэн',
                                                'approved':'Зөвшөөрсөн',
                                                'confirmed':'Баталсан',
                                                'purchase':'Шалгарсан',
                                                'done':'Дууссан',
                                                'sent_rfq':'Үнийн санал авах',
                                                'back':'Үнийн санал ирсэн'
                            }

                            var required_translation = {'required':'Шаардлагатай',
                                                'not_required':'Шаардлагагүй',
                            }

                            self.states[order_obj.name] = state_translation[order_obj.state];
                            self.vat_condition = required_translation[order_obj.vat_condition];
                            self.delivery_condition = required_translation[order_obj.delivery_condition];
                            self.installation_condition = required_translation[order_obj.installation_condition];

                            // self.states[order_obj.name] = order_obj.state;
                        });
                        supps = self.suppliers;
                        return order_lines;
                    }).then(function(order_lines) {
                        _.each(order_lines, function(line) {
                            _.each(self.suppliers, function(supplier) {
                                self.product_price[supplier] = {};
                                self.product_qty[supplier] = {};
                                self.product_description[supplier] = {};
                                self.planned_product_qty = {};
                                self.planned_price = {};
                                self.planned_description = {};
                                self.planned_total = {};
                                var products = self.fetch('purchase.order.line', ['id', 'product_id', 'price_unit', 'product_qty','market_price','additional_desc','name'],
                                 [['id', 'in', order_lines[supplier]]]).then(function(lines) {
                                    _.each(lines, function(line) {
                                        if (self.products.indexOf(line.product_id[1]) < 0) {
                                            self.products.push(line.product_id[1]);
                                            self.product_id[line.product_id[1]]=line.product_id[0];
                                        }
                                        // if (!self.has_product(line.product_id[0])) {
                                        //     self.product_objs.push({'id':line.product_id[0],'name':line.product_id[1]});
                                        // }
                                        // console.log('self.currency_rate[supplier]',self.currency_rate[supplier])
                                        // console.log(' self.currency_rate[order_obj.name]= currency.ratey', self.currency_rate[supplier])
                                        self.product_price[supplier][line.product_id[1]] = line.price_unit * self.currency_rate[supplier];
                                        self.product_qty[supplier][line.product_id[1]] = line.product_qty;
                                        self.product_description[supplier][line.product_id[1]] = line.additional_desc || line.name;
                                        self.planned_product_qty[line.product_id[1]] = line.product_qty;
                                        self.planned_price[line.product_id[1]] = line.market_price;
                                        self.planned_description[line.product_id[1]] = line.name;
                                        self.planned_total[line.product_id[1]] = line.market_price * line.product_qty
                                    });
                                    self.display_data();
                                    return products;
                                }).then(function(products) {
                                    return self.products;
                                });
                            });
                        });
                    });    
    },
    
    get_formatted_amount:function(amount){
            var amount1=Math.round(amount);
            return amount1.toString().replace(/(\d)(?=(\d{3})+(?!\d))/g, "$1,");
        
        },
    fetch: function(model, fields, domain, ctx) {
            return new Model(model).query(fields).filter(domain).context(ctx).all();
        },

    get_planned_price:function(product) {
        self = this;
        return self.planned_price[product]
    },

    get_planned_product_qty:function(product) {
        self = this;
        return self.planned_product_qty[product]
    },

    get_planned_total:function(product) {
        self = this;
        return self.planned_total[product]
    },

    get_planned_description:function(product) {
        self = this;
        return self.planned_description[product]
    },

    get_description: function(supplier, product) {
        self = this;
        var field;
        for (field in self.product_description[supplier]) {
            if (field == product) {
                return self.product_description[supplier][field];
            }
        }
        return 0;
    },

    get_price:function(supplier, product){
            self = this;
            var field;
            for(field in self.product_price[supplier]){
                if(field == product){
                    // console.log("PRODUCT field", self.product_price[supplier][field]);
                    return this.get_formatted_amount( self.product_price[supplier][field]);
                }
            }
            return 0;
        },
    get_qty:function(supplier, product){
            self = this;
            var field;
            for(field in self.product_qty[supplier]){
                if(field == product){
                    return this.get_formatted_amount(self.product_qty[supplier][product]);
                }
            }
            return 0;
        },
    get_total:function(supplier, product){
            self = this;
            var field;
            var total;
            var product_qty;
            var product_price;
            for(field in self.product_qty[supplier]){
                if(field == product){
                    product_qty = self.product_qty[supplier][product];
                }
            }
            for(field in self.product_price[supplier]){
                if(field == product){
                    // console.log("PRODUCT field", self.product_price[supplier][field]);
                    product_price = self.product_price[supplier][field];
                }
            }
            total = product_qty*product_price;
            return this.get_formatted_amount(total);
            
        },
    destroy_content: function() {
        // console.log('%c destroy_content', "background: blue; color: black; padding-left:10px;");
        if (this.dfm) {
            this.dfm.destroy();
            this.dfm = undefined;
        }
    },
    
    display_data: function() {
        var self = this;
        // console.log('%c display_data', "background: blue; color: black; padding-left:10px;");
        self.$el.html(QWeb.render("nomin_comparison.Comparison", {widget: self}));
       
    },

    sync: function() {
        // console.log('%c sync', "background: blue; color: black; padding-left:10px;");
        this.setting = true;
        this.setting = false;
    },
   
});

core.form_custom_registry.add('comparison_widget', WeeklyTimesheet);

});

