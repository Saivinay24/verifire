"""The 25 areas the judges' test tool uses (brief, Appendix B).

Map points are always these area centroids, never a reporter's own location.
"""

from typing import NamedTuple


class Area(NamedTuple):
    pincode: str
    locality: str
    city: str
    lat: float
    lng: float


AREAS: tuple[Area, ...] = (
    Area("560102", "HSR Layout", "Bengaluru", 12.9116, 77.6473),
    Area("560038", "Indiranagar", "Bengaluru", 12.9784, 77.6408),
    Area("560034", "Koramangala", "Bengaluru", 12.9352, 77.6245),
    Area("560066", "Whitefield", "Bengaluru", 12.9698, 77.7500),
    Area("560076", "BTM Layout", "Bengaluru", 12.9166, 77.6101),
    Area("560011", "Jayanagar", "Bengaluru", 12.9299, 77.5826),
    Area("560037", "Marathahalli", "Bengaluru", 12.9591, 77.6974),
    Area("560103", "Bellandur", "Bengaluru", 12.9260, 77.6762),
    Area("560100", "Electronic City", "Bengaluru", 12.8452, 77.6602),
    Area("560078", "JP Nagar", "Bengaluru", 12.9077, 77.5851),
    Area("560003", "Malleshwaram", "Bengaluru", 13.0035, 77.5709),
    Area("560010", "Rajajinagar", "Bengaluru", 12.9915, 77.5520),
    Area("560024", "Hebbal", "Bengaluru", 13.0358, 77.5970),
    Area("560064", "Yelahanka", "Bengaluru", 13.1007, 77.5963),
    Area("560070", "Banashankari", "Bengaluru", 12.9250, 77.5468),
    Area("400050", "Bandra West", "Mumbai", 19.0596, 72.8295),
    Area("110016", "Hauz Khas", "Delhi", 28.5494, 77.2001),
    Area("500081", "Madhapur", "Hyderabad", 17.4486, 78.3908),
    Area("600020", "Adyar", "Chennai", 13.0012, 80.2565),
    Area("411014", "Viman Nagar", "Pune", 18.5679, 73.9143),
    Area("700091", "Salt Lake Sector V", "Kolkata", 22.5790, 88.4290),
    Area("380015", "Satellite", "Ahmedabad", 23.0260, 72.5085),
    Area("302017", "Malviya Nagar", "Jaipur", 26.8570, 75.8080),
    Area("226010", "Gomti Nagar", "Lucknow", 26.8540, 80.9990),
    Area("682030", "Kakkanad", "Kochi", 10.0159, 76.3419),
)

AREAS_BY_PINCODE: dict[str, Area] = {a.pincode: a for a in AREAS}
