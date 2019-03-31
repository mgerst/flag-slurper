RED_USER = {
    'username': 'reduser',
    'first_name': 'Red',
    'last_name': 'User',
    'is_superuser': False,
    'profile': {
        'is_red': True,
    }
}

RED_FLAGS = [
    {
        'id': 1,
        'team_number': 1,
        'name': 'WWW /etc',
        'type': 'red',
        'data': 'ABCDEFGHIJ',
    }
]

ADMIN_USER = {
    'username': 'adminuser',
    'first_name': 'Admin',
    'last_name': 'User',
    'is_superuser': True,
    'profile': {
        'is_red': False,
    }
}

ADMIN_FLAGS = [
    {
        'id': 1,
        'team_number': 1,
        'name': 'WWW /etc',
        'type': 'red',
        'data': 'ABCDE',
    },
    {
        'id': 2,
        'team_number': 1,
        'name': 'WWW /root',
        'type': 'blue',
        'data': 'FGHIJ',
    },
]

BLUE_USER = {
    'username': 'blueuser',
    'first_name': 'Blue',
    'last_name': 'User',
    'is_superuser': False,
    'profile': {
        'is_red': False,
        'is_blue': True,
    }
}
