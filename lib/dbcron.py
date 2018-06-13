#!/usr/bin/python
#
###########################################################
#                                                         #
# Project: GMP                                            #
# Author:  gianluca.sabella@gmail.com                     #
#                                                         #
# Module:  config.py                                      #
# First version: 18/10/2014                               #
#                                                         #
###########################################################

import os,sys
thisFolder=os.path.dirname(__file__)
prjFolder=os.path.split(thisFolder)[0]
sys.path.append(prjFolder+'/lib')

import dbif
import datetime
import config

try:
    interval = config.ini.get('dbcron', 'interval')
except:
    interval = '1 HOUR'

sql=list()
sql.append(
  "update queue set dwnstatus='Q' where status='CATALOGUED' and pid is Null and dwnstatus='N';")
sql.append(
  "update queue set pid=Null where pid is not null and LAST_UPDATE<(now() - INTERVAL 20 MINUTE);")
sql.append(
  "update queue set status='NEW' where status='NOK' and pid is null and LAST_UPDATE<(now() - interval "+interval+");")

sql.append(
  "delete from files where LAST_UPDATE <(now() - INTERVAL 30 DAY);")


#Query for searching for interferometric pairs
'''
sql.append("""
    INSERT INTO slc (name, area,producttype,relativeorbit)
    SELECT
       concat('Area_',floor(Area(ST_Intersection(p1.footprint, p2.footprint))/Area(p1.footprint)*100)),
       ST_Intersection(p1.footprint, p2.footprint),
       p1.producttype,
       mod(p1.orbit -73, 175)+1 relorb
    FROM product p1, product p2
    WHERE
       (p1.id != p2.id) and 
       p1.producttype=p2.producttype and
       p1.producttype like '%SLC' and
       p1.producttype not like 'WV%SLC' and
       p1.slcid is null and
       p2.slcid is null and
       mod(p1.orbit,175)=mod(p2.orbit,175) and
       AsText(ST_Intersection(p1.footprint, p2.footprint)) is not null and
       Area(ST_Intersection(p1.footprint, p2.footprint))/Area(p1.footprint)>0.6
    ORDER BY Area(ST_Intersection(p1.footprint, p2.footprint))/Area(p1.footprint) desc limit 10;
""")

sql.append("truncate table product_slc;                              ")
sql.append("""insert into product_slc (productid, slcid, area_intersection, area_product)
SELECT P.id, S.id,
    st_area(st_intersection(P.footprint, S.area)),
    st_area(P.footprint)
FROM product P JOIN slc S ON P.producttype=S.producttype
WHERE
    isnull(P.slcid) and (((P.orbit - 73) % 175) + 1)=S.relativeorbit and
    st_area(st_intersection(P.footprint, S.area))IS NOT NULL;
""")
sql.append("""UPDATE product P INNER JOIN product_slc PS on P.id=PS.productid
SET P.SLCID=PS.slcid
WHERE ratio>0.7;
""")

sql.append("""UPDATE slc S INNER JOIN area A
SET S.name =A.name
WHERE substr(S.name,1,4)='Area' and
Area(ST_Intersection(S.area, A.geom))/Area(S.area)>0.9;
""")
sql.append("""UPDATE slc S INNER JOIN area A
SET S.name =A.name
WHERE substr(S.name,1,4)='Area' and
Area(ST_Intersection(S.area, A.geom))/Area(S.area)>0.8;
""")
sql.append("""UPDATE slc S INNER JOIN area A
SET S.name =A.name
WHERE substr(S.name,1,4)='Area' and
Area(ST_Intersection(S.area, A.geom))/Area(S.area)>0.7;
""")
sql.append("""UPDATE slc S INNER JOIN area A
SET S.name =A.name
WHERE substr(S.name,1,4)='Area' and
Area(ST_Intersection(S.area, A.geom))/Area(S.area)>0.6;
""")
sql.append("""UPDATE slc S INNER JOIN area A
SET S.name =A.name
WHERE substr(S.name,1,4)='Area' and
Area(ST_Intersection(S.area, A.geom))/Area(S.area)>0.2;
""")
'''

def main():
    db=dbif.gencur('SELECT * FROM queue')
    for isql in sql:
        out=isql.strip().replace('\n',' ')[:50]
        start = datetime.datetime.now()
        try:
            db.exe(isql)
            out+= ' OK'
        except:
            out+= ' ERROR'
        duration = datetime.datetime.now() - start
        print out + ' (%s sec)' % duration.seconds
    pass

if __name__ == "__main__":
    main()