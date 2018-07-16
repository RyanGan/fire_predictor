# ---------------------------------------
# Title: Fire Predictor Flask Application
# Author: Ryan Gan
# Date Created: 2018-07-13
# ---------------------------------------

# loading required packages
from flask import Flask, render_template, request, redirect
# bokeh
from bokeh.plotting import figure, show, output_file
from bokeh.tile_providers import CARTODBPOSITRON
from bokeh.models import HoverTool
from bokeh.io import output_notebook
from bokeh.models import ColumnDataSource
from bokeh.palettes import RdYlGn6 as palette
from bokeh.models import LogColorMapper
from bokeh.embed import components

# pandas
import pandas as pd
# change lat lon projection
from pyproj import Proj, transform
# geopandas
import geopandas as gp
import pysal as ps
# math
import math

# load data -----
current_fires = pd.read_csv('./app_data/fire_locations.csv')
# transform lat/lon coordinates to mercator projection
fire_coords = []
for i in zip(current_fires.longitude, current_fires.latitude):
    coords = transform(Proj(init='epsg:4326'), Proj(init='epsg:3857'), i[0], i[1])
    fire_coords.append(coords)
    
   # output vectors of lons and lats
lons = []
lats = []
for lon, lat in fire_coords:
    lons.append(lon)
    lats.append(lat)
    
# output vector of fire size
size = []
for s in current_fires.area:
    size.append(math.sqrt(s/50))
    
# read in shapefile for grid
grid = gp.read_file('./app_data/grid_poly/grid_poly.shp')
# convert projection to mercator
grid = grid.to_crs(crs={'init':'epsg:3857'})

def getPolyCoords(row, geom, coord_type):
    """Returns the coordinates ('x' or 'y') of edges of a Polygon exterior"""

    # Parse the exterior of the coordinate
    exterior = row[geom].exterior

    if coord_type == 'x':
        # Get the x coordinates of the exterior
        return list( exterior.coords.xy[0] )
    elif coord_type == 'y':
        # Get the y coordinates of the exterior
        return list( exterior.coords.xy[1] )
    
    
# Get the Polygon x and y coordinates
grid['x'] = grid.apply(getPolyCoords, geom='geometry', coord_type='x', axis=1)
grid['y'] = grid.apply(getPolyCoords, geom='geometry', coord_type='y', axis=1)

# making copy without geometry 
grid_nogeo = grid.drop('geometry', axis=1).copy()

# Create the color mapper
color_mapper = LogColorMapper(palette=palette)

# grid to column data source
gsource = ColumnDataSource(grid_nogeo)

# define app name
app = Flask(__name__)


@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/index', methods=['GET'])
def make_map():
    # initial figure
    p = figure(x_range=(-14230740, -7866287), y_range=(3008561, 6207909), 
               plot_width=800, plot_height=600,
               x_axis_type="mercator", y_axis_type="mercator", 
               tools = 'pan, zoom_in, zoom_out, reset, save, wheel_zoom')
    # patches
    r1 = p.patches('x', 'y', source=gsource,
             fill_color={'field': 'fire_risk', 'transform': color_mapper},
             fill_alpha=0.3, line_color=None, line_width=0.05)
    p.add_tools(HoverTool(renderers=[r1], tooltips=[("Fire Risk", "@fire_risk{1.11}")]))
    
    # add fire circles based on location
    p.scatter(x = lons, y = lats, size = size, marker='triangle', line_color = 'red',
              fill_color = None, alpha = 0.3)
    # add stamen basemap
    p.add_tile(CARTODBPOSITRON)

    script, div = components(p)

    return render_template('plot.html', p_script=script, p_div=div)
    
if __name__ == '__main__':
  app.run(host='0.0.0.0', port=33507, debug=True)