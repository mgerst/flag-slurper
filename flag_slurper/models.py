class User(object):
    def __init__(self, resp):
        self.raw = resp

        self.first_name = resp['first_name']
        self.last_name = resp['last_name']
        self.username = resp['username']

        self.is_red = resp['profile']['is_red']
        self.is_admin = resp['is_superuser']

    @property
    def is_red_or_admin(self):
        return self.is_red or self.is_admin

    @property
    def full_name(self):
        return '{} {}'.format(self.first_name, self.last_name)