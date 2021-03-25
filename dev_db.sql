-- This file can be used to set up a database for manual testing.

INSERT INTO team (id, name, number, domain) VALUES
    (1, 'CDC Team 1', 1, 'team1.isucdc.com'),
    (2, 'CDC Team 2', 2, 'team2.isucdc.com'),
    (3, 'CDC Team 3', 3, 'team3.isucdc.com'),
    (4, 'CDC Team 4', 4, 'team4.isucdc.com');


INSERT INTO service (remote_id, service_id, service_name, service_url, service_port, team_id, is_rand)
VALUES
    (1, 1, 'WWW SSH', '192.168.3.11', 22, 1, false),
    (2, 2, 'WWW SSH', '192.168.3.12', 22, 2, false),
    (3, 3, 'WWW SSH', '192.168.3.13', 22, 3, false),
    (4, 4, 'WWW SSH', '192.168.3.14', 22, 4, false),
    (5, 5, 'DNS', '192.168.3.11', 53, 1, false), -- DNS is handled automatically
    (6, 6, 'WWW SMTP', '192.168.3.11', 25, 1, false),
    (7, 7, 'WWW DB', '192.168.3.12', 3306, 2, false);
