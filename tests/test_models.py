import pytest

from flag_slurper.models import User


@pytest.fixture
def user():
    return User({
        'first_name': 'Test',
        'last_name': 'Blue',
        'username': 'blue',
        'is_superuser': False,
        'profile': {'is_red': False},
    })


@pytest.fixture
def user_admin():
    return User({
        'first_name': 'Test',
        'last_name': 'Admin',
        'username': 'admin',
        'is_superuser': True,
        'profile': {'is_red': False},
    })


@pytest.fixture
def user_red():
    return User({
        'first_name': 'Test',
        'last_name': 'Red',
        'username': 'Red',
        'is_superuser': False,
        'profile': {'is_red': True},
    })


def test_full_name(user):
    assert user.full_name == "Test Blue"


def test_user_is_red(user_red):
    assert user_red.is_red_or_admin


def test_user_is_admin(user_admin):
    assert user_admin.is_red_or_admin


def test_user_is_blue(user):
    assert not user.is_red_or_admin
