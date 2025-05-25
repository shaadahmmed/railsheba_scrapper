from os import environ
import requests


def search_train(headers):
    from_station = environ.get("FROM_STATION").strip().capitalize()
    to_station = environ.get("TO_STATION").strip().capitalize()
    date_of_journey = environ.get("DATE").strip()
    seat_class = environ.get("SEAT_CLASS").upper().strip()
    train_search_url = f"https://railspaapi.shohoz.com/v1.0/web/bookings/search-trips-v2?from_city={from_station}&to_city={to_station}&date_of_journey={date_of_journey}&seat_class={seat_class}"

    train_search_dict = None
    while True:
        print("Searching for the trains...")
        train_search_response = requests.get(train_search_url, headers=headers)
        train_search_dict = train_search_response.json()
        if train_search_dict["data"]["trains"]:
            break
        else:
            print("No trains found! Retrying...")
    print("Trains Found!")
    return find_desired_train(train_search_dict["data"]["trains"])


def find_desired_train(trains):
    types = {}
    trip_number = environ.get("TRAIN_NAME").strip().upper()
    print(f"Searching for {trip_number}...")
    for train in trains:
        if trip_number in train["trip_number"].upper():
            print(f"Found {train['trip_number']}!")
            boarding_point_id = train["boarding_points"][0]["trip_point_id"]
            seat_types = train["seat_types"]

            for seat_type in seat_types:
                types[seat_type["type"]] = {
                    "key": seat_type["key"],
                    "trip_id": seat_type["trip_id"],
                    "trip_route_id": seat_type["trip_route_id"],
                    "boarding_point_id": boarding_point_id,
                    "total_seats": seat_type["seat_counts"]["online"]
                    + seat_type["seat_counts"]["offline"],
                }
            return types
    return None
