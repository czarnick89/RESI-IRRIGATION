from shapely.geometry import shape, Polygon
from shapely.ops import unary_union
from .models import SketchElement

def parse_yard_geometry(yard):
    """
    Parses sketch elements for a yard and returns plantable area (as polygons) 
    with obstacles removed.
    """
    sketch_elements = SketchElement.objects.filter(yard=yard)

    plantable_polygons = []
    obstacle_polygons = []

    for element in sketch_elements:
        if not element.geometry:
            continue  # skip empty geometry

        geom = shape(element.geometry)  # assumes GeoJSON-style dict

        if element.type in ['full_sun', 'partial_shade', 'full_shade']:
            plantable_polygons.append(geom)
        elif element.type == 'obstacle':
            obstacle_polygons.append(geom)

    # Union all plantable zones into one polygon
    usable_area = unary_union(plantable_polygons)

    # Remove obstacles from usable area
    if obstacle_polygons:
        obstacles_union = unary_union(obstacle_polygons)
        usable_area = usable_area.difference(obstacles_union)

    return usable_area