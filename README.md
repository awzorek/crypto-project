# Projekt *e-voting*

## Wstęp
Celem projektu była analiza, implementacja oraz porównanie dwóch algorytmów głosowania internetowego (*e-voting*), opartych na kilku mechanizmach kryptograficznych. Projekt koncentrował się na ocenie bezpieczeństwa, anonimowości, integralności głosu oraz odporności na manipulacje w obu podejściach.

W ramach projektu zaimplementowano dwa warianty systemu:
- **Wariant 1 (jednoetapowe głosowanie)**, w którym rejestracja i oddanie głosu odbywają się w jednym procesie;
- **Wariant 2 (dwuetapowe głosowanie)**, rozdzielające fazę rejestracji i fazę głosowania oraz wprowadzające dodatkowy podmiot.

Całe wprowadzenie teoretyczne opisane jest w plikach `notes.pdf` i `Electronic Voting.pdf` oraz w raporcie projektu.

## Jak korzystać?

### Wymagania
- Git
- Python 3
- pip

### Instalacja
```
$ git clone https://github.com/awzorek/crypto-project.git
$ cd crypto-project
$ pip install -r requirements.txt
```

### Przeprowadzenie głosowania (lokalnie)
1. Należy przejść do folderu `/variant_1` lub `/variant_2`.
2. Należy uruchomić programy `registration_server.py` i `ballot_box_server.py`.
3. Następnie trzeba uruchomić dowolną ilość programów `voter.py` *(aktuanie obowiązuje ograniczenie 7, ale można je łatwo podnieść)*.
4. Każdy głosujący wpisuje swoje id `(3-9)`, **koniecznie** każdy inne. Jest to prymitywny zapełniacz systemu uwierzytelniania. 
5. Jeśli wszystko pójdzie poprawnie, wyborca powinien zostać połączony do serwera rejestracji i kartę do głosowania, która wyświetli się na ekranie konsoli głosującego.
6. Głosujący podaje id swojego kandydata (w przykładzie `0` lub `1`) i potwierdza swój wybór.
7. Wypełniony głos jest automatycznie przesyłany do serwera zliczającego głosy.
8. Gdy wszyscy wyborcy oddadzą swoje głosy, należy uruchomić program `root.py` i wybrać opcję `3`.
9. Serwer zliczający głosy publikuje wyniki głosowania.