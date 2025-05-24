from os import environ
import requests


def search_train(headers):
    from_station = environ.get("FROM_STATION")
    to_station = environ.get("TO_STATION")
    date_of_journey = environ.get("DATE")
    seat_class = environ.get("SEAT_CLASS")
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
    return train_search_dict


def find_desired_train(trains):
    trip_number = environ.get("TRAIN_NAME").strip().upper()

    for train in trains:
        if train["trip_number"].upper() == trip_number:
            trains.remove(trains)
            trains.insert(0, train)
            return train
    return None
