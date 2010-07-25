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
    call('wget http://www.sogis1.so.ch/sogis/dl/postgis/cleanGeometry.sql')
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

