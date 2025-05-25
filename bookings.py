import threading
from os import environ
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

from seat import get_max_size_room

number_of_seats = int(environ.get("NUMBER_OF_PASSENGERS"))
successful_bookings = 0
thread_lock = threading.Lock()


def reserve_seat(seat, trip_route_id, headers):
    global successful_bookings

    with thread_lock:
        if successful_bookings >= number_of_seats:
            print("Maximum number of seats booked!")
            return False

    seat_book_url = "https://railspaapi.shohoz.com/v1.0/web/bookings/reserve-seat"
    res = requests.patch(
        seat_book_url,
        json={
            "ticket_id": seat["ticket_id"],
            "route_id": trip_route_id,
        },
        headers=headers,
    )
    res_dict = res.json()
    if res_dict.get("error"):
        print(res_dict["error"]["messages"])
        return False
    with thread_lock:
        if successful_bookings < number_of_seats:
            successful_bookings += 1
            print(
                f"{seat['seat_number']} booked successfully! Total booked: {successful_bookings}"
            )
            return seat["ticket_id"]


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


def single_seat_booking(layout, trip_route_id, headers):
    global successful_bookings
    successful_bookings = 0
    room_layout = get_max_size_room(layout)
    window_seat = eval(environ.get("WINDOW_SEAT"))
    booked_tickets = []

    seats = []

    for row in room_layout:
        if window_seat:
            if row[0]["seat_availability"] == 1:
                seats.append(row[0])
            if row[-1]["seat_availability"] == 1:
                seats.append(row[-1])
            continue
        for seat in row:
            if seat["seat_availability"] == 1:
                seats.append(seat)

    with ThreadPoolExecutor(max_workers=10) as extractor:
        futures = []
        for seat in seats:
            print(
                f"Trying to book {'window seat' if window_seat else ''} {seat['seat_number']} {seat['ticket_id']}"
            )

            future = extractor.submit(reserve_seat, seat, trip_route_id, headers)

            futures.append(future)

        for future in as_completed(futures):
            result = future.result()
            if result:
                with thread_lock:
                    booked_tickets.append(result)
            if successful_bookings >= number_of_seats:
                break

    return booked_tickets


def double_seat_booking(layout, headers):
    pass


def three_seat_booking(layout, headers):
    pass


def four_seat_booking(layout, headers):
    pass


def book_booking(layout, headers):
    pass
