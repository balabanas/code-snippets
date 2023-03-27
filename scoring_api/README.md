# On Windows:
* Run Git Bash
* $ curl -X POST -H "Content-Type: application/json" -d '{"account": "horns&hoofs", "login": "hf", "method": "online_score", "token": "token_val", "arguments": {"phone":78888888888, "email": "test@mail.ent"}}' http://localhost:8080/method

curl -X POST -H "Content-Type: application/json" -d '{"account": "horns&hoofs", "login": "admin", "method": "clients_interests", "token": "token_val", "arguments": {"client_ids": ["1", "2", "10", "25"], "date": "22.03.1996"}}' http://localhost:8080/method

"arguments": {"phone":78888888888, "email": "test@mail.ent"}