# Location Lifestyle AI V7.2 Journey Map Upgrade

Replace `app.py` and `requirements.txt` in the V7 repository. Keep the V7 `data/` folder unchanged.

## Journey Map
- dedicated first-class tab, not hidden under the editor
- candidate centred in the viewport
- important places positioned by catalogue latitude/longitude
- straight geographic connectors
- Road, Public transport, and Both views
- miles, estimated one-way time, monthly return burden and importance on hover
- colour: green <=60 min, amber 61–120 min, red >120 min
- line thickness: importance
- candidate star and labelled network nodes

## Important limitation
The lines are geographic connectors, not routed roads or railway lines. Road and public-transport times are distance-based estimates:
- Road: 35 mph effective average plus 10 minutes
- Public transport: 45 mph effective average plus 30 minutes

Monthly burden assumes return journeys at the configured visits per month. This is an explanatory prototype, not a journey planner.
