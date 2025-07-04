#include <initializer_list>
#include <iostream>

int sum(std::initializer_list<int> vals) {
    int total = 0;
    for (int v : vals) total += v;
    return total;
}

int main() {
    std::cout << "Sum: " << sum({1, 2, 3}) << std::endl;
    return 0;
}
