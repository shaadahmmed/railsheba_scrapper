from encodings.punycode import T
import requests
from os import environ

from train import find_desired_train, search_train


def reserve_seat(ticket_id, trip_route_id, headers):
    print(f"Trying to book {ticket_id}")
    seat_book_url = "https://railspaapi.shohoz.com/v1.0/web/bookings/reserve-seat"
    res = requests.patch(
        seat_book_url,
        json={
            "ticket_id": ticket_id,
            "route_id": trip_route_id,
        },
        headers=headers,
    )
    res_dict = res.json()
    if res_dict.get("error"):
        print(res_dict["error"]["messages"])
        return False
    return True


def release_seat(ticket_id, trip_route_id, headers):
    print("Trying to relase seat", ticket_id)
    seat_release_url = "https://railspaapi.shohoz.com/v1.0/web/bookings/release-seat"
    res = requests.patch(
        seat_release_url,
        json={"ticket_id": ticket_id, "route_id": trip_route_id},
        headers=headers,
    )
    res_dict = res.json()
    if res_dict.get("error"):
        print(res_dict["error"]["messages"])
        return False
    print("Seat Released!")
    return True


def seat_class_available(seat_types):
    seat_class = environ.get("SEAT_CLASS").upper()
    number_of_seats = int(environ.get("NUMBER_OF_PASSENGERS"))

    for seat_type in seat_types:
        if seat_type["type"] == seat_class:
            seat_counts = (
                seat_type["seat_counts"]["online"] + seat_type["seat_counts"]["offline"]
            )
            if seat_counts < number_of_seats:
                return None
            return seat_type

    return None


def check_seat_availability(headers):
    trip_number = environ.get("TRAIN_NAME").upper()
    seat_class = environ.get("SEAT_CLASS").upper()
    retry_another = eval(environ.get("RETRY_ANOTHER"))

    count = 0
    found = False
    while not found:
        count += 1
        train_search_dict = search_train(headers)
        if train_search_dict["data"]["trains"] == []:
            print(f"No trains found! Retrying {count}...")
            continue

        print("All Trains Found!")
        print("Finding Desired Train...")

        train = find_desired_train(train_search_dict["data"]["trains"])

        if train:
            print(f"{train['trip_number']} is available!")
        elif retry_another:
            train = train_search_dict["data"]["trains"][0]
            print(f"{trip_number} is not available!")
            print(f"Selected Train {train['trip_number']} instead!")
        else:
            print(f"{trip_number} is not available!")
            print("Exiting...")
            exit()

        seat_type = seat_class_available(train["seat_types"])
        if not seat_type:
            print(f"No {seat_class} seats available for {train['trip_number']}!")
            print(f"Retrying...{count}")
            continue

        return (
            seat_type["trip_id"],
            seat_type["trip_route_id"],
            train["boarding_points"][0]["trip_point_id"],
        )


def get_seat_layout(trip_id, trip_route_id, headers):
    train_seat_url = f"https://railspaapi.shohoz.com/v1.0/web/bookings/seat-layout?trip_id={trip_id}&trip_route_id={trip_route_id}"
    train_seat_response = requests.get(train_seat_url, headers=headers)
    train_seat_dict = train_seat_response.json()
    if train_seat_dict.get("error"):
        print(train_seat_dict["error"]["messages"])
        return None
    else:
        seat_layout = train_seat_dict["data"]["seatLayout"]
        return seat_layout


def sort_rooms(seat_layout):
    available_rooms = [room for room in seat_layout if room["seat_availability"]]
    if not available_rooms:
        print("No rooms available!")
        return None

    if len(available_rooms) == 1:
        print("Only one room available!")
        return available_rooms

    sorted_rooms = sorted(
        available_rooms,
        key=lambda room: sum(
            1 for row in room["layout"] for seat in row if seat["seat_availability"]
        ),
        reverse=True,
    )
    return sorted_rooms
