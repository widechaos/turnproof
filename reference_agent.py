"""Small offline booking voice agent used as a controlled test target.

Bookings are test records only. Fault modes intentionally change its behavior.
"""
def respond(text, call_tool, fault='none'):
    normalized = text.lower()
    if 'cancel' in normalized or 'do not make any booking' in normalized:
        if fault == 'ignore_cancel':
            call_tool('save_booking', {'date': 'Thursday'})
            return 'I saved your booking for Thursday.'
        return 'Cancelled. No booking was made.'
    if 'friday' in normalized:
        date = 'Thursday' if fault == 'wrong_date' else 'Friday'
        call_tool('save_booking', {'date': date})
        if fault == 'duplicate_save':
            call_tool('save_booking', {'date': date})
        return 'Your booking is saved for ' + date + '.'
    return 'Please specify a date or cancel the booking.'
