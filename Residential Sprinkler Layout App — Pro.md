# Residential Sprinkler Layout App — Product Requirements Document (PRD)

## Tech Stack
- **Frontend:** React (responsive, desktop & mobile browser support)
- **Backend:** Django
- **Database:** PostgreSQL
- **Authentication:** Django’s built-in JWT authentication

## Core User Inputs
- Water pressure & flow rate
- Soil type
- Grass type
- Zip code (for weather/sun data)
- Property sketch (grid-based, supports irregular shapes, mark obstacles, slopes, sun/shade)

## Basic Features (MVP)
- Guest access for trial (limited features, no saving)
- User account creation (email, password, email verification)
- Dashboard/project list for logged-in users
- Guided input forms for yard data (with autosave and ability to return later)
- Grid-based sketch tool (draw/edit shapes, mark obstacles, redo/undo)
- Button to generate sprinkler head layout after sketching
- Manual adjustment of generated layout before saving
- Digital output: sketch with head locations, water coverage (transparent color), overlap (different color), legend, bill of materials (list of heads)
- Save layout to device or email to self
- Multiple projects per user

## Prioritized Usability Features
- Responsive design
- Undo/redo (especially in sketch tool)
- Autosave

## Advanced Features (Future)
- Satellite imagery integration (e.g., Google Earth)
- Smart scheduling (weather-based)
- Support for more landscape types
- Cost estimation
- 3D visualization
- Mobile app version
- Smart controller integration

## Fundamental Problem-Solving Logic
1. **Model the yard/area to irrigate.**
2. **Calculate water needs by area** (based on user input and weather data).
3. **Develop sprinkler head layout**:
   - Ensure full coverage, prioritize overlap over undercoverage, minimize overlap where possible.
   - Indicate significant overlap in visualization.
   - Account for obstacles and excluded areas.
   - Group heads into zones for optimal performance.
   - Use manufacturer data for head capabilities.
4. **Visualization for installation reference**:
   - Show head locations, coverage, overlap, legend, and bill of materials.
   - Highlight suboptimal irrigation areas (overwatering, overspray, etc.).

## User Flow Outline

1. **Onboarding & Authentication**
   - Guest access for trial; account required for saving/full features (email verification).
2. **Project Management**
   - Dashboard/project list; prompt to create new project if none exist; name project at creation.
3. **Yard Data Input**
   - Guided form; autosave partial data; return later to complete.
4. **Yard Sketching**
   - Grid-based tool; draw/edit shapes; mark obstacles; undo/redo.
5. **Sprinkler Layout Generation**
   - Button to generate layout; manual adjustment before saving.
6. **Review & Visualization**
   - Show sketch, head locations, coverage, overlap, legend, bill of materials; save or email output.
7. **Project Saving & Management**
   - Multiple projects per user; dashboard for easy access (future).

## Assumptions
- Target: competent homeowners & professionals
- Digital plans only (for now)
- Privacy/data storage to be addressed in future development phases

## Core Data Models

### User
- `id`: unique identifier
- `email`: string
- `password_hash`: string
- `is_verified`: boolean
- `created_at`: datetime

### Project
- `id`: unique identifier
- `user_id`: reference to User
- `name`: string
- `created_at`: datetime
- `updated_at`: datetime
- `status`: draft/complete/archived

### Yard
- `id`: unique identifier
- `project_id`: reference to Project
- `area`: float (total irrigated area, sq ft/m²)
- `soil_type`: string
- `grass_type`: string
- `zip_code`: string
- `water_pressure`: float (PSI)
- `flow_rate`: float (GPM)

### SketchElement may need to be broken into individual pieces
- `id`: unique identifier
- `sketch_data`: JSON (stores grid, shapes, obstacles, zones, etc.)

### SprinklerHead
- `id`: unique identifier
- `yard_id`: reference to Yard
- `type`: string (rotary, spray, etc.)
- `location`: coordinates (x, y on grid)
- `throw_radius`: float
- `flow_rate`: float (GPM)
- `zone`: integer (zone number)
- `overlap`: boolean (true if significant overlap)

### Zone
- `id`: unique identifier
- `yard_id`: reference to Yard
- `zone_number`: integer
- `sprinkler_heads`: list of SprinklerHead ids
- `total_flow`: float (GPM)
- `area_covered`: float

### BillOfMaterials (BOM)
- `id`: unique identifier
- `project_id`: reference to Project
- `items`: JSON (list of heads, quantities, types)

1. **Start Django Project**
   a. Create new Django project (`django-admin startproject`)*
   b. Set up main app (e.g., `core` or `irrigation`)*
   c. Configure PostgreSQL database in `settings.py`*
   d. Set up virtual environment and install dependencies*

2. **Set Up User Authentication**
   a. Install and configure Django REST Framework (DRF)*
   b. Set up JWT authentication (using `djangorestframework-simplejwt`)*
   c. Create User model (if customizing) skipped for now
   d. Implement registration*, login*, logout*, change password*, and email verification* endpoints - need to add resend email verification, throttling, change email, sign up with 3rd party?, update profile data, session management, logout all sessions

3. **Create Core Backend Models & APIs**
   a. Define models: Project, Yard, SprinklerHead, Zone, BillOfMaterials*
   b. Create serializers for each model*
   c. Build CRUD API endpoints for each model*
   d. Add permissions so users can only access their own data*

4. **Implement Project & Yard Logic**
   a. Add logic for saving partial yard data (autosave)
   b. Implement endpoints for sketch data (accept/save JSON)
   c. Add endpoints for generating sprinkler layouts (stub logic for now)

5. **Set Up React Frontend with Vite**
   a. Scaffold React app with Vite
   b. Set up project structure (pages, components, services)
   c. Configure API calls to Django backend

6. **Build Frontend Features**
   a. User authentication (login, register, email verification)
   b. Dashboard/project list UI
   c. Forms for yard data input (with autosave)
   d. Grid-based sketch tool (basic version)
   e. Button to trigger sprinkler layout generation and display results
   f. Visualization of layout, coverage, overlap, and bill of materials

7. **Connect Frontend and Backend**
   a. Test all API integrations
   b. Handle authentication tokens in frontend
   c. Ensure data flows smoothly between React and Django

8. **Polish and Test MVP**
   a. Add undo/redo and autosave to sketch tool
   b. Test usability on desktop and mobile browsers
   c. Fix bugs and refine UI/UX

9. **Prepare for Deployment**
   a. Add production settings for Django and React
   b. Set up environment variables and secrets
   c. Write deployment/readme documentation