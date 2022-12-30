# -*- coding: utf-8 -*-
##############################################################################
#
#   USI-ERP, Enterprise Management Solution    
#   Copyright (C) 2007-2010 USI Co.,ltd (<http://www.usi.mn>). All Rights Reserved
#    
#    ЮүЭсАй-ЕРП, Байгууллагын цогц мэдээлэлийн систем
#    зохиогчийн эрх авсан 2007-2010 ЮүЭсАй ХХК (<http://www.usi.mn>). 
#    
#    Зохиогчийн зөвшөөрөлгүйгээр хуулбарлах ашиглахыг хориглоно.
#    
#    Харилцах хаяг : 
#    Э-майл : info@usi.mn
#    Утас : 976 + 70151145
#    Факс : 976 + 70151146
#    Баянзүрх дүүрэг, 4-р хороо, Энхүүд төв,
#    Улаанбаатар, Монгол Улс
#    
##############################################################################
from standard_report.standard_report import StandardReport
from standard_report.simple_row_table import *
from standard_report.report_helper import *
from standard_report.translation import _
from reportlab.platypus import *
from reportlab.lib.colors import red, black, navy, white, green, aqua
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from datetime import datetime
from operator import itemgetter
from openerp.tools.translate import _
from openerp.report import report_sxw
import StringIO, cStringIO, base64
from openerp import api
from openerp import SUPERUSER_ID

import time

