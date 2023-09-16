from neurospector_backend.database import Database
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import neurospector_backend.utils as u

px.set_mapbox_access_token("pk.eyJ1Ijoia2lyaWxsYmlrdHlhIiwiYSI6ImNrcnJlams4bjF6cHgyb25vdGhxZGFtbzYifQ.xoUPHxQCb8FccmD_q9JpHg")

db = Database(db_name='C:/Users/Kirill/PycharmProjects/neurospector_backend/database.sqlite')
vectors = db.get_vectors()

points = []


for _vector in vectors:
    vector = db.get_vector(_vector['uid'])
    photo = db.get_photo(vector[0]['photo_uid'])
    location = db.get_location(vector[0]['photo_uid'])
    detection = db.get_detection(vector[0]['detection_uid'])
    course = np.deg2rad(location[0]['course'])

    photo_location_diff = photo[0]['timestamp'] - location[0]['timestamp']
    distance_diff = photo_location_diff * location[0]['speed']
    approx_photo_location = {
        'lat': location[0]['latitude'] + u.meters_to_lat_grad(distance_diff) * np.sin(course),
        'lon': location[0]['longitude'] + u.meters_to_lon_grad(
            distance_diff, location[0]['latitude'] + u.meters_to_lat_grad(distance_diff) * np.sin(course)
        ) * np.cos(course)
    }

    coords = u.get_line_coords_from_vector(_vector['uid'], 30)

    points.append({'lat': location[0]['latitude'], 'lon': location[0]['longitude'], 'type': 'location', 'uid': _vector['uid']})
    points.append({'lat': approx_photo_location['lat'], 'lon': approx_photo_location['lon'], 'type': 'approx_photo_location', 'uid': _vector['uid']})
    points.append({'lat': coords[0]['lat'], 'lon': coords[0]['lon'], 'type': 'vector_end', 'uid': _vector['uid']})
    print('\n\n\n\n', points[-1], '\n', points[-2], '\n', points[-3])

fig = px.scatter_mapbox(points, lat='lat', lon='lon', hover_data=['type', 'uid'], hover_name='uid', color='uid')


fig.update_layout(
    mapbox_zoom=10,
    mapbox_center_lat=55.8,
    mapbox_center_lon=37.5,
    margin={"r":0,"t":0,"l":0,"b":0},
    mapbox_style="mapbox://styles/kirillbiktya/ckx28wwrg3y0414k55m16bbtz"
)

fig.show()
