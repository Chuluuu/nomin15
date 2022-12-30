# -*- coding: utf-8 -*-
from openerp import api, fields, models, _
import xlwt
from xlwt import *

ezxf = xlwt.easyxf
styles = {'nomin_title_normal_xf':ezxf('font: height 240, name Times New Roman, bold on; align: wrap on, vert centre, horiz centre;'),
          'nomin_sub_title_right_xf':ezxf('font: height 240, name Times New Roman, bold off; align: wrap on, vert centre, horiz right;'),
          'nomin_sub_title_left_xf':ezxf('font: height 240, name Times New Roman, bold off; align: wrap on, vert centre, horiz left;'),
          
          'nomin_table_header_normal_xf':ezxf('font: height 240, name Times New Roman, bold on; align: wrap on, vert centre, horiz centre; borders: top thin, left thin, bottom thin, right thin;'),
          'nomin_table_header_left_xf':ezxf('font: height 240, name Times New Roman, bold on; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin;'),
          
          'nomin_table_td_center_xf':ezxf('font: height 240, name Times New Roman, bold off; align: wrap on, vert centre, horiz centre; borders: top thin, left thin, bottom thin, right thin;'),
          'nomin_table_td_left_xf':ezxf('font: height 240, name Times New Roman, bold off; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin;'),
          'nomin_table_td_right_xf':ezxf('font: height 240, name Times New Roman, bold off; align: wrap on, vert centre, horiz right; borders: top thin, left thin, bottom thin, right thin;'),
          'nomin_table_td_float_left_xf':ezxf('font: height 240, name Times New Roman, bold off; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin;',num_format_str='#,##0.00'),
          'nomin_table_td_float_left_xf_bold':ezxf('font: height 240, name Times New Roman, bold on; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin;',num_format_str='#,##0.00'),
          'nomin_table_td_float_right_xf_bold':ezxf('font: height 240, name Times New Roman, bold on; align: wrap on, vert centre, horiz right; borders: top thin, left thin, bottom thin, right thin;',num_format_str='#,##0.00'),
          'nomin_footer_left_xf':ezxf('font: height 240, name Times New Roman, bold off; align: wrap on, vert centre, horiz left;'),
          'nomin_footer_right_xf':ezxf('font: height 240, name Times New Roman, bold off; align: wrap on, vert centre, horiz right;'),
          'nomin_footer_center_bold_xf':ezxf('font: height 240, name Times New Roman, bold on; align: wrap on, vert centre, horiz centre;'),
          'nomin_footer_center_xf':ezxf('font: height 240, name Times New Roman, bold off; align: wrap on, vert centre, horiz centre;'),
          }
                                        
                                        # 
    
        