import queries

from sqlalchemy.orm import Session
from models import Product


watchlist = {
    "CU3244-100": { "sizes": [], "include_restricted": True }, # Ben & Jerry's
    "BQ6817-602": { "sizes": [], "include_restricted": True }, # Dunk Low Bart
    "DO6274-001": { "sizes": ["11"], "include_restricted": False }, # Union LA Slide
    "DH7577-001": { "sizes": [], "include_restricted": False }, # Dunk Low Fossile Rose
    "DH7722-001": { "sizes": [], "include_restricted": True }, # Dunk Low Polaroid
    "DJ9649-400": { "sizes": [], "include_restricted": True }, # Dunk Low Union
    "DN1803-300": { "sizes": ["11"], "include_restricted": True }, # Air Max Concepts Mellow
    "DN1803-500": { "sizes": [], "include_restricted": True }, # Air Max Concepts Far Out
    "DN1803-900": { "sizes": [], "include_restricted": True }, # Air Max Concepts Heavy
    "DD1875-100": { "sizes": [], "include_restricted": True }, # Sacai Vapor Waffle White
    "DD1875-001": { "sizes": [], "include_restricted": True }, # Sacai Vapor Waffle Black
    "DD8338-001": { "sizes": [], "include_restricted": True }, # Dunk Low Vast Gray
    "BQ4422-400": { "sizes": [], "include_restricted": True }, # Jordan 1 1985 Georgetown 
    "CT8527-016": { "sizes": ["9", "9.5", "10", "10.5", "11", "11.5"], "include_restricted": True }, # Jordan 4 Red Thunder
    "DO7097-100": { "sizes": [], "include_restricted": True }, # Jordan 1 A Ma Maniere
    "BQ6817-010": { "sizes": [], "include_restricted": True }, # Dunk Low Fog
    "CW7093-600": { "sizes": [], "include_restricted": True }, # Dunk High Strawberry Cough
    "555088-134": { "sizes": [], "include_restricted": True }, # Jordan 1 University Blue
    "CZ0775-801": { "sizes": [], "include_restricted": True }, # Jordan 1 Low Starfish
    "DV3029-100": { "sizes": [], "include_restricted": True }, # Dunk Low Ocean
    "DN3802-001": { "sizes": [], "include_restricted": True }, # Jordan 2 Union
    "BQ6817-501": { "sizes": ["11", "11.5", "12"], "include_restricted": True }, # Dunk Low Red Plum
    "DH6927-111": { "sizes": [], "include_restricted": True }, # Jordan 4 Military Black
    "555088-063": { "sizes": [], "include_restricted": True }, # Jordan 1 Patent Bred
    "DM0807-600": { "sizes": [], "include_restricted": True }, # Dunk Low Cherry
    "DR7515-200": { "sizes": [], "include_restricted": True }, # Travis Air Trainer Brown
    "DR7515-001": { "sizes": [], "include_restricted": True }, # Travis Air Trainer Gray
    "DO9392-200": { "sizes": [], "include_restricted": True }, # Travis Air Max Brown
    "DO9392-700": { "sizes": [], "include_restricted": True }, # Travis Air Max Gold
    "DO9392-701": { "sizes": [], "include_restricted": True }, # Travis Air Max Special (Lemon)
    "DM0807-300": { "sizes": [], "include_restricted": True }, # Dunk Low Sour Apple
    "DQ4040-400": { "sizes": ["11", "11.5", "12"], "include_restricted": True }, # Dunk Low Valour Blue
    "DO7216-100": { "sizes": [], "include_restricted": True }, # Jordan 2 A Ma Maniere
    "DJ9754-652": { "sizes": [], "include_restricted": True }, # Jordan A Ma Maniere Shorts Bordeaux
    "DJ9754-010": { "sizes": [], "include_restricted": True }, # Jordan A Ma Maniere Shorts Black
    "555088-702": { "sizes": ["11"], "include_restricted": True }, # Jordan 1 Volt
    "DM0808-700": { "sizes": ["8", "8.5"], "include_restricted": True }, # Dunk High Pinapple
    "DM0807-400": { "sizes": [], "include_restricted": True }, # Dunk Low Blue Raspberry
    "CD4487-100": { "sizes": [], "include_restricted": True }, # Travis Jordan 1
    "CQ4277-001": { "sizes": [], "include_restricted": True }, # Travis Jordan 1 Low
    "DH3227-105": { "sizes": [], "include_restricted": True }, # Travis Jordan 1 Fragment
    "DM7866-140": { "sizes": [], "include_restricted": True }, # Travis Jordan 1 Low Fragment
    "CT5053-001": { "sizes": [], "include_restricted": True }, # Travis Dunk Low
    "CT2552-800": { "sizes": [], "include_restricted": True }, # Dunk Low StrangeLove
}


def should_notify(session: Session, all_changes: dict[str, list[int]]) -> list[Product]:
    """
    returns:
    a list of products that have become available in the most recent step.
    """
    skus = list(watchlist.keys())
    watched_products = queries.query_products_by_style_color(session, style_colors=skus)

    notify = []
    # for p, info in zip(watched_products, watchlist.values()):
    for p in watched_products:
        info = watchlist[p.info[-1].style_color]

        if p is None:
            continue

        # prev_available = queries.is_available(p, -2, sizes=info.get("sizes", []))
        # curr_available = queries.is_available(p, -1, sizes=info.get("sizes", []))
        # print(f"title: {p.info[-1].title} ({p.info[-1].style_color}): {prev_available}/{curr_available} --> {info.get('sizes')}")


        if p.id in all_changes["availability"] or all_changes["add"]:
            # product becomes available. 
            prev_available = queries.is_available(p, -2, sizes=info.get("sizes", []))
            curr_available = queries.is_available(p, -1, sizes=info.get("sizes", []))

            if not prev_available and curr_available:
                notify.append(p)

        if p.id in all_changes["launch"]:
            pass

    return notify
