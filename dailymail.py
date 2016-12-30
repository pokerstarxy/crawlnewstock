#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re,urllib,socket,socks,os,sys,time,datetime,json,urllib2
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from urllib import urlencode
from pyPdf import PdfFileWriter, PdfFileReader
from bs4 import BeautifulSoup
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.layout import *
from pdfminer.converter import PDFPageAggregator
#socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 1080)
#socket.socket = socks.socksocket                      #开启SS代理
urllist={"SS":"http://ipo.sseinfo.com/info/xgfxyl/","SZ":"http://www.cninfo.com.cn/eipo/index.jsp"}
list_seg=[
                "ONLINE_CIRCULATION",    #网上
                "OFFLINE_ISSUANCE_END_DATE",#缴款日期
                "ONLINE_PURCHASE_LIMIT",   #申购上限
                "SECURITY_NAME",#名字
                "ANNOUNCEMENT_URL",#url
                "TOTAL_ISSUED",   #总量
                "ONLINE_ISSUANCE_DATE", #发行日期
                "OFFLINE_CIRCULATION",#网下
                "PAYMENT_END_DATE",#交款截止
                "ISSUE_PRICE",#价格
                "SECURITY_CODE", #id


          ]   #json 键
html_list={}
dict_week={"1":u"周一","2":u"周二","3":u"周三","4":u"周四","5":u"周五"}
dict_type={"0":u"0网上","1":u"1网下","2":u"2网上网下"}
message_list = []   #SZ信息列表
dict_info={"SS":{},"SZ":{}}     #新股详细信息
info_list=["stockname","start_date","weekday","city","stockid","stock_pur","price","stid_cy","pur_type","total","on_int","under_int","min_pur","end_date","url"]                #新股基础字段
def get_date(day):   #获取日期
    return get_time(day).strftime("%Y-%m-%d")
def get_weekday():
    date_obj=get_time(1)
    t=date_obj.weekday()
    return dict_week[str(t+1)]
def get_time(i):
    count=1
    fx_day=datetime.datetime.now()
    end_day=fx_day
    while count<(i+1):
        end_day=end_day+datetime.timedelta(days=1)
        sta_tus=get_holiday(end_day.strftime("%Y%m%d"))
        if sta_tus:
            count+=1
        else:
            count+=0
    return end_day
def get_end():
    return get_time(3).strftime("%Y-%m-%d")
def get_holiday(strdate):
    url = 'http://api.k780.com:88'
    params = {
        'app': 'life.workday',
        'date': strdate,
        'appkey': '22387',
        'sign': '4647060331a7fa81d4ac79d2f0d408e8',
        'format': 'json',
    }

    params = urlencode(params)
    f = urllib.urlopen('%s?%s' % (url, params))
    nowapi_call = f.read()
    a_result = json.loads(nowapi_call)

    if a_result["result"]["workmk"] == "1":  #工作日 1
        return True
    else:
        return False
def get_num(str_a):
    if str_a=="null":
        return 0
    else:
        tt=""
        a=str_a.split(".")
        if len(a)==2:
            s=4-len(a[1])
            for i in xrange(s):
                tt=tt+"0"
            return a[0]+a[1]+tt
        if len(a)==1:
            return str_a+"0000"
def downpdf(stockid,url_l,i):
    downpath=r"C:\Users\Administrator\Desktop\%s_%s.pdf" %(stockid,i)
    urllib.urlretrieve(url_l,downpath)
def get_ssurl(stockid):
    sta_ss=0

    time_i=time.strftime("%Y-%m-%d", time.localtime())
    timei=time.strftime("%Y%m%d",time.localtime())
    for i in xrange(1,10):
        c = 0
        downpath = r"C:\Users\Administrator\Desktop\%s_%s.pdf" % (stockid,i)
        save_name = r"D:\mysoft\personnal\python\code\%s_%s.txt" % (stockid,i)
        spath="http://static.sse.com.cn/disclosure/listedinfo/announcement/c/%s/%s_%s_%s.pdf" %(time_i,stockid,timei,i)
        try:
            print "begin download %s_%s" %(stockid,i)
            downpdf(stockid,spath,i)
            print "end"
            time.sleep(5)

        except SyntaxError:
            print "not exists ",i
            break
        print "begin trans"
        f=open(downpath,"rb")
        Pdf2Txt(f,save_name)
        f.close()
        print "end"
        print "begin del"
        os.remove(downpath)
        print "end del"
        with open(save_name,"r") as f:
            for line in f:
                c=c+1
                if c<20:
                    if re.search("发行公告", line):
                        sta_ss=1
                        break
                else:
                    break
        print "begin del"
        os.remove(save_name)
        print "end del"
        if sta_ss==1:
            return spath
        else:
            pass
