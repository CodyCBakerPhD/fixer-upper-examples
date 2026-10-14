# folks will likely suggest pulling out the duplicated check/rollback, but I wonder if anyone
# will suggest my preferred solution of a context manager

# ------------------------------------------------------------

class Transaction:
    def __init__(self):
        self.failed = false
        self.checkpoint = get_status()

    def commit(self):
        if self.failed:
            rollback(self.checkpoint)
        return not self.failed

    def create_record(self, name):
        result, failed = create_record(name)
        self.failed |= failed
        return result

    def link_record(self, record, other):
        self.failed |= link_record(record, other)

    def unlink_all(self, record):
        self.failed |= unlink_all(record)

    def decrement_waiting_time(self, record):
        self.failed |= decrement_waiting_time(record)

    def reset_waiting_time(self, record):
        self.failed |= reset_waiting_time(record)

    # these two functions make this class a "Context Manager"
    def __enter__(self):
        self.failed = false
        self.checkpoint = get_status()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exec_val is not None:
            self.failed = true
        self.commit()
        return True

def initialize_caller(name, partner):
    with Transaction() as t:
        client = t.create_record(name)
        t.link_record(client, get(partner))
        t.decrement_waiting_time(client)
    return get(name)

def swap_partner(client, partner):
    """Given a CLIENT record, move them to PARTNER's queue and reset their waiting time."""
    with Transaction() as t:
        t.unlink_all(client)
        t.link_record(record, get(partner))
        t.reset_waiting_time(record)


# note that once this is used everywhere, it creates a cleaner location for more changes

# e.g. If we wanted to ignore all functions after the first failed, we could just
# `if self.failed: return` at the start

# We could also migrate to a true transaction model rather than a modeled one with rollbacks,
# etc, etc
