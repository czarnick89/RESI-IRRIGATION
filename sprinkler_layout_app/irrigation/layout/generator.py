from shapely.geometry import Point, LineString
from shapely.affinity import translate, rotate
from shapely.geometry import Polygon
from shapely.ops import nearest_points
from irrigation.layout_utils import parse_yard_geometry
import math

SPRINKLER_RADIUS = 10  # feet
COVERAGE_OVERLAP_FACTOR = 0.95
#MAX_SPRINKLERS = 1000  # failsafe cap

def calculate_angle(p1, p2, p3):
    """Returns the interior angle at point p2 (in degrees)"""
    v1 = (p1[0] - p2[0], p1[1] - p2[1])
    v2 = (p3[0] - p2[0], p3[1] - p2[1])
    dot = v1[0]*v2[0] + v1[1]*v2[1]
    mag1 = math.hypot(*v1)
    mag2 = math.hypot(*v2)
    if mag1 == 0 or mag2 == 0:
        return 0  # skip degenerate case
    cos_angle = max(-1, min(1, dot / (mag1 * mag2)))
    return math.degrees(math.acos(cos_angle))

def bisector_direction(p1, p2, p3):
    """Returns the angle (deg) of the angle bisector pointing into the corner"""
    v1 = (p1[0] - p2[0], p1[1] - p2[1])
    v2 = (p3[0] - p2[0], p3[1] - p2[1])
    # Normalize vectors
    mag1 = math.hypot(*v1)
    mag2 = math.hypot(*v2)
    if mag1 == 0 or mag2 == 0:
        return 0
    v1 = (v1[0]/mag1, v1[1]/mag1)
    v2 = (v2[0]/mag2, v2[1]/mag2)
    bisector = ((v1[0] + v2[0]), (v1[1] + v2[1]))
    angle_rad = math.atan2(-bisector[1], -bisector[0])  # point inward
    return math.degrees(angle_rad) % 360

# Helper to create a sector-shaped spray pattern
def create_sprinkler_sector(x, y, radius, angle, direction):
    num_points = 30
    half_angle = angle / 2
    points = [(0, 0)]

    for i in range(num_points + 1):
        theta = math.radians(-half_angle + i * angle / num_points)
        px = radius * math.cos(theta)
        py = radius * math.sin(theta)
        points.append((px, py))

    sector = Polygon(points)
    sector = rotate(sector, direction, origin=(0, 0), use_radians=False)
    return translate(sector, xoff=x, yoff=y)

def generate_sprinkler_layout(yard):
    from shapely.geometry import LineString
    usable_area = parse_yard_geometry(yard)
    if usable_area.is_empty:
        return []

    sprinklers = []
    spacing = SPRINKLER_RADIUS * 1.0  # head-to-head spacing
    coords = list(usable_area.exterior.coords[:-1])

    # === 1. Place corner sprinklers with smart arcs ===
    for i in range(len(coords)):
        prev = coords[i - 1]
        curr = coords[i]
        nxt = coords[(i + 1) % len(coords)]

        v1 = (curr[0] - prev[0], curr[1] - prev[1])
        v2 = (nxt[0] - curr[0], nxt[1] - curr[1])

        len_v1 = math.hypot(*v1)
        len_v2 = math.hypot(*v2)

        if len_v1 < 1e-6 or len_v2 < 1e-6:
            continue

        # Compute interior corner angle
        dot = v1[0]*v2[0] + v1[1]*v2[1]
        corner_angle = math.degrees(math.acos(max(-1, min(1, dot / (len_v1 * len_v2)))))

        if corner_angle >= 180:
            continue  # skip concave or straight corners

        # Compute spray arc needed to fill the exterior corner
        spray_angle = 180 - corner_angle

        # Bisector direction (rough inward spray direction)
        unit_v1 = (v1[0] / len_v1, v1[1] / len_v1)
        unit_v2 = (v2[0] / len_v2, v2[1] / len_v2)
        bisector = (-unit_v1[0] - unit_v2[0], -unit_v1[1] - unit_v2[1])
        bisector_angle = math.degrees(math.atan2(bisector[1], bisector[0])) % 360

        # Adjust to arc starting angle (counterclockwise)
        adjusted_direction = (bisector_angle + 90 - spray_angle / 2) % 360

        sprinklers.append({
            "x": curr[0],
            "y": curr[1],
            "radius": SPRINKLER_RADIUS,
            "angle": spray_angle,
            "direction": adjusted_direction
        })

    # === 2. Place 180° edge sprinklers ===
    for i in range(len(coords)):
        start = coords[i]
        end = coords[(i + 1) % len(coords)]

        segment = LineString([start, end])
        length = segment.length
        num_heads = max(1, int(length // spacing))
        dx = (end[0] - start[0]) / num_heads
        dy = (end[1] - start[1]) / num_heads

        for j in range(1, num_heads):
            x = start[0] + dx * j
            y = start[1] + dy * j

            edge_vector = (end[0] - start[0], end[1] - start[1])
            direction = math.degrees(math.atan2(edge_vector[1], edge_vector[0])) + 90
            direction = (direction + 90) % 360  # rotate to face inward

            sprinklers.append({
                "x": x,
                "y": y,
                "radius": SPRINKLER_RADIUS,
                "angle": 180,
                "direction": direction
            })

    # === 3. Interior 360° sprinkler heads ===
    minx, miny, maxx, maxy = usable_area.bounds
    spacing = SPRINKLER_RADIUS * 1.0  # same head-to-head spacing

    EFFECTIVE_COVERAGE_RADIUS = SPRINKLER_RADIUS * COVERAGE_OVERLAP_FACTOR

    def is_covered(x, y):
        for s in sprinklers:
            dx = s["x"] - x
            dy = s["y"] - y
            dist = math.hypot(dx, dy)
            if dist <= EFFECTIVE_COVERAGE_RADIUS:
                return True
        return False

    y = miny + spacing / 2
    while y < maxy:
        x = minx + spacing / 2
        while x < maxx:
            point = Point(x, y)
            if usable_area.contains(point) and not is_covered(x, y):
                sprinklers.append({
                    "x": x,
                    "y": y,
                    "radius": SPRINKLER_RADIUS,
                    "angle": 360,
                    "direction": 0  # 360° heads don't need orientation
                })
            x += spacing
        y += spacing

    return sprinklers
