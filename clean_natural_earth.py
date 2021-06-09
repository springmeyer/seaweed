#!/usr/bin/env python

import os
import sys

# hardcoded:
# epsg, in-out
# the_geom
# bounds
# output dir

DEBUG = False

def call(cmd):
    if DEBUG:
        print cmd
    else:
        os.system(cmd)

def setup_db(db):
    call('dropdb %s' % db)
    call('createdb -T template_postgis %s' % db)
    f = open("cleanGeometry.sql", "a")
    f.write("""-- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
--  
-- $Id: cleanGeometry.sql 2008-04-24 10:30Z Dr. Horst Duester $
--
-- cleanGeometry - remove self- and ring-selfintersections from  
--                 input Polygon geometries  
-- http://www.sogis.ch
-- Copyright 2008 SO!GIS Koordination, Kanton Solothurn, Switzerland
-- Version 1.0
-- contact: horst dot duester at bd dot so dot ch
--
-- This is free software; you can redistribute and/or modify it under
-- the terms of the GNU General Public Licence. See the COPYING file.
-- This software is without any warrenty and you use it at your own risk
--   
-- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


CREATE OR REPLACE FUNCTION cleanGeometry(geometry)
   RETURNS geometry AS
$BODY$DECLARE
   inGeom ALIAS for $1;
   outGeom geometry;
   tmpLinestring geometry;
   tmpPolygon geometry;
   Pk geometry;
   Pi geometry;
   nGeometries integer;
   nGeom integer;
   intRingPi geometry;
   nIntRings integer;
   extRingPk geometry;
   isHole boolean;

Begin

   outGeom := NULL;

-- Clean Process for Polygon  
   IF (GeometryType(inGeom) = 'POLYGON' OR GeometryType(inGeom) =  
'MULTIPOLYGON') THEN

-- Only process if geometry is not valid, 
-- otherwise put out without change
     if not isValid(inGeom) THEN

-- create nodes at all self-intersecting lines by union the polygon  
boundaries
-- with the startingpoint of the boundary.  
       tmpLinestring :=  
st_union(st_multi(st_boundary(inGeom)),st_pointn(boundary(inGeom),1));
       outGeom = buildarea(tmpLinestring);
       RETURN st_multi(outGeom);
     else
       RETURN st_multi(inGeom);
     END IF;


------------------------------------------------------------------------------
-- Clean Process for LINESTRINGS, self-intersecting parts of linestrings 
-- will be divided into multiparts of the mentioned linestring 
------------------------------------------------------------------------------
   ELSIF (GeometryType(inGeom) = 'LINESTRING' OR GeometryType(inGeom)  
= 'MULTILINESTRING') THEN

-- create nodes at all self-intersecting lines by union the linestrings
-- with the startingpoint of the linestring.  
     outGeom := st_union(st_multi(inGeom),st_pointn(inGeom,1));
     RETURN outGeom;
   ELSE
     RAISE EXCEPTION 'The input type % is not  
supported',GeometryType(inGeom);
   END IF;	
End;$BODY$
   LANGUAGE 'plpgsql' VOLATILE;
""")
    f.close()
    call('psql %s -f cleanGeometry.sql' % db)

def fix_ne(url,db,clipping_extent):
    filename = os.path.basename(url)
    if not os.path.exists(filename):
        call('wget %(url)s' % locals())
    call('unzip %(filename)s' % locals())
    # note, tricky move nate k. changing zip '-' to shape '_'!
    name = os.path.splitext(filename)[0].replace('-','_')
    call('shp2pgsql -s 4326 %(name)s.shp %(name)s | psql -q %(db)s' % locals())
    # note must quote names in postgres starting with digits
    call("""psql -q %(db)s -c 'update "%(name)s" set the_geom = cleanGeometry(the_geom);'""" % locals())
    clean = '%(name)s_clean.shp' % locals()
    call('pgsql2shp -f %(clean)s %(db)s %(name)s' % locals())
    wrapped = '%(name)s_wrapped.shp' % locals()
    # phony re-project to EPSG:4326 even though it is already in that projection
    # this allows us to apply the dateline wrapping logic in the native projection
    call('ogr2ogr %(wrapped)s %(clean)s -t_srs EPSG:4326 -wrapdateline -skipfailures' % locals())
    merc_clipped = '%(name)s_merc_clipped.shp' % locals()
    call('ogr2ogr %(merc_clipped)s %(wrapped)s -skipfailures -t_srs EPSG:900913 -clipsrc %(clipping_extent)s' % locals())
    call('shapeindex %(merc_clipped)s' % locals())
        
if __name__ == '__main__':
    
    if not len(sys.argv) == 2:
        sys.exit('usage: clean_natural_earth.py <output_directory>')
    target_dir = sys.argv[1]
    if not os.path.exists(target_dir):
        os.mkdir(target_dir)
    else:
        call('rm %s/*' % target_dir)
    os.chdir(target_dir)
    db = 'spring_cleaning'
    setup_db(db)
    base = 'http://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/physical/'
    shps = ['10m-land.zip','10m-coastline.zip','10m-ocean.zip']
    # osm max extents, reasonable restriction from -90.90
    # in mercator are: -20037508 -19929239 20037508 19929239
    clipping_extent = '-179.9 -84.9 179.9 84.9'

    for s in shps:
        url = os.path.join(base,s)
        fix_ne(url,db,clipping_extent)