class abstract_report_builder2(StandardReport):
    ''' Тайлангийн ерөнхий загвар
    '''
    def get_template_title(self, cr, context):
        """ return the title of the report """
        return u"Abstract Report"
    
    def get_story(self):
        ''' Тайлангийн өгөгдлүүдийг боловсруулж, PDF -г зурна.
            A4 цаасний стандарт хэмжээ 210x297 үүний тайлангийн бие нь
            Хэвтээ хэлбэрээр 280x200 байхаар тогтоолоо.
        '''
        story = []
        cr = self.cr
        uid = self.uid
        context = self.context
        
        res = self.pool.get(self.datas['model']).get_export_data(cr, uid, self.datas['ids'], '', context=context)
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        datas = res['datas']
        title = datas.get('title', 'Generic Report')
        headers = datas.get('headers', [])
        header_span = datas.get('header_span', [])
        titles = datas.get('titles', [])
        footers = datas.get('footers', [])
        rows = datas.get('rows', [])
        row_span = datas.get('row_span', [])
        widths = datas.get('widths', [])
        font_size_offset = datas.get('font_size_offset', 5)
        leading_offset = 3
        
        title_normal_xf = ParagraphStyle('normal', fontName='Helvetica', fontSize=8, leading=13,
                    textColor=navy, alignment=TA_LEFT, leftIndent=8, spaceAfter=10)
        title_big_xf = ParagraphStyle('tabledataleft', fontName='Helvetica-Bold', fontSize=12, leading=15, 
                    alignment=TA_CENTER, leftIndent=1, rightIndent=1, spaceAfter=3, spaceBefore=4)
        heading_xf = ParagraphStyle('table_header_style', fontName='Helvetica-Bold', fontSize=font_size_offset, leading=font_size_offset+leading_offset,
                    textColor=black, alignment=TA_CENTER, leftIndent=1, rightIndent=0, spaceBefore=0, spaceAfter=0)
        styles_dict = {
            'text_xf': ParagraphStyle('text_xf', fontName='Helvetica', fontSize=font_size_offset, leading=font_size_offset+leading_offset, textColor=black, alignment=TA_LEFT, leftIndent=6, spaceAfter=5),
            'text_right_xf': ParagraphStyle('text_right_xf', fontName='Helvetica', fontSize=font_size_offset, leading=font_size_offset+leading_offset, textColor=black, alignment=TA_RIGHT, leftIndent=6, spaceAfter=5),
            'text_bold_xf': ParagraphStyle('text_bold_xf', fontName='Helvetica-Bold', fontSize=font_size_offset, leading=font_size_offset+leading_offset, textColor=black, alignment=TA_LEFT, leftIndent=6, spaceAfter=5),
            'text_bold_right_xf': ParagraphStyle('text_bold_right_xf', fontName='Helvetica-Bold', fontSize=font_size_offset, leading=font_size_offset+leading_offset, textColor=black, alignment=TA_RIGHT, leftIndent=6, spaceAfter=5),
            'text_center_bold_xf': ParagraphStyle('text_center_bold_xf', fontName='Helvetica-Bold', fontSize=font_size_offset, leading=font_size_offset+leading_offset, textColor=black, alignment=TA_CENTER, leftIndent=6, spaceAfter=5),
            'text_center_xf': ParagraphStyle('text_center_xf', fontName='Helvetica', fontSize=font_size_offset, leading=font_size_offset+leading_offset, textColor=black, alignment=TA_CENTER, leftIndent=6, spaceAfter=5),
            'number_xf': ParagraphStyle('number_xf', fontName='Helvetica', fontSize=font_size_offset, leading=font_size_offset+leading_offset, textColor=black, alignment=TA_RIGHT, leftIndent=6, spaceAfter=5),
            'number_bold_xf': ParagraphStyle('number_bold_xf', fontName='Helvetica-Bold', fontSize=font_size_offset, leading=font_size_offset+leading_offset, textColor=black, alignment=TA_RIGHT, leftIndent=6, spaceAfter=5),
            'grey_text_xf': ParagraphStyle('grey_text_bold_xf', fontName='Helvetica', fontSize=font_size_offset, leading=font_size_offset+leading_offset, textColor=black, alignment=TA_LEFT, leftIndent=6, spaceAfter=5, backColor=aqua),
            'grey_text_bold_xf': ParagraphStyle('grey_text_bold_xf', fontName='Helvetica-Bold', fontSize=font_size_offset, leading=font_size_offset+leading_offset, textColor=black, alignment=TA_LEFT, leftIndent=6, spaceAfter=5, backColor=aqua),
            'grey_text_bold_right_xf': ParagraphStyle('grey_text_bold_right_xf', fontName='Helvetica-Bold', fontSize=font_size_offset, leading=font_size_offset+leading_offset, textColor=black, alignment=TA_RIGHT, leftIndent=6, spaceAfter=5, backColor=aqua),
            'grey_text_center_bold_xf': ParagraphStyle('grey_text_center_bold_xf', fontName='Helvetica-Bold', fontSize=font_size_offset, leading=font_size_offset+leading_offset, textColor=black, alignment=TA_CENTER, leftIndent=6, spaceAfter=5, backColor=aqua),
            'grey_text_bold_center_xf': ParagraphStyle('grey_text_bold_center_xf', fontName='Helvetica-Bold', fontSize=font_size_offset, leading=font_size_offset+leading_offset, textColor=black, alignment=TA_CENTER, leftIndent=6, spaceAfter=5, backColor=aqua),
            'grey_number_bold_xf': ParagraphStyle('grey_number_bold_xf', fontName='Helvetica-Bold', fontSize=font_size_offset, leading=font_size_offset+leading_offset, textColor=black, alignment=TA_RIGHT, leftIndent=6, spaceAfter=5, backColor=aqua),
            'number_grey_bold_xf': ParagraphStyle('grey_number_bold_xf', fontName='Helvetica-Bold', fontSize=font_size_offset, leading=font_size_offset+leading_offset, textColor=black, alignment=TA_RIGHT, leftIndent=6, spaceAfter=5, backColor=aqua),
            'number_grey_xf': ParagraphStyle('grey_number_bold_xf', fontName='Helvetica', fontSize=font_size_offset, leading=font_size_offset+leading_offset, textColor=black, alignment=TA_RIGHT, leftIndent=6, spaceAfter=5, backColor=aqua),
            'gold_text_bold_xf': ParagraphStyle('gold_text_bold_xf', fontName='Helvetica-Bold', fontSize=font_size_offset, leading=font_size_offset+leading_offset, textColor=black, alignment=TA_LEFT, leftIndent=6, spaceAfter=5, backColor=green),
            'gold_text_bold_right_xf': ParagraphStyle('gold_text_bold_right_xf', fontName='Helvetica-Bold', fontSize=font_size_offset, leading=font_size_offset+leading_offset, textColor=black, alignment=TA_RIGHT, leftIndent=6, spaceAfter=5, backColor=green),
            'gold_text_center_bold_xf': ParagraphStyle('gold_text_center_bold_xf', fontName='Helvetica-Bold', fontSize=font_size_offset, leading=font_size_offset+leading_offset, textColor=black, alignment=TA_CENTER, leftIndent=6, spaceAfter=5, backColor=green),
            'gold_text_bold_center_xf': ParagraphStyle('gold_text_bold_center_xf', fontName='Helvetica-Bold', fontSize=font_size_offset, leading=font_size_offset+leading_offset, textColor=black, alignment=TA_CENTER, leftIndent=6, spaceAfter=5, backColor=green),
            'gold_number_bold_xf': ParagraphStyle('gold_number_bold_xf', fontName='Helvetica-Bold', fontSize=font_size_offset, leading=font_size_offset+leading_offset, textColor=black, alignment=TA_RIGHT, leftIndent=6, spaceAfter=5, backColor=green)
        }
        pretty = report_helper.comma_me # Тоог мянгатын нарийвчлалтай болгодог method
        nullpara = Paragraph('', styles_dict['text_xf'])
        xpara = Paragraph('x', styles_dict['text_center_xf'])
        
        grid = []
        grid.append([Paragraph(u'Маягт', title_normal_xf), Paragraph(u'Байгууллагын нэр: %s' % user.company_id.name, title_normal_xf)])
        grid.append([Paragraph(title, title_big_xf), nullpara])
        
        i = 0
        while i < len(titles):
            grid.append([Paragraph(titles[i], title_normal_xf)])
            if len(titles) > i + 1:
                grid[-1].append(Paragraph(titles[i+1], title_normal_xf))
            i += 2
        
        grid.append([nullpara, Paragraph(u'Огноо: %s' %time.strftime('%Y-%m-%d'), title_normal_xf)])
        tsGrid = TableStyle([
                ('GRID', (0,0), (-1,-1), 0.25, colors.white),
                ('SPAN', (0,1), (1,1))
        ])
        
        t = Table(grid, style=tsGrid, colWidths=[90*mm,110*mm])
        t.hAlign = 'LEFT'
        story.append(t)
        story.append(Spacer(20,20))
        grid = []
        
        for tr in headers:
            grid_tr = []
            for hr in tr:
                if hr is None:
                    grid_tr.append(nullpara)
                else :
                    grid_tr.append(Paragraph(hr, heading_xf))
            grid.append(grid_tr)
        
        for tr in rows:
            grid_tr = []
            for td in tr:
                if td is None:
                    grid_tr.append(nullpara)
                else :
                    _style = '_xf'
                    str_td = u'%s' % td
                    if '<b>' in str_td:
                        _style = '_bold'+ _style
                        td = td.replace('<b>','').replace('</b>','')
                    if '<color>' in str_td:
                        _style = '_grey'+ _style
                        td = td.replace('<color>','').replace('</color>','')
                    if '<c>' in str_td:
                        _style = '_center'+ _style
                        td = td.replace('<c>','').replace('</c>','')
                    if '<str>' in str_td:
                        td = td.replace('<str>','').replace('</str>','')
                    if _style <> '_xf':
                        try:
                            td = float(td)
                        except :
                            pass
                    if type(td) in (type(1), type(1.1)):
                        _style = 'number'+ _style
                        td = pretty(td, separator=',')
                    else :
                        _style = 'text'+ _style
                    
                    if '<head>' in str_td:
                        td = td.replace('<head>','').replace('</head>','')
                        style = heading_xf
                    else :
                        style = styles_dict.get(_style, styles_dict['text_xf'])
                    
                    if '<space/>' in str_td:
                        td = td.replace('<space/>','<font color="white">**</font>')
                    
                    grid_tr.append(Paragraph(td, style))
                
            grid.append(grid_tr)
        
        gstyle = [
            ('BOX', (0,0), (-1,-1), 1.0, colors.black),
            ('GRID', (0,0), (-1,-1), 0.40, colors.black),
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('TOPPADDING', (0,1), (-1,-1), 2),
            ('BOTTOMPADDING', (0,1), (-1,-1), 0),
            ('LEFTPADDING', (0,1), (-1,-1), 0),
            ('RIGHTPADDING', (0,1), (-1,-1), 1)
        ]
        head_height = len(headers)-1
        gstyle.append(('BACKGROUND',(0,0),(-1,head_height),colors.gold))
        if header_span and len(header_span) > 0:
            for head in header_span:
                head_style = ('SPAN',)
                head_style += (head[0],)
                head_style += (head[1],)
                gstyle.append(head_style)
        if row_span and len(row_span) > 0:
            for row in row_span:
                row_style = ('SPAN',)
                row_style += (row[0],)
                row_style += (row[1],)
                gstyle.append(row_style)
        #gstyle += header_span + row_span
        
        t = Table(grid, '100%',repeatRows=len(headers))
        t.setStyle(TableStyle(gstyle))
        _widths = []
        for x in widths:
            _widths.append(x * 5 * mm)
        t._argW = _widths
        total_width = sum(_widths)
        if widths > 200*mm:
            self.CUSTOM_PAGE_WIDTH = sum(_widths) + 20*mm
        t.hAlign = 'CENTER'
        story.append(t)
        
        #spacer
        story.append(Spacer(30,30))
        
        # Тайлангийн доод хэсэгт гарын үсэг зурах жижиг хүснэгт бэлдэнэ.
        tsGrid = TableStyle([
                ('GRID', (0,0), (-1,-1), 0.25, colors.white),
                ('FONT', (0,0),(-1,-1),'Helvetica', 8)
        ])
        
        if footers:
            grid = []
            for f in footers:
                grid.append( [nullpara, Paragraph(f, styles_dict['text_right_xf'])] )
            t = Table(grid, style=tsGrid, colWidths=[10*mm,190*mm])
            t.hAlign = 'LEFT'
        else:
            grid = [
                [Paragraph(u'Боловсруулсан :', styles_dict['text_right_xf']), Paragraph(u'Нягтлан бодогч .........................................../<font color="white">____________________________________</font>/', styles_dict['text_xf'])],
                [Paragraph(u'Хянасан :', styles_dict['text_right_xf']), Paragraph(u'Ерөнхий нягтлан бодогч............................................./<font color="white">____________________________________</font>/', styles_dict['text_xf'])]
            ]
            t = Table(grid, style=tsGrid, colWidths=[60*mm,140*mm])
            t.hAlign = 'LEFT'
        story.append(t)
        
        return story
    
