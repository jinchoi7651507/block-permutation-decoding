import sys, json, re, xml.etree.ElementTree as ET
from pathlib import Path
S=Path(sys.argv[1])
recs=[(63,'PMC12875639'),(79,'PMC13278741'),(98,'PMC12282809'),(127,'PMC12578254'),(137,'PMC12919843'),(304,'PMC12768531'),(305,'PMC11950404'),(368,'PMC11126972'),(375,'PMC12063830'),(476,'PMC12003885'),(508,'PMC13263383'),(517,'PMC13648456'),(518,'PMC11184972'),(521,'PMC12834399'),(663,'PMC11189588'),(669,'PMC13223030'),(901,'PMC13503106'),(902,'PMC13168177'),(1020,'PPR992842'),(1127,'PMC12028213'),(1209,'PMC13578614'),(1288,'PMC11368949'),(1358,'PMC13269409'),(1359,'PMC12650059'),(1461,'PMC13319115'),(1522,'PMC10871532'),(1559,'PMC11420495'),(1624,'PMC11659776'),(1638,'PMC13144522'),(1691,'PMC12218136'),(1758,'PMC11709427'),(1763,'PMC13388300'),(1795,'PMC12402162'),(1798,'PMC11228270'),(1894,'PMC12248717'),(1898,'PMC13461148'),(2021,'PMC12947046'),(2054,'PMC12053643'),(2116,'PMC12202505'),(2139,'PMC11379379')]
def txt(e): return re.sub(r'\s+',' ',''.join(e.itertext())).strip() if e is not None else ''
for o,p in recs:
    out=[f"RECORD order {o}, {p}"]
    x=S/'xml'/f'{p}.xml'
    ok=False
    if x.exists() and x.stat().st_size>1000:
        try:
            r=ET.parse(x).getroot(); ok=True
        except Exception as e: out.append(f"XML parse error: {e}")
    if ok:
        art=r.find('.//article') if r.tag!='article' else r
        art=art if art is not None else r
        out.append("article-type: "+str(art.get('article-type')))
        out.append("TITLE: "+txt(r.find('.//article-title')))
        out.append("ABSTRACT: "+txt(r.find('.//abstract'))[:4000])
        body=r.find('.//body')
        if body is None: out.append("BODY: none in the XML")
        else:
            secs=body.findall('./sec')
            out.append("SECTION TITLES: "+" | ".join(txt(s.find('title')) for s in secs))
            meth=[s for s in secs if re.search(r'method|material|procedure|experimental',txt(s.find('title')),re.I)]
            if meth:
                m=" ".join(txt(s) for s in meth)
                out.append("METHODS-LIKE SECTIONS (first 25,000 characters): "+m[:25000])
            else:
                out.append("BODY (no methods-titled section; first 20,000 characters): "+txt(body)[:20000])
    else:
        c=S/'core'/f'{p}.json'
        if c.exists():
            res=json.load(open(c)).get('resultList',{}).get('result',[])
            if res:
                d=res[0]
                out.append("NO FULL TEXT (fullTextXML unavailable); Europe PMC core record:")
                out.append("TITLE: "+str(d.get('title')))
                out.append("pubType: "+str(d.get('pubTypeList')))
                out.append("ABSTRACT: "+re.sub('<[^>]+>','',str(d.get('abstractText')))[:5000])
    (S/'rec'/f'{o:04d}.txt').write_text("\n".join(out))
    print(o,p,len("\n".join(out)))
