from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import force_authenticate
from irrigation.models import Project, Yard, SketchElement
import matplotlib.pyplot as plt
from django.contrib.auth import get_user_model
from shapely.geometry import shape
import json
from irrigation.layout_utils import parse_yard_geometry
from matplotlib.patches import Wedge

class FullProjectSetupTest(APITestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='NewPass123!')
        self.client.force_authenticate(user=self.user)
        self.url = "/api/v1/projects/full-setup/"


    def test_full_project_setup(self):
        mock_data = {
            "project": {
                "name": "Backyard Irrigation Test"
            },
            "yard": {
                "soil_type": "loam",
                "grass_type": "bermuda",
                "zip_code": "78701",
                "water_pressure": 50,
                "flow_rate": 8.0
            },
            "sprinkler_heads": [
                {
                    "type": "rotary",
                    "throw_radius": 15.0,
                    "flow_rate": 2.0,
                    "angle": 360,
                    "direction": 0
                }
            ],
            "sketch_elements": [
                {
                    "type": "label",
                    "geometry": {
                        "type": "point",
                        "coordinates": [10, 20]
                    },
                    "properties": {
                        "width": 100,
                        "height": 50,
                        "rotation": 0
                    }
                }
            ]
        }

        response = self.client.post(self.url, mock_data, format='json')
        #print("RESPONSE DATA:", response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("project_id", response.data)

class GenerateSprinklerLayoutTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='layoutuser', password='testpass123')
        self.client.login(username='layoutuser', password='testpass123')

        # Create Project + Yard
        self.project = Project.objects.create(name="Test Project", user=self.user)
        self.yard = Yard.objects.create(
            project=self.project,
            soil_type='loam',
            grass_type='bermuda',
            zip_code='12345',
            water_pressure=50,
            flow_rate=10.0
        )

    def test_generate_layout_stub(self):
        url = '/api/v1/projects/generate-layout/'
        response = self.client.post(url, {"yard_id": self.yard.id}, format='json')
        print("LAYOUT RESPONSE:", response.data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("zones", response.data)
        self.assertEqual(response.data["status"], "geometry_parsed")

class ParseGeometryTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='geomuser', password='testpass123')
        self.client.login(username='geomuser', password='testpass123')

        self.project = Project.objects.create(name="Geometry Project", user=self.user)
        self.yard = Yard.objects.create(
            project=self.project,
            soil_type='loam',
            grass_type='fescue',
            zip_code='54321',
            water_pressure=45,
            flow_rate=9.0
        )

        # Full sun polygon (40 x 30)
        SketchElement.objects.create(
            yard=self.yard,
            type="full_sun",
            geometry={
                "type": "Polygon",
                "coordinates": [[[0, 0], [40, 0], [40, 30], [0, 30], [0, 0]]]
            },
            properties={"width": 40, "height": 30}
        )

        # Obstacle in center (10 x 10)
        SketchElement.objects.create(
            yard=self.yard,
            type="obstacle",
            geometry={
                "type": "Polygon",
                "coordinates": [[[15, 10], [25, 10], [25, 20], [15, 20], [15, 10]]]
            },
            properties={"width": 10, "height": 10}
        )

    def test_geometry_parsing(self):
        url = '/api/v1/projects/generate-layout/'
        response = self.client.post(url, {"yard_id": self.yard.id}, format='json')
        print("LAYOUT RESPONSE:", response.data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("area_bounds", response.data)

class VisualLayoutTest(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser4", password="testpass")
        self.client.force_authenticate(user=self.user)

        self.project = Project.objects.create(user=self.user, name="Test Project")
        self.yard = Yard.objects.create(
            project=self.project,
            water_pressure=50.0,
            flow_rate=10.0,
            soil_type="loam",
            grass_type="fescue",
            zip_code="12345",
        )

        # Add full-sun yard polygon (irregular 5-sided shape)
        SketchElement.objects.create(
            yard=self.yard,
            type="full_sun",
            geometry={
                "type": "Polygon",
                "coordinates": [[
                    [0, 0],      # Bottom-left
                    [60, 0],     # Bottom-right
                    [60, 30],    # Mid-right
                    [30, 50],    # Top peak (non-90° corner)
                    [0, 30],     # Mid-left
                    [0, 0]       # Close polygon
                ]]
            },
            properties={"sun_exposure": "full"}
        )

        # Add 10x10 obstacle in the middle
        SketchElement.objects.create(
            yard=self.yard,
            type="obstacle",
            geometry={
                "type": "Polygon",
                "coordinates": [[[15, 10], [25, 10], [25, 20], [15, 20], [15, 10]]]
            },
            properties={"type": "shed"}
        )

    def test_plot_yard_geometry(self):
        response = self.client.post("/api/v1/projects/generate-layout/", {"yard_id": self.yard.id}, format="json")
        #print("STATUS CODE:", response.status_code)
        #print("RESPONSE CONTENT:", response.content)

        # Don't try to access .data unless it's 200 OK
        self.assertEqual(response.status_code, 200)

        # sprinklers = response.data.get("sprinklers", [])
        # print("SPRINKLERS:", sprinklers)

        geom = parse_yard_geometry(self.yard)

        if geom.is_empty:
            print("Geometry is empty. Nothing to visualize.")
            return

        fig, ax = plt.subplots()
        ax.set_title("Parsed Usable Area")
        ax.set_aspect('equal')

        if geom.geom_type == "Polygon":
            x, y = geom.exterior.xy
            ax.fill(x, y, alpha=0.5, fc='green', ec='black')
            for interior in geom.interiors:
                x, y = interior.xy
                ax.fill(x, y, alpha=0.5, fc='red', ec='black')

        elif geom.geom_type == "MultiPolygon":
            for polygon in geom.geoms:
                x, y = polygon.exterior.xy
                ax.fill(x, y, alpha=0.5, fc='green', ec='black')
                for interior in polygon.interiors:
                    x, y = interior.xy
                    ax.fill(x, y, alpha=0.5, fc='red', ec='black')

        sprinklers = response.data.get("sprinklers", [])
        self.assertGreater(len(sprinklers), 0, "Expected at least one sprinkler")
        self.assertTrue(all("x" in s and "y" in s for s in sprinklers), "Missing coordinates")

        for s in sprinklers:
            x, y = s["x"], s["y"]
            r = s["radius"]
            angle = s.get("angle", 360)
            direction = s.get("direction", 0)

            if angle < 360:
                # Draw wedge arc
                start = direction
                end = direction + angle
                wedge = Wedge((x, y), r, start, end, color="blue", alpha=0.3)
                ax.add_patch(wedge)
            else:
                # Full circle
                circle = plt.Circle((x, y), r, color="blue", alpha=0.2)
                ax.add_patch(circle)

            ax.plot(x, y, 'ko')  # Black dot at center

        plt.show()