abstract_report_builder2('report.abstract.report.builder', "Abstract Report Builder", 'abstract.report.model', StandardReport.A4_PORTRAIT)


class abstract_builder(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(abstract_builder, self).__init__(cr, uid, name, context=context)
        self.localcontext.update( {
            'time': time,
            'big_title': self._big_title,
            'get_titles': self._get_titles,
            'get_headers': self._get_headers,
            'get_rows': self._get_rows,
            'it_has': self._it_has,
            'clear': self._clear,
            'check_td_class': self._check_td_class,
            'check_header_colspan': self._check_header_colspan,
            'check_header_rowspan': self._check_header_rowspan
        })
        self.context = context

    def set_context(self, objects, data, ids, report_type=None):
        res = self.pool.get(data['model']).get_export_data(self.cr, self.uid, data['ids'], '', context=self.context)
        user = self.pool.get('res.users').browse(self.cr, self.uid, self.uid, context=self.context)
        self.report_datas = res['datas']
        self.localcontext.update({'user':user})
        self.header_span = res['datas']['header_span']
        
        return super(abstract_builder, self).set_context(objects, data, ids, report_type=report_type)

    def _big_title(self):
        return self.report_datas.get('title', 'Abstract Report')
    
    def _get_titles(self):
        return self.report_datas.get('titles', [])
    
    def _get_headers(self):
        return self.report_datas.get('headers', [])
    
    def _get_rows(self):
        return self.report_datas.get('rows', [])
    
    def _it_has(self, col, patterns):
        if col is None:
            return False
        col = '%s' % col
        ok = True
        for pat in patterns:
            if pat == 'bold' and '<b>' not in col:
                ok = False
            elif pat == 'center' and '<c>' not in col:
                ok = False
        return ok
    
    def _clear(self, col):
        if col is None:
            return ''
        col = '%s' % col
        if '<b>' in col:
            col = col.replace('<b>','').replace('</b>','')
        if '<c>' in col:
            col = col.replace('<c>','').replace('</c>','')
        if '<color>' in col:
            col = col.replace('<color>','').replace('</color>','')
        if '<str>' in col:
            col = col.replace('<str>','').replace('</str>','')
        if '<head>' in col:
            col = col.replace('<head>','').replace('</head>','')
        if '<space/>' in col:
            col = col.replace('<space/>','  ')
        if '<level1/>' in col:
            col = col.replace('<level1/>','')
        if '<level2/>' in col:
            col = col.replace('<level2/>','')
        if '<level3/>' in col:
            col = col.replace('<level3/>','')
        if '<level4/>' in col:
            col = col.replace('<level4/>','')
        
        try:
            col = float(col)
        except :
            pass
        if type(col) in (type(1), type(1.1)):
            return report_helper.comma_me(col, separator="'")
        return col
    
    def _check_td_class(self, col):
        orig_col = col
        if col is None:
            return ''
        col = '%s' % col
        classname = ''
        if '<b>' in col:
            col = col.replace('<b>','').replace('</b>','')
        if '<color>' in col:
            col = col.replace('<color>','').replace('</color>','')
            classname += ' color'
        if '<c>' in col:
            col = col.replace('<c>','').replace('</c>','')
            classname += ' center'
        if '<str>' in col:
            col = col.replace('<str>','').replace('</str>','')
        if '<head>' in col:
            col = col.replace('<head>','').replace('</head>','')
        if '<space/>' in col:
            col = col.replace('<space/>','&nbsp;&nbsp;')
            
        try:
            col = float(col)
        except :
            pass
        if type(col) in (type(1), type(1.1)):
            classname += ' number'
        
        return classname
        
    def _check_header_colspan(self, i, j, th):
        tobespan = filter(lambda tup: tup[0][1] == i and tup[0][0] == j, self.header_span)
        if tobespan:
            tobespan = tobespan[0]
            return (tobespan[1][0] - tobespan[0][0]) + 1
        return 0
    
    def _check_header_rowspan(self, i, j, th):
        tobespan = filter(lambda tup: tup[0][1] == i and tup[0][0] == j, self.header_span)
        if tobespan:
            tobespan = tobespan[0]
            return (tobespan[1][1] - tobespan[0][1]) + 1
        return 0
    
class report_abstract_builder(osv.AbstractModel):
    _name = 'report.nomin_base.abstract_report_builder'
    _inherit = 'report.abstract_report'
    _template = 'nomin_base.abstract_report_builder'
    _wrapped_report_class = abstract_builder


class Report(osv.Model):
    _inherit = 'report'
    
    @api.v7
    def get_pdf_base64(self, cr, uid, ids, report_name, html=None, data=None, context=None):
        
        result = self.get_pdf(cr, uid, ids, report_name, html=html, data=data, context=context)
        
        return base64.encodestring(result)
        