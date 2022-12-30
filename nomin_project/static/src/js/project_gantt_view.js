odoo.define('nomin_project.project_forecast_widget', function (require) {
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
    
    var project_forecast = form_common.FormWidget.extend(form_common.ReinitializeWidgetMixin, {
        events: {
            // "click .oe_payroll_employee a": "go_to_employee",
            "click .gtasklist a": "open_task",
        },
        open_task: function(event) {
            var id = JSON.parse($(event.target).data("embedded-Ganttchild_177622"));
            console.log("DDDDD"+id);   
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: "project.task",
                res_id: 15,
                views: [['form', 'Tree']],
            });
        },    
        init: function() {
            
            this._super.apply(this, arguments);        
            this.set({
                project_id: false,                
                task_ids: false,
            });
            
            this.task_ids = [];       
            this.field_manager.on("field_changed:project_id", this, function() {
                this.set({"project_id": this.field_manager.get_field_value("project_id")});
            });
            this.field_manager.on("field_changed:task_ids", this, this.query_sheets);
            this.on("change:task_ids", this, this.update_sheets);
            
            
            this.res_o2m_drop = new utils.DropMisordered();
            this.render_drop = new utils.DropMisordered();   
            
        },
        query_sheets: function() {
            if (this.updating) {
                return;
            }
            var commands = this.field_manager.get_field_value("task_ids");
            var self = this;
    
            this.res_o2m_drop.add(new Model(this.view.model).call("resolve_2many_commands", 
                    ["task_ids", commands, [], new data.CompoundContext()]))
                .done(function(result) {
                    console.log(result)
                    self.querying = true;
                    self.set({task_ids: result});
                    self.querying = false;
                });
                // console.log('%c query_sheets', "background: blue; color: black; padding-left:10px;");   
        },

        update_sheets: function() {
            if(this.querying) {
                return;
            }
            this.updating = true;
            // console.log('%c update_sheets', "background: blue; color: black; padding-left:10px;");
            var commands = [form_common.commands.delete_all()];
            _.each(this.get("task_ids"), function (_data) {
                var data = _.clone(_data);
                console.log('TASK',data)
                if(data.id) {
                    commands.push(form_common.commands.link_to(data.id));
                    commands.push(form_common.commands.update(data.id, data));
                } else {
                    commands.push(form_common.commands.create(data));
                }
            });
    
            var self = this;
            this.field_manager.set_values({'task_ids': commands}).done(function() {
                self.updating = false;
            });
        },

        initialize_field: function() {

            form_common.ReinitializeWidgetMixin.initialize_field.call(this);
            var self = this;            
            self.on("change:project_id", self, self.initialize_content);
            self.on("change:task_ids", self, self.initialize_content);
        },
        initialize_content: function() {
            if(this.setting) {
                return;
            }                
            if (!this.get("project_id")) {                                
                return ;
               }                   
            this.destroy_content();
            this.display_data();
        },

        display_data: function() {
            var self = this;        
            self.$el.html(QWeb.render("nomin_project.project_forecast_widget", {widget: self}));            
            try {
                self.display_gantt();
                
            }catch(err) {
                console.log(err.message);
            }
            
        },
        destroy_content: function() {
            if (this.dfm) {
                this.dfm.destroy();
                this.dfm = undefined;
            }
        },
        display_gantt: function(){
            
            var g = new JSGantt.GanttChart(document.getElementById('embedded-Gantt'), 'week');                    
            if (g.getDivId() != null) {
            g.setCaptionType('Complete');  // Set to Show Caption (None,Caption,Resource,Duration,Complete)
            g.setQuarterColWidth(36);
            g.setDateTaskDisplayFormat('day dd month yyyy'); // Shown in tool tip box
            g.setDayMajorDateDisplayFormat('mon yyyy - Week ww') // Set format to display dates in the "Major" header of the "Day" view
            g.setWeekMinorDateDisplayFormat('dd mon') // Set format to display dates in the "Minor" header of the "Week" view
            g.setShowTaskInfoLink(1); // Show link in tool tip (0/1)
            g.setShowEndWeekDate(0); // Show/Hide the date for the last day of the week in header for daily view (1/0)
            g.setUseSingleCell(10000); // Set the threshold at which we will only use one cell per table row (0 disables).  Helps with rendering performance for large charts.
            g.setFormatArr('Day', 'Week', 'Month', 'Quarter'); // Even with setUseSingleCell using Hour format on such a large chart can cause issues in some browsers
            // Parameters (pID, pName,                  pStart,       pEnd,        pStyle,         pLink (unused)  pMile, pRes,       pComp, pGroup, pParent, pOpen, pDepend, pCaption, pNotes, pGantt)
            var vAdditionalHeaders = {
                category: {
                  title: 'Category'
                },
                sector: {
                  title: 'Sector'
                }
              }
            // g.setAdditionalHeaders(vAdditionalHeaders)
            var self = this;
            self.line_ids = []
            self.lines = self.field_manager.get_field_value("task_ids");            
            var tasks = self.get("task_ids");
            _.each(tasks, function(line) {                
                self.line_ids.push(line.task_id);
            });
            
            self.results= {};
            
            var loaded= new Model("project.forecast.task").call("get_line_values", [self.line_ids]).then(function(result) {                   
                
                self.results= result;
                _.each(result, function(res) {                      
                    g.AddTaskItem(new JSGantt.TaskItem(Number(res.pID), res.pName, res.pStart, res.pEnd, res.pClass, res.pLink,res.pMile, res.pRes, res.pComp, 0, Number(res.pParent), res.pOpen, '', '', res.pNotes, g));                    
                })
                g.Draw();
                })
            // console.log('results',self.results)
            // console.log('loaded',loaded);
            
            // g.AddTaskItem(new JSGantt.TaskItem(1, 'Define Chart API', '2017-02-20', '2017-05-20', 'ggroupblack', '', 0, 'Brian', 0, 1, 0, 1, '', '', 'Some Notes text', g));                  
            
            // g.AddTaskItem(new JSGantt.TaskItem(11, 'Chart Object', '2017-02-20', '2017-05-20', 'gtaskblue', '', 1, 'Shlomy', 100, 0, 1, 1, '', '', '', g));
            // g.AddTaskItem(new JSGantt.TaskItem(12, 'Task Objects', '', '', 'ggroupblack', '', 0, 'Shlomy', 40, 1, 1, 1, '', '', '', g));
            // g.AddTaskItem(new JSGantt.TaskItem(121, 'Constructor Proc #1234 of February 2017', '2017-02-21', '2017-03-09', 'gtaskblue', '', 0, 'Brian T.', 100, 0, 12, 1, '', '', '', g));
            // g.AddTaskItem(new JSGantt.TaskItem(122, 'Task Variables', '2017-03-06', '2017-03-11', 'gtaskred', '', 0, 'Brian', 60, 0, 12, 1, 121, '', '', g));
            // g.AddTaskItem(new JSGantt.TaskItem(123, 'Task by Minute/Hour', '2017-03-09', '2017-03-14 12:00', 'gtaskyellow', '', 0, 'Ilan', 60, 0, 12, 1, '', '', '', g));
            // g.AddTaskItem(new JSGantt.TaskItem(124, 'Task Functions', '2017-03-09', '2017-03-29', 'gtaskred', '', 0, 'Anyone', 60, 0, 12, 1, '123SS', 'This is a caption', null, g));
            // g.AddTaskItem(new JSGantt.TaskItem(2, 'Create HTML Shell', '2017-03-24', '2017-03-24', 'gtaskyellow', '', 0, 'Brian', 20, 0, 0, 1, 122, '', '', g));
            // g.AddTaskItem(new JSGantt.TaskItem(3, 'Code Javascript', '', '', 'ggroupblack', '', 0, 'Brian', 0, 1, 0, 1, '', '', '', g));
            // g.AddTaskItem(new JSGantt.TaskItem(31, 'Define Variables', '2017-02-25', '2017-03-17', 'gtaskpurple', '', 0, 'Brian', 30, 0, 3, 1, '', 'Caption 1', '', g));
            // g.AddTaskItem(new JSGantt.TaskItem(32, 'Calculate Chart Size', '2017-03-15', '2017-03-24', 'gtaskgreen', '', 0, 'Shlomy', 40, 0, 3, 1, '', '', '', g));
            // g.AddTaskItem(new JSGantt.TaskItem(33, 'Draw Task Items', '', '', 'ggroupblack', '', 0, 'Someone', 40, 2, 3, 1, '', '', '', g));
            // g.AddTaskItem(new JSGantt.TaskItem(332, 'Task Label Table', '2017-03-06', '2017-03-09', 'gtaskblue', '', 0, 'Brian', 60, 0, 33, 1, '', '', '', g));
            // g.AddTaskItem(new JSGantt.TaskItem(333, 'Task Scrolling Grid', '2017-03-11', '2017-03-20', 'gtaskblue', '', 0, 'Brian', 0, 0, 33, 1, '332', '', '', g));
            // g.AddTaskItem(new JSGantt.TaskItem(34, 'Draw Task Bars', '', '', 'ggroupblack', '', 0, 'Anybody', 60, 1, 3, 0, '', '', '', g));
            // g.AddTaskItem(new JSGantt.TaskItem(341, 'Loop each Task', '2017-03-26', '2017-04-11', 'gtaskred', '', 0, 'Brian', 60, 0, 34, 1, '', '', '', g));
            // g.AddTaskItem(new JSGantt.TaskItem(342, 'Calculate Start/Stop', '2017-04-12', '2017-05-18', 'gtaskpink', '', 0, 'Brian', 60, 0, 34, 1, '', '', '', g));
            // g.AddTaskItem(new JSGantt.TaskItem(343, 'Draw Task Div', '2017-05-13', '2017-05-17', 'gtaskred', '', 0, 'Brian', 60, 0, 34, 1, '', '', '', g));
            // g.AddTaskItem(new JSGantt.TaskItem(344, 'Draw Completion Div', '2017-05-17', '2017-06-04', 'gtaskred', '', 0, 'Brian', 60, 0, 34, 1, "342,343", '', '', g));
            // g.AddTaskItem(new JSGantt.TaskItem(35, 'Make Updates', '2017-07-17', '2017-09-04', 'gtaskpurple', '', 0, 'Brian', 30, 0, 3, 1, '333', '', '', g));

            // g.Draw();
            }
        },
        fetch: function(model, fields, domain, ctx) {
            return new Model(model).query(fields).filter(domain).context(ctx).all();
        },

    });
    
    
    core.form_custom_registry.add('project_gantt_widget', project_forecast);    
    });
    
    