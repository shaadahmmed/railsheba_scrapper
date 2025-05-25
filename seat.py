import requests
from os import environ
from train import search_train


def get_seat_layouts(seat_type, headers):
    trip_id = seat_type["trip_id"]
    trip_route_id = seat_type["trip_route_id"]
    seat_layout_url = f"https://railspaapi.shohoz.com/v1.0/web/bookings/seat-layout?trip_id={trip_id}&trip_route_id={trip_route_id}"

    seat_layout = []
    count = 0
    while seat_layout == []:
        count += 1
        print(f"Try {count}")
        res = requests.get(seat_layout_url, headers=headers).json()
        if res.get("error"):
            print(res["error"]["messages"])
            continue
        seat_layout = [
            room for room in res["data"]["seatLayout"] if room["seat_availability"]
        ]
    print("Seat Layout Found!")
    return seat_layout


def check_seat_availability(headers):
    seat_class = environ.get("SEAT_CLASS").upper().strip()
    classes = search_train(headers)

    count = 0
    while not classes:
        count += 1
        print(f"No trains found! Retrying {count}...")
        classes = search_train(headers)

    seat_type = classes.get(seat_class)
    if not seat_type:
        print("Check the SEAT_CLASS environment variable!")
        exit()

    trip_id = seat_type["trip_id"]
    trip_route_id = seat_type["trip_route_id"]
    boarding_point_id = seat_type["boarding_point_id"]
    return (
        trip_id,
        trip_route_id,
        boarding_point_id,
        get_seat_layouts(seat_type, headers),
    )


def get_max_size_room(seat_layout):
    if len(seat_layout) == 1:
        return seat_layout[0]["layout"]

    selected = seat_layout[0]
    max = 0
    for room in seat_layout:
        sum = 0
        for row in room["layout"]:
            sum += sum(1 for seat in row if seat["seat_availability"] == 1)
        if sum > max:
            max = sum
            selected = room
    return selected["layout"]
