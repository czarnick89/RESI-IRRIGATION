from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
# Create your models here.

class Project(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('complete', 'Complete'),
        ('archived', 'Archived'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Project {self.name}"

class Yard(models.Model):
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='yard')
    area = models.FloatField(null=True, blank=True)
    soil_type = models.CharField(max_length=100)
    grass_type = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)
    water_pressure = models.FloatField(help_text="PSI")
    flow_rate = models.FloatField(help_text="GPM")

    def __str__(self):
        return f"Yard for {self.project}"

class SketchElement(models.Model):
    YARD_ELEMENT_TYPES = [
    ("obstacle", "Obstacle"),
    ("slope", "Slope"),
    ("full_sun", "Full Sun"),
    ("partial_shade", "Partial Shade"),
    ("full_shade", "Full Shade"),
    ("label", "Label"),  
    ]
    
    yard = models.ForeignKey('Yard', on_delete=models.CASCADE, related_name='sketch_elements')
    type = models.CharField(max_length=50, choices=YARD_ELEMENT_TYPES)
    geometry = models.JSONField(help_text="Geometry: point, polyline, or polygon as JSON")
    properties = models.JSONField(default=dict, help_text="Extra properties like color, label, rotation")

    def __str__(self):
        return f"Sketch element for {self.yard}"

class Zone(models.Model):
    yard = models.ForeignKey(Yard, on_delete=models.CASCADE, related_name='zones')
    zone_number = models.IntegerField(null=True, blank=True)
    total_flow = models.FloatField(null=True, blank=True)
    area_covered = models.FloatField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['yard', 'zone_number'], name='unique_zone_number_per_yard')
        ]

    def save(self, *args, **kwargs):
        if self.zone_number is None:
            last = (
                Zone.objects
                .filter(yard=self.yard)
                .order_by('-zone_number')
                .first()
            )
            self.zone_number = (last.zone_number + 1) if last else 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Zone {self.zone_number} for {self.yard}"

class SprinklerHead(models.Model):
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='sprinkler_heads', null=True, blank=True)
    head_number = models.IntegerField(null=True, blank=True, help_text="Sequential number within the zone")
    type = models.CharField(max_length=100)
    location = models.JSONField(null=True, blank=True, help_text="Coordinates like {x: 10, y: 5}")
    throw_radius = models.FloatField()
    flow_rate = models.FloatField()
    angle = models.FloatField(default=360.0)
    direction = models.FloatField(default=0.0, help_text="Angle in degrees where spray is directed (0 = right)")
    overlap = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['zone', 'head_number'], name='unique_head_number_per_zone')
        ]

    def save(self, *args, **kwargs):
        if self.head_number is None:
            last = (
                SprinklerHead.objects
                .filter(zone=self.zone)
                .order_by('-head_number')
                .first()
            )
            self.head_number = (last.head_number + 1) if last else 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"SprinkerHead {self.head_number} for {self.zone}"

class BillOfMaterials(models.Model):
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='bom')
    items = models.JSONField(default=list)  # [{ "type": "Rotary Head", "quantity": 4 }, ...]

    def __str__(self):
        return f"BOM for {self.project}"