def Pdf2Txt(Path,Save_name):
    page_count=1

    #来创建一个pdf文档分析器
    parser = PDFParser(Path)
    #创建一个PDF文档对象存储文档结构
    document = PDFDocument(parser)
    # 检查文件是否允许文本提取
    if not document.is_extractable:
        raise PDFTextExtractionNotAllowed
    else:
        # 创建一个PDF资源管理器对象来存储共赏资源
        rsrcmgr=PDFResourceManager()
        # 设定参数进行分析
        laparams=LAParams()
        # 创建一个PDF设备对象
        # device=PDFDevice(rsrcmgr)
        device=PDFPageAggregator(rsrcmgr,laparams=laparams)
        # 创建一个PDF解释器对象
        interpreter=PDFPageInterpreter(rsrcmgr,device)
        # 处理每一页

        for page in PDFPage.create_pages(document):
            if page_count == 1:
                page_count+=1
                interpreter.process_page(page)
                # 接受该页面的LTPage对象
                layout=device.get_result()
                for x in layout:
                    if(isinstance(x,LTTextBoxHorizontal)):
                        with open('%s'%(Save_name),'a') as f:
                            f.write(x.get_text().encode('utf-8')+'\n')
            else:
                break
def geturl(urllist):        #获取网页内容，正则获取pdf文档url
    for keyname in urllist:
        cont=urllib2.urlopen(urllist[keyname]).read()
        analyse_html(keyname,cont)
def get_szurl(stockid):
    urlname="http://www.cninfo.com.cn/eipo/stockinquiry/%s.js"%stockid
    req=urllib2.urlopen(urlname).read()
    t = re.findall(re.compile("\w+=(\[\[.*?\]\])*"), req)
    cont = json.loads(t[0].decode("gbk"), encoding="utf8")
    for i in cont:
        if re.search("发行公告".decode("utf8"), i[2]):
            return "http://www.cninfo.com.cn/" + i[1]
def change_id(id):
    urlname = "http://vip.stock.finance.sina.com.cn/corp/go.php/vRPD_NewStockIssue/page/1.phtml"
    req = urllib2.urlopen(urlname).read()
    a = []
    soup = BeautifulSoup(req, "lxml", from_encoding="utf8")
    tt = soup.find_all("div", {"align": "center"})
    for i in tt:
        a.append(i.string)
    return a[a.index(id) + 1]
