-- This file can be used to set up a database for manual testing.

INSERT INTO team (id, name, number) VALUES
    (1, 'CDC Team 1', 1),
    (2, 'CDC Team 2', 2),
    (3, 'CDC Team 3', 3),
    (4, 'CDC Team 4', 4);


INSERT INTO service (remote_id, service_id, service_name, service_url, service_port, team_id, is_rand)
VALUES
    (1, 1, 'WWW SSH', '192.168.3.11', 22, 1, 0),
    (2, 2, 'WWW SSH', '192.168.3.12', 22, 2, 0),
    (3, 3, 'WWW SSH', '192.168.3.13', 22, 3, 0),
    (4, 4, 'WWW SSH', '192.168.3.14', 22, 4, 0);
