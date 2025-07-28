from django.contrib import admin
from .models import Project, Yard, SprinklerHead, Zone, BillOfMaterials, SketchElement

# Register your models here.
admin.site.register(Project)
admin.site.register(Yard)
admin.site.register(SprinklerHead)
admin.site.register(Zone)
admin.site.register(BillOfMaterials)
admin.site.register(SketchElement)