def analyse_html(key_nm,html_ct):
    sp=BeautifulSoup(html_ct,"lxml",from_encoding="utf-8")
    if key_nm=="SS":
        user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0"
        req = urllib2.Request("http://ipo.sseinfo.com/info/commonQuery.do?jsonCallBack=jsonpCallback69744&isPagination=true&sqlId=COMMON_SSE_IPO_IPO_LIST_L&pageHelp.pageSize=15&_=1482891164024")
        req.add_header('User-Agent', user_agent)
        cont = urllib2.urlopen(req).read()
        t = re.findall(re.compile("\w+\((.*?)\)"), cont)
        vv = json.loads(t[0], encoding="utf8")
        cont_list = vv["pageHelp"]["data"]
        for i in cont_list:
            codeid=i["SECURITY_CODE"]
            if i["ONLINE_ISSUANCE_DATE"]==get_date(1):
                dict_info["SS"][codeid]={}
                dict_info["SS"][codeid]["stockid"] = i["SECURITY_CODE"]
                dict_info["SS"][codeid]["stockname"] = i["SECURITY_NAME"]
                dict_info["SS"][codeid]["start_date"] = i["ONLINE_ISSUANCE_DATE"]
                dict_info["SS"][codeid]["price"] = i["ISSUE_PRICE"][:-2]
                dict_info["SS"][codeid]["city"] = u"上海"
                dict_info["SS"][codeid]["weekday"] = get_weekday()
                dict_info["SS"][codeid]["stock_pur"] = change_id(i["SECURITY_CODE"])
                dict_info["SS"][codeid]["stid_cy"] =i["SECURITY_CODE"]+ "SS"
                dict_info["SS"][codeid]["min_pur"] = get_num(i["ONLINE_PURCHASE_LIMIT"])
                dict_info["SS"][codeid]["end_date"] = i["PAYMENT_END_DATE"]
                dict_info["SS"][codeid]["url"] = get_ssurl(i["SECURITY_CODE"])
                dict_info["SS"][codeid]["total"] = get_num(i["TOTAL_ISSUED"])
                dict_info["SS"][codeid]["on_int"] = get_num(i["ONLINE_CIRCULATION"])
                if i["OFFLINE_CIRCULATION"]==None:
                    dict_info["SS"][codeid]["pur_type"]=dict_type["0"]
                    dict_info["SS"][codeid]["under_int"] = ""

                else:
                    dict_info["SS"][codeid]["pur_type"] = dict_type["2"]
                    dict_info["SS"][codeid]["under_int"] = u"，网下发行量： "+get_num(i["OFFLINE_CIRCULATION"])
    elif key_nm=="SZ":
        vv = sp.find_all("tr", id=re.compile("newstock_(\d+)"))
        for i in vv:
            message_list.append(i.get_text().strip().split("\n"))
        for per_mes in message_list:
            if per_mes[2]==get_date(1):
                dict_info["SZ"][per_mes[0]]={}
                dict_info["SZ"][per_mes[0]]["stockid"]=per_mes[0]
                dict_info["SZ"][per_mes[0]]["stockname"]=per_mes[1]
                dict_info["SZ"][per_mes[0]]["start_date"]=get_date(1)
                dict_info["SZ"][per_mes[0]]["price"]=per_mes[3]
                dict_info["SZ"][per_mes[0]]["city"]=u"深圳"
                dict_info["SZ"][per_mes[0]]["weekday"]=get_weekday()
                dict_info["SZ"][per_mes[0]]["stock_pur"]=per_mes[0]
                dict_info["SZ"][per_mes[0]]["stid_cy"] = per_mes[0]+"SZ"
                dict_info["SZ"][per_mes[0]]["min_pur"] = get_num(per_mes[9])
                dict_info["SZ"][per_mes[0]]["end_date"] =get_end()
                dict_info["SZ"][per_mes[0]]["url"]=get_szurl(per_mes[0])
                dict_info["SZ"][per_mes[0]]["total"] = get_num(per_mes[5])
                dict_info["SZ"][per_mes[0]]["on_int"] = get_num(per_mes[6])
                if per_mes[5]==per_mes[6]:
                    dict_info["SZ"][per_mes[0]]["pur_type"]=dict_type["0"]
                    dict_info["SZ"][per_mes[0]]["under_int"] = ""
                else:
                    dict_info["SZ"][per_mes[0]]["pur_type"] = dict_type["2"]
                    dict_info["SZ"][per_mes[0]]["under_int"] = u"，网下发行量： "+get_num(str((float(per_mes[5]) - float(per_mes[6]))))
def replacecont(cont):                         # cont={SS:{stock:{name:stock},}}
    for i,j in cont.items():
        for p,q in j.items():
            spath=r"C:\Users\Administrator\Desktop\%s.html" %p
            html_list[q["stockname"]]=spath

            with open("modual.html","r") as f ,open(spath,"w") as l :
                for line in f:
                    new_info = line
                    for ba_info in info_list:

                        new_info=new_info.replace(ba_info,q[ba_info].encode("utf8"))
                    l.write(new_info)
def mail_custermer(html_list):
    for p,q in html_list.items():
        subject_cont=u"温馨提示--关于新股“%s”的申购提示"%p
        with open(q,"rb") as f:
            cont=f.read()
        msg = MIMEText(cont, 'html', 'utf-8')
        # msg["From"] = formataddr(["poker", 'pokerstar_xy@sina.com'])
        # msg['To'] = formataddr(["showgirl", '857607332@qq.com'])
        # msg['Subject'] = subject_cont
        # server = smtplib.SMTP("smtp.sina.com")
        # server.login('pokerstar_xy@sina.com', 'xy906307')
        # server.sendmail('pokerstar_xy@sina.com', ["857607332@qq.com"], msg.as_string())
        msg["From"] = formataddr(["someone", 'XXX@sina.com'])
        msg['To'] = formataddr(["help", 'xx@xx.com'])
        msg['Subject'] = subject_cont
        server = smtplib.SMTP("domain")
        server.login('XXX@sina.com', 'xxxxxx')
        server.sendmail('XXX@sina.com', ["xx@xx.com"], msg.as_string())
        server.quit()
        os.remove(q)
if __name__=="__main__":
    geturl(urllist)
    replacecont(dict_info)
    mail_custermer(html_list)









