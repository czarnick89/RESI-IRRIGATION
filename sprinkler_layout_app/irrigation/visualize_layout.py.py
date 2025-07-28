import matplotlib.pyplot as plt
from shapely.geometry import Polygon, MultiPolygon
from irrigation.models import Yard
from irrigation.layout_utils import parse_yard_geometry  
import django

django.setup()

def plot_geometry(geom):
    fig, ax = plt.subplots()

    def draw_poly(p, **kwargs):
        x, y = p.exterior.xy
        ax.fill(x, y, **kwargs)
        for interior in p.interiors:
            ix, iy = interior.xy
            ax.fill(ix, iy, color='white')

    if geom.is_empty:
        print("Geometry is empty.")
        return

    if geom.geom_type == "Polygon":
        draw_poly(geom, color='lightgreen', edgecolor='green', alpha=0.6)
    elif geom.geom_type == "MultiPolygon":
        for poly in geom.geoms:
            draw_poly(poly, color='lightgreen', edgecolor='green', alpha=0.6)

    ax.set_aspect('equal')
    plt.title("Usable Yard Area")
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    # Replace this with an actual Yard ID from your test data
    yard = Yard.objects.first()
    usable_area = parse_yard_geometry(yard)
    plot_geometry(usable_area)
