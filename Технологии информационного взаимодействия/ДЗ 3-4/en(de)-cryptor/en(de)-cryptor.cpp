#include <iostream>
#include <string>
#include <vector>
#include <cctype>
#include <limits>
#include <cstdlib>
#include <clocale>
#ifdef _WIN32
#define NOMINMAX
#include <windows.h>
#endif
void clearScreen() {
#ifdef _WIN32
    std::system("cls");
#else
    std::system("clear");
#endif
}
void waitEnter() {
    std::cout << "Нажмите Enter...";
    std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
}
void caesarMenu() {
    while (true) {
        std::cout << "=== Алгоритм Цезаря ===\n";
        std::cout << "1 - Шифрование\n";
        std::cout << "2 - Дешифрование\n";
        std::cout << "0 - Назад\n";
        std::cout << "> ";
        int mode = -1;
        std::cin >> mode;
        std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
        clearScreen();
        if (mode == 0) {
            return;
        }
        if (mode == 1 || mode == 2) {
            std::string text;
            std::cout << "Введите текст (латиница): ";
            std::getline(std::cin, text);
            std::cout << "Ключ (целое число): ";
            int key = 0;
            std::cin >> key;
            std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
            int shift = key % 26;
            if (shift < 0) {
                shift = shift + 26;
            }
            std::string result = text;
            int i = 0;
            while (i < text.size()) {
                char c = text[i];
                bool isUpper = false;
                bool isLower = false;
                if (std::isupper(static_cast<unsigned char>(c))) {
                    isUpper = true;
                }
                if (std::islower(static_cast<unsigned char>(c))) {
                    isLower = true;
                }
                if (isUpper || isLower) {
                    char base = 'a';
                    if (isUpper) {
                        base = 'A';
                    }
                    int offset = c - base;
                    int newOffset = offset;
                    if (mode == 1) {
                        newOffset = (offset + shift) % 26;
                    }
                    if (mode == 2) {
                        newOffset = (offset + 26 - shift) % 26;
                    }
                    result[i] = base + newOffset;
                }
                else {
                    result[i] = c;
                }
                i = i + 1;
            }
            clearScreen();
            if (mode == 1) {
                std::cout << "Режим: Шифрование (Caesar)\n";
            }
            if (mode == 2) {
                std::cout << "Режим: Дешифрование (Caesar)\n";
            }
            std::cout << "Ключ: " << key << "\n";
            std::cout << "Входной текст: " << text << "\n";
            std::cout << "Результат: " << result << "\n";
            waitEnter();
            clearScreen();
        }
        else {
            clearScreen();
        }
    }
}
void xorMenu() {
    while (true) {
        std::cout << "=== Алгоритм XOR ===\n";
        std::cout << "1 - Шифрование\n";
        std::cout << "2 - Дешифрование\n";
        std::cout << "0 - Назад\n";
        std::cout << "> ";
        int mode = -1;
        std::cin >> mode;
        std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
        clearScreen();
        if (mode == 0) {
            return;
        }
        if (mode == 1 || mode == 2) {
            std::string text;
            std::cout << "Введите текст (латиница): ";
            std::getline(std::cin, text);
            std::cout << "Ключ (один символ): ";
            char key = 0;
            std::cin >> key;
            std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
            std::string result = text;
            int i = 0;
            while (i < text.size()) {
                result[i] = text[i] ^ key;
                i = i + 1;
            }
            clearScreen();
            if (mode == 1) {
                std::cout << "Режим: Шифрование (XOR)\n";
            }
            if (mode == 2) {
                std::cout << "Режим: Дешифрование (XOR)\n";
            }
            std::cout << "Ключ: " << key << "\n";
            std::cout << "Входной текст: " << text << "\n";
            std::cout << "Результат: " << result << "\n";
            waitEnter();
            clearScreen();
        }
        else {
            clearScreen();
        }
    }
}
void multiAlphabetMenu() {
    while (true) {
        std::cout << "=== Многоалфавитная замена ===\n";
        std::cout << "1 - Шифрование\n";
        std::cout << "2 - Дешифрование\n";
        std::cout << "0 - Назад\n";
        std::cout << "> ";
        int mode = -1;
        std::cin >> mode;
        std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
        clearScreen();
        if (mode == 0) {
            return;
        }
        if (mode == 1 || mode == 2) {
            int shifts[4] = { 12, 5, 9, 21 };
            std::string text;
            std::cout << "Введите текст (латиница): ";
            std::getline(std::cin, text);
            std::string result = text;
            int i = 0;
            while (i < text.size()) {
                char c = text[i];
                bool isUpper = false;
                bool isLower = false;
                if (std::isupper(static_cast<unsigned char>(c))) {
                    isUpper = true;
                }
                if (std::islower(static_cast<unsigned char>(c))) {
                    isLower = true;
                }
                if (isUpper || isLower) {
                    char base = 'a';
                    if (isUpper) {
                        base = 'A';
                    }
                    int offset = c - base;
                    int shift = shifts[i % 4];
                    if (mode == 2) {
                        shift = 26 - shift;
                    }
                    int newOffset = (offset + shift) % 26;
                    result[i] = base + newOffset;
                }
                else {
                    result[i] = c;
                }
                i = i + 1;
            }
            clearScreen();
            if (mode == 1) {
                std::cout << "Режим: Шифрование (Многоалфавитная)\n";
            }
            if (mode == 2) {
                std::cout << "Режим: Дешифрование (Многоалфавитная)\n";
            }
            std::cout << "Ключ: фиксированный [12, 5, 9, 21]\n";
            std::cout << "Входной текст: " << text << "\n";
            std::cout << "Результат: " << result << "\n";
            waitEnter();
            clearScreen();
        }
        else {
            clearScreen();
        }
    }
}
void transpositionMenu() {
    while (true) {
        std::cout << "=== Перестановка ===\n";
        std::cout << "1 - Шифрование\n";
        std::cout << "2 - Дешифрование\n";
        std::cout << "0 - Назад\n";
        std::cout << "> ";
        int mode = -1;
        std::cin >> mode;
        std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
        clearScreen();
        if (mode == 0) {
            return;
        }
        if (mode == 1 || mode == 2) {
            int blockSize = 4;
            int perm[4] = { 3, 1, 2, 0 };
            int invPerm[4] = { 0, 0, 0, 0 };
            int i = 0;
            while (i < blockSize) {
                int pos = perm[i];
                invPerm[pos] = i;
                i = i + 1;
            }
            std::string text;
            std::cout << "Введите текст (латиница): ";
            std::getline(std::cin, text);
            std::string result = "";
            int len = text.size();
            int j = 0;
            while (j < len) {
                std::vector<char> block(blockSize, ' ');
                int k = 0;
                while (k < blockSize) {
                    int idx = j + k;
                    if (idx < len) {
                        block[k] = text[idx];
                    }
                    k = k + 1;
                }
                int m = 0;
                while (m < blockSize) {
                    if (mode == 1) {
                        int pos = perm[m];
                        result.push_back(block[pos]);
                    }
                    if (mode == 2) {
                        int pos = invPerm[m];
                        result.push_back(block[pos]);
                    }
                    m = m + 1;
                }
                j = j + blockSize;
            }
            clearScreen();
            if (mode == 1) {
                std::cout << "Режим: Шифрование (Перестановка)\n";
            }
            if (mode == 2) {
                std::cout << "Режим: Дешифрование (Перестановка)\n";
            }
            std::cout << "Ключ: фиксированный [3, 1, 2, 0]\n";
            std::cout << "Входной текст: " << text << "\n";
            std::cout << "Результат: " << result << "\n";
            waitEnter();
            clearScreen();
        }
        else {
            clearScreen();
        }
    }
}
void vigenereMenu() {
    while (true) {
        std::cout << "=== Виженер ===\n";
        std::cout << "1 - Шифрование\n";
        std::cout << "2 - Дешифрование\n";
        std::cout << "0 - Назад\n";
        std::cout << "> ";
        int mode = -1;
        std::cin >> mode;
        std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
        clearScreen();
        if (mode == 0) {
            return;
        }
        if (mode == 1 || mode == 2) {
            std::string text;
            std::cout << "Введите текст (латиница): ";
            std::getline(std::cin, text);
            std::string key;
            std::cout << "Ключевое слово (латиница): ";
            std::getline(std::cin, key);
            if (key.empty()) {
                std::cout << "Ключ не может быть пустым!\n";
                waitEnter();
                clearScreen();
                continue;
            }
            std::string result = text;
            int keyLen = key.size();
            int keyPos = 0;
            int i = 0;
            while (i < text.size()) {
                char c = text[i];
                bool isUpper = false;
                bool isLower = false;
                if (std::isupper(static_cast<unsigned char>(c))) {
                    isUpper = true;
                }
                if (std::islower(static_cast<unsigned char>(c))) {
                    isLower = true;
                }
                if (isUpper || isLower) {
                    char kch = key[keyPos % keyLen];
                    char base = 'A';
                    if (isLower) {
                        base = 'a';
                    }
                    int shift = std::toupper(static_cast<unsigned char>(kch)) - 'A';
                    int offset = c - base;
                    int newOffset = offset;
                    if (mode == 1) {
                        newOffset = (offset + shift) % 26;
                    }
                    if (mode == 2) {
                        newOffset = (offset + 26 - shift) % 26;
                    }
                    result[i] = base + newOffset;
                    keyPos = keyPos + 1;
                }
                else {
                    result[i] = c;
                }
                i = i + 1;
            }
            clearScreen();
            if (mode == 1) {
                std::cout << "Режим: Шифрование (Виженер)\n";
            }
            if (mode == 2) {
                std::cout << "Режим: Дешифрование (Виженер)\n";
            }
            std::cout << "Ключ: " << key << "\n";
            std::cout << "Входной текст: " << text << "\n";
            std::cout << "Результат: " << result << "\n";
            waitEnter();
            clearScreen();
        }
        else {+
            +
            clearScreen();
        }
    }
}
void buildPlayfairTable(const std::string& key, char table[5][5]) {
    bool used[26] = { false };
    std::string seq = "";
    int i = 0;
    while (i < key.size()) {
        char c = std::toupper(static_cast<unsigned char>(key[i]));
        if (c == 'J') {
            c = 'I';
        }
        if (c >= 'A' && c <= 'Z') {
            int pos = c - 'A';
            if (used[pos] == false) {
                used[pos] = true;
                seq.push_back(c);
            }
        }
        i = i + 1;
    }
    char c2 = 'A';
    while (c2 <= 'Z') {
        if (c2 != 'J') {
            int pos = c2 - 'A';
            if (used[pos] == false) {
                used[pos] = true;
                seq.push_back(c2);
            }
        }
        c2 = c2 + 1;
    }
    int k = 0;
    while (k < 25) {
        int row = k / 5;
        int col = k % 5;
        table[row][col] = seq[k];
        k = k + 1;
    }
}
void playfairMenu() {
    while (true) {
        std::cout << "=== Плейфер ===\n";
        std::cout << "1 - Шифрование\n";
        std::cout << "2 - Дешифрование\n";
        std::cout << "0 - Назад\n";
        std::cout << "> ";
        int mode = -1;
        std::cin >> mode;
        std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
        clearScreen();
        if (mode == 0) {
            return;
        }
        if (mode == 1 || mode == 2) {
            std::string text;
            std::cout << "Введите текст (латиница): ";
            std::getline(std::cin, text);
            std::string key;
            std::cout << "Ключевое слово (латиница): ";
            std::getline(std::cin, key);
            if (key.empty()) {
                std::cout << "Ключ не может быть пустым!\n";
                waitEnter();
                clearScreen();
                continue;
            }
            char table[5][5];
            std::string pts = "";
            int i = 0;
            buildPlayfairTable(key, table);
            while (i < text.size()) {
                char c = std::toupper(static_cast<unsigned char>(text[i]));
                if (std::isalpha(static_cast<unsigned char>(c)) && (c >= 'A' && c <= 'Z')) {
                    if (c == 'J') {
                        pts.push_back('I');
                    }
                    else {
                        pts.push_back(c);
                    }
                }
                i = i + 1;
            }
            std::string result = "";
            int length = pts.size();
            int j = 0;
            while (j < length) {
                char a = pts[j];
                char b = a;
                if (j + 1 < length) {
                    b = pts[j + 1];
                }
                if (a == b) {
                    b = 'X';
                }
                int ra = 0;
                int ca = 0;
                int rb = 0;
                int cb = 0;
                int r = 0;
                while (r < 5) {
                    int c = 0;
                    while (c < 5) {
                        if (table[r][c] == a) {
                            ra = r;
                            ca = c;
                        }
                        if (table[r][c] == b) {
                            rb = r;
                            cb = c;
                        }
                        c = c + 1;
                    }
                    r = r + 1;
                }
                if (mode == 1) {
                    if (ra == rb) {
                        result.push_back(table[ra][(ca + 1) % 5]);
                        result.push_back(table[rb][(cb + 1) % 5]);
                    }
                    else if (ca == cb) {
                        result.push_back(table[(ra + 1) % 5][ca]);
                        result.push_back(table[(rb + 1) % 5][cb]);
                    }
                    else {
                        result.push_back(table[ra][cb]);
                        result.push_back(table[rb][ca]);
                    }
                }
                if (mode == 2) {
                    if (ra == rb) {
                        result.push_back(table[ra][(ca + 4) % 5]);
                        result.push_back(table[rb][(cb + 4) % 5]);
                    }
                    else if (ca == cb) {
                        result.push_back(table[(ra + 4) % 5][ca]);
                        result.push_back(table[(rb + 4) % 5][cb]);
                    }
                    else {
                        result.push_back(table[ra][cb]);
                        result.push_back(table[rb][ca]);
                    }
                }
                if (a == b) {
                    j = j + 1;
                }
                else {
                    j = j + 2;
                }
            }
            clearScreen();
            if (mode == 1) {
                std::cout << "Режим: Шифрование (Плейфер)\n";
            }
            if (mode == 2) {
                std::cout << "Режим: Дешифрование (Плейфер)\n";
            }
            std::cout << "Ключ: " << key << "\n";
            std::cout << "Входной текст: " << text << "\n";
            std::cout << "Результат: " << result << "\n";
            waitEnter();
            clearScreen();
        }
        else {
            clearScreen();
        }
    }
}
int main() {
    std::setlocale(LC_ALL, "");
#ifdef _WIN32
    SetConsoleCP(1251);
    SetConsoleOutputCP(1251);
#endif
    while (true) {
        std::cout << "Выберите алгоритм:\n";
        std::cout << "1 - Цезарь\n";
        std::cout << "2 - XOR\n";
        std::cout << "3 - Многоалфавитная замена\n";
        std::cout << "4 - Перестановка\n";
        std::cout << "5 - Виженер\n";
        std::cout << "6 - Плейфер\n";
        std::cout << "0 - Выход\n";
        std::cout << "> ";
        int alg = -1;
        std::cin >> alg;
        std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
        clearScreen();
        if (alg == 0) {
            break;
        }
        else if (alg == 1) {
            caesarMenu();
        }
        else if (alg == 2) {
            xorMenu();
        }
        else if (alg == 3) {
            multiAlphabetMenu();
        }
        else if (alg == 4) {
            transpositionMenu();
        }
        else if (alg == 5) {
            vigenereMenu();
        }
        else if (alg == 6) {
            playfairMenu();
        }
        else 
        {
            clearScreen();
        }
    }
    return 0;
}
