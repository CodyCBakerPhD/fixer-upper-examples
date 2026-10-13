# existing API

def get_status() -> Checkpoint:
    ...

def rollback(checkpoint: Checkpoint) -> None:
    ...

def create_record(name) -> tuple[Record, bool]:
    ...

def link_record(record, other) -> bool:
    ...

def unlink_all(record) -> bool:
    ...

def get(name) -> Optional[Record]:
    ...

def decrement_waiting_time(record) -> bool:
    ...

def reset_waiting_time(record) -> bool:
    ...

# existing usages

def initialize_caller(name, partner):
    """Create a new caller based on their NAME and start them waiting for PARTNER."""
    checkpoint = get_status()
    client, failed1 = create_record(name)
    failed2 = link_record(client, get(partner))
    failed3 = decrement_waiting_time(client)

    if any([failed1, failed2, failed3]):
        rollback(checkpoint)
        return None
    else:
        return client

def swap_partner(client, partner):
    """Given a CLIENT record, move them to PARTNER's queue and reset their waiting time."""
    checkpoint = get_status()
    failed1 = unlink_all(client)
    failed2 = link_record(client, get(partner))
    failed3 = reset_waiting_time(client)

    if any([failed1, failed2, failed2]):
        rollback(checkpoint)

# does anyone see the bug above?


# any ideas for refactoring?
