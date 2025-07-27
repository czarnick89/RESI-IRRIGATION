from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import force_authenticate
from irrigation.models import Project, Yard

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
        print("RESPONSE DATA:", response.data)
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
        self.assertEqual(response.data["status"], "layout_generated_stub")
