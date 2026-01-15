# Jak korzystać z głosowania w projekcie crypto-project (wariant 1)?

## Instalacja bibliotek:
Biblioteki do zainstalowania: `cryptography`

Można skorzystać z pliku `requirements.txt` w katalogu głównym.

`pip install -r requirements.txt`

## Przeprowadzenie głosowania (lokalnie)
1. Należy przejść do folderu `/variant_1` lub `/variant_2`.
2. Należy uruchomić programy `registration_server.py` i `ballot_box_server.py`.
3. Następnie trzeba uruchomić dowolną ilość programów `voter.py` *(aktuanie obowiązuje ograniczenie 7, ale można je łatwo podnieść)*.
4. Każdy głosujący wpisuje swoje id *(3-9)*, **koniecznie** każdy inne. Jest to prymitywny zapełniacz systemu uwierzytelniania. 
5. Jeśli wszystko pójdzie poprawnie, wyborca powinien zostać połączony do serwera rejestracji i kartę do głosowania, która wyświetli się na ekranie konsoli głosującego.
6. Głosujący podaje id swojego kandydata (*w przykładzie 0 lub 1*) i potwierdza swój wybór.
7. Wypełniony głos jest automatycznie przesyłany do serwera zliczającego głosy.
8. Gdy wszyscy wyborcy oddadzą swoje głosy, należy uruchomić program `root.py` i wybrać opcję 3.
9. Serwer zliczający głosy publikuje wyniki głosowania